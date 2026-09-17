/**
 * Lampa Cordova Bridge (完全模拟 AndroidJS 原生状态机)
 * 1:1 模拟官方 top.rootu.lampa.AndroidJS 原生协议
 */
(function () {
    'use strict';

    // =========================================================================
    // 拦截核心解码库：强制任何试图请求远端 vender/ 的脚本重定向为本地 ./vender/
    // =========================================================================
    // var originalCreateElement = document.createElement;
    // document.createElement = function (tagName) {
    //     var el = originalCreateElement.apply(this, arguments);
    //     if (tagName && typeof tagName === 'string' && tagName.toLowerCase() === 'script') {
    //         var originalSetAttribute = el.setAttribute;
    //         el.setAttribute = function (name, value) {
    //             if (name === 'src' && typeof value === 'string' && value.indexOf('vender/') !== -1) {
    //                 value = './vender/' + value.split('vender/')[1];
    //             }
    //             return originalSetAttribute.call(this, name, value);
    //         };
    //         Object.defineProperty(el, 'src', {
    //             set: function (value) {
    //                 if (typeof value === 'string' && value.indexOf('vender/') !== -1) {
    //                     value = './vender/' + value.split('vender/')[1];
    //                 }
    //                 el.setAttribute('src', value);
    //             },
    //             get: function () {
    //                 return el.getAttribute('src');
    //             },
    //             configurable: true
    //         });
    //     }
    //     return el;
    // };

    // 0. 证书信任
    if (!window._cordova_certs_accepted && window.cordovaHTTP) {
        try {
            cordovaHTTP.acceptAllCerts(true, function () {}, function () {});
            window._cordova_certs_accepted = true;
        } catch (e) {}
    }

    // 存储请求响应的字典 (对应 Kotlin 里的 reqResponse: MutableMap<String, String>)
    var reqResponse = {};

    // =========================================================================
    // 核心契约模拟：AndroidJS.httpReq + AndroidJS.getResp
    // =========================================================================
    var nativeHttpEngine = {
        /**
         * 对应 Kotlin: fun httpReq(str: String, returnI: Int)
         */
        httpReq: function (str, returnI) {
            var params;
            try {
                params = typeof str === 'string' ? JSON.parse(str) : str;
            } catch (e) {
                console.error('[Bridge] 解析 httpReq JSON 失败:', str);
                return;
            }

            var url = params.url;
            var data = params.post_data;
            var headers = params.headers || {};
            var returnHeaders = params.returnHeaders || false;
            var dataType = params.dataType || 'json';
            var method = (params.type || (data ? 'POST' : 'GET')).toUpperCase();

            // 成功后通知 Lampa 并存入数据池
            function finalizeSuccess(bodyStr, allHeaders) {
                if (returnHeaders) {
                    reqResponse[returnI.toString()] = JSON.stringify({
                        body: bodyStr,
                        headers: allHeaders || {}
                    });
                } else {
                    reqResponse[returnI.toString()] = typeof bodyStr === 'string' ? bodyStr : JSON.stringify(bodyStr);
                }

                // 核心：像 Kotlin 那样反向调用 Lampa 的回调函数！
                if (window.Lampa && window.Lampa.Android && window.Lampa.Android.httpCall) {
                    window.Lampa.Android.httpCall(returnI, 'complite');
                }
            }

            // 失败通知
            function finalizeError(status, message) {
                reqResponse[returnI.toString()] = JSON.stringify({
                    status: status || 0,
                    message: message || "request error"
                });
                if (window.Lampa && window.Lampa.Android && window.Lampa.Android.httpCall) {
                    window.Lampa.Android.httpCall(returnI, 'error');
                }
            }

            // 优先走 cordovaHTTP
            if (window.cordovaHTTP) {
                if (method === 'GET') {
                    cordovaHTTP.get(url, {}, headers, function (res) {
                        finalizeSuccess(res.data, res.headers);
                    }, function (err) {
                        finalizeError(err.status, err.error);
                    });
                    return;
                } else if (method === 'POST') {
                    var postBody = {};
                    if (data) {
                        if (typeof data === 'string') {
                            try { postBody = JSON.parse(data); }
                            catch (e) {
                                data.split('&').forEach(function (pair) {
                                    var parts = pair.split('=');
                                    if (parts[0]) postBody[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1] || '');
                                });
                            }
                        } else if (typeof data === 'object') {
                            postBody = data;
                        }
                    }
                    cordovaHTTP.post(url, postBody, headers, function (res) {
                        finalizeSuccess(res.data, res.headers);
                    }, function (err) {
                        finalizeError(err.status, err.error);
                    });
                    return;
                }
            }

            // 兜底走 cordovaFetch / fetch
            var fetchRunner = window.cordovaFetch || window.fetch;
            if (fetchRunner) {
                var fetchOptions = { method: method, headers: headers };
                if (data && method !== 'GET') {
                    fetchOptions.body = typeof data === 'object' ? JSON.stringify(data) : data;
                }

                fetchRunner(url, fetchOptions)
                    .then(function (res) {
                        return res.text().then(function (txt) {
                            if (res.status >= 200 && res.status < 400) {
                                finalizeSuccess(txt, {});
                            } else {
                                finalizeError(res.status, res.statusText);
                            }
                        });
                    })
                    .catch(function (err) {
                        finalizeError(0, err.message);
                    });
                return;
            }

            finalizeError(0, 'No Native HTTP Available');
        },

        /**
         * 对应 Kotlin: fun getResp(str: String): String?
         * Lampa 收到 httpCall 通知后，立刻调这个方法把数据取走！
         */
        getResp: function (str) {
            var string = "";
            var key = str.toString();
            if (reqResponse.hasOwnProperty(key)) {
                string = reqResponse[key];
                delete reqResponse[key]; // 取完即焚，和 Kotlin 完全一致！
            }
            return string;
        }
    };

    // =========================================================================
    // 核心播放器逻辑提取（供 AndroidJS 和 Android 共用）
    // =========================================================================
    var nativePlayerEngine = {
        openPlayer: function (url, data) {
            // 容错：有些版本的 Lampa 传的是 JSON 字符串，有些传的是对象
            var playData = {};
            if (typeof data === 'string') {
                try { playData = JSON.parse(data); } catch (e) {}
            } else if (typeof data === 'object' && data !== null) {
                playData = data;
            }

            // 计算起始播放位置（毫秒）
            var pos = parseInt((playData.timeline ? playData.timeline.time || -1 : -1) * 1000);
            
            var intentExtra = {
                title: playData.title || playData.path || '',
                position: pos,
                return_result: true,
                forcedirect: true,
                forceresume: true
            };

            var intentConfig = {
                action: window.plugins.intentShim.ACTION_VIEW,
                url: playData.url || url,
                position: pos,
                type: "video/*",
                extras: intentExtra
            };

            // 获取用户在设置中指定的默认播放器包名
            var chosenPlayer = localStorage.getItem('lampa_default_player') || '';
            if (chosenPlayer) {
                intentConfig.package = chosenPlayer;
            }

            if (!window.plugins || !window.plugins.intentShim) {
                console.warn('[Bridge] 未找到 intentShim 插件，尝试降级打开');
                if (window.cordova && cordova.InAppBrowser) cordova.InAppBrowser.open(intentConfig.url, '_system');
                return;
            }

            // 唤起外部播放器并监听播放进度
            window.plugins.intentShim.startActivityForResult(intentConfig, function (intent) {
                var extras = intent.extras || {};
                var time = (extras.position || extras.extra_position) / 1000;
                var duration = (extras.duration || extras.extra_duration) / 1000;
                var percent = duration > 0 ? parseInt(time * 100 / duration) : 100;

                // 播放完毕/退出后，回写进度到 Lampa 历史记录
                if (time && playData.timeline) {
                    playData.timeline.time = time;
                    playData.timeline.duration = duration;
                    playData.timeline.percent = percent;
                    if (window.Lampa && Lampa.Timeline) {
                        Lampa.Timeline.update(playData.timeline);
                    }
                }
            }, function (err) {
                // 如果指定了默认播放器但启动失败（比如被用户卸载了），清空默认包名并重新弹框选择
                if (intentConfig.package) {
                    console.warn('[Bridge] 预设播放器启动失败，降级为系统应用选择器', err);
                    delete intentConfig.package;
                    window.plugins.intentShim.startActivityForResult(intentConfig, function () {}, function () {});
                } else {
                    console.error('[Bridge] 启动播放器失败:', err);
                }
            });
        }
    };

    // =========================================================================
    // 挂载 window.Android 与 window.AndroidJS 接口
    // =========================================================================
    window.AndroidJS = {
        appVersion: function () { return '3.3.3-28'; }, // 现在可以放心地用 28 了！
        exit: function () {
            if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
        },
        httpReq: nativeHttpEngine.httpReq,
        getResp: nativeHttpEngine.getResp,

        clearDefaultPlayer: function () {
            if (window.selectDefaultPlayerMenu) window.selectDefaultPlayerMenu();
            else localStorage.removeItem('lampa_default_player');
        },
        openYoutube: function (str) {
            if (!str) return;

            // 1. 兼容处理：如果传进来的是完整链接则直接用；如果是 ID，则拼接标准 YouTube 播放地址
            var fullUrl = (typeof str === 'string' && (str.indexOf('http://') === 0 || str.indexOf('https://') === 0))
                ? str
                : 'https://www.youtube.com/watch?v=' + str;

            // 获取当前语言环境，与 voiceStart 保持一致风格
            var curL = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'en';

            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity(
                    {
                        action: window.plugins.intentShim.ACTION_VIEW,
                        url: fullUrl
                    },
                    function () {
                        console.log('[Bridge] YouTube 打开成功');
                    },
                    function (err) {
                        console.error('[Bridge] 未找到 YouTube 对应应用:', err);
                        
                        // 1:1 还原官方 Kotlin: App.toast(R.string.no_youtube_activity_found, true)
                        if (window.Lampa && Lampa.Noty) {
                            var tip = (curL === 'zh') ? '未找到可用的 YouTube 播放器' : 'No YouTube activity found';
                            Lampa.Noty.show(tip);
                        }

                        // 电视端兜底方案：如果装了系统浏览器，尝试通过浏览器唤起
                        if (window.cordova && cordova.InAppBrowser) {
                            cordova.InAppBrowser.open(fullUrl, '_system');
                        }
                    }
                );
            } else {
                // 插件不存在时的降级兜底
                if (window.cordova && cordova.InAppBrowser) {
                    cordova.InAppBrowser.open(fullUrl, '_system');
                }
            }
        },
        openPlayer: nativePlayerEngine.openPlayer,
        openTorrentLink: function (urlOrMagnet, jsonString) {
            var jsonData = {};
            try { jsonData = JSON.parse(jsonString || '{}'); } catch (e) {}

            var intentExtra = {
                title: jsonData.title || '',
                poster: jsonData.poster || '',
                action: "play",
                data: { lampa: true }
            };

            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity({
                    action: window.plugins.intentShim.ACTION_VIEW,
                    url: urlOrMagnet,
                    extras: intentExtra
                }, function () {}, function () {});
            }
        },
        voiceStart: function () {
            if (!window.plugins || !window.plugins.intentShim) return;
            var curL = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'en';
            var voiceExtras = { "android.speech.extra.LANGUAGE_MODEL": "free_form", "android.speech.extra.MAX_RESULTS": 1 };
            if (curL === 'zh') voiceExtras["android.speech.extra.PROMPT"] = "请说出影片名称...";

            window.plugins.intentShim.startActivityForResult({
                action: "android.speech.action.RECOGNIZE_SPEECH",
                extras: voiceExtras
            }, function (result) {
                var extras = result.extras || {};
                var matches = extras['android.speech.extra.RESULTS'] || extras.results;
                if (matches && window.voiceResult) window.voiceResult(Array.isArray(matches) ? matches[0] : matches);
            }, function () {
                if (window.Lampa && Lampa.Noty) Lampa.Noty.show(curL === 'zh' ? '未检测到可用语音服务' : 'Voice service not available');
            });
        },
        updateChannel: function (where) {},
        saveBookmarks: function (json) {}
    };

    // 兼容可能存在的直接 Android.httpReq 调用
    window.Android = {
        exit: window.AndroidJS.exit,
        openPlayer: nativePlayerEngine.openPlayer
    };

    // 默认配置
    try {
        if (!localStorage.getItem('lampa_cordova_initiale')) {
            localStorage.setItem('lampa_cordova_initiale', 'true');
            localStorage.setItem('screensaver', 'false');
            localStorage.setItem('device_name', 'Lampa Cordova');
            localStorage.setItem('keyboard_type', 'integrate');
        }
    } catch (e) {}

    // 原生全屏
    document.addEventListener('deviceready', function () {
        if (window.StatusBar) window.StatusBar.hide();
    }, false);
})();
