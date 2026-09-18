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
    // 1:1 模拟 MainActivity.runPlayer + configurePlayerIntent
    // =========================================================================
    var nativePlayerEngine = {
        openPlayer: function (link, data) {
            // 1. 参数归一化：支持外部传字符串或对象
            var playData = {};
            if (typeof data === 'string') {
                try { playData = JSON.parse(data || '{}'); } catch (e) {}
            } else if (typeof data === 'object' && data !== null) {
                playData = data;
            }

            // 对应 Kotlin: 优先使用 playData.url，没有则回退为入参 link
            var videoUrl = playData.url || link;
            if (!videoUrl) {
                console.error('[Bridge] openPlayer 缺少视频地址');
                return;
            }

            // 2. 提取基础播放信息
            var title = playData.title || playData.path || (playData.iptv ? "LAMPA TV" : "LAMPA video");
            var timeline = playData.timeline || {};
            var posMillis = parseInt((timeline.time || -1) * 1000);

            // 3. 构建 Extras（集齐 MX Player、VLC、ViMu 专属起播参数）
            var intentExtra = {
                title: title,
                forcename: title,
                return_result: true,
                sticky: false,
                from_start: false,
                forcedirect: true,
                forceresume: true
            };

            if (posMillis > 0) {
                intentExtra.position = posMillis;       // 通用 / MX Player
                intentExtra.extra_position = posMillis; // VLC
                intentExtra.startfrom = posMillis;      // ViMu
            }

            // 4. 支持多集播放列表 (对应 Kotlin: playlist 转换)
            if (playData.playlist && Array.isArray(playData.playlist) && playData.playlist.length > 1) {
                var urls = [];
                var titles = [];
                playData.playlist.forEach(function (item, idx) {
                    urls.push(item.url);
                    titles.push(item.title || ("Item " + (idx + 1)));
                });
                intentExtra.video_list = urls;
                intentExtra["video_list.name"] = titles;
                intentExtra.video_list_is_explicit = true;
            }

            // 5. 组装 Intent 配置
            var intentConfig = {
                action: window.plugins.intentShim.ACTION_VIEW,
                url: videoUrl,
                type: "video/*",
                position: posMillis,
                extras: intentExtra
            };

            // 读取默认播放器
            var chosenPlayer = localStorage.getItem('lampa_default_player') || '';
            if (chosenPlayer) {
                intentConfig.package = chosenPlayer;
            }

            if (!window.plugins || !window.plugins.intentShim) {
                console.warn('[Bridge] 未找到 intentShim 插件');
                return;
            }

            // 6. 1:1 还原你原模板的 launchVideoIntent，完整保留进度处理与自动降级重试
            function launchVideoIntent(config, isRetry) {
                window.plugins.intentShim.startActivityForResult(config, function (itent) {
                    var extras = (itent && itent.extras) ? itent.extras : {};

                    // 读取播放器返回的进度（毫秒 -> 秒）
                    var returnPos = extras.position || extras.extra_position || 0;
                    var returnDur = extras.duration || extras.extra_duration || 0;

                    var time = returnPos > 0 ? (returnPos / 1000) : 0;
                    var duration = returnDur > 0 ? (returnDur / 1000) : 0;
                    var percent = duration > 0 ? parseInt(time * 100 / duration) : 100;

                    // 核心：精准回写各种层级的进度对象与回调
                    if (time && playData.timeline) {
                        playData.timeline.time = time;
                        playData.timeline.duration = duration;
                        playData.timeline.percent = percent;

                        // 触发页面插件自身的私有进度回调（如果有）
                        if (typeof playData.timeline.handler === 'function') {
                            playData.timeline.handler(percent, time, duration);
                        }

                        // 触发全局 Timeline 更新
                        if (window.Lampa && Lampa.Timeline && typeof Lampa.Timeline.update === 'function') {
                            Lampa.Timeline.update(playData.timeline);
                        } else if (typeof Timeline !== 'undefined' && typeof Timeline.update === 'function') {
                            Timeline.update(playData.timeline);
                        }
                    }
                }, function (err) {
                    // 安全降级：万一指定的播放器被卸载了，自动移除包名回退到系统每次询问！
                    if (!isRetry && config.package) {
                        console.log("[Bridge] 指定播放器启动失败，自动回退到系统选择器...");
                        var fallbackConfig = Object.assign({}, config);
                        delete fallbackConfig.package;
                        launchVideoIntent(fallbackConfig, true);
                    } else {
                        console.error("[Bridge] 启动播放器失败:", err);
                    }
                });
            }

            launchVideoIntent(intentConfig, false);
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
        openTorrentLink: function (url, jsonString) {
            if (!url) return false;

            // 1. 对应 Kotlin: val jsonData = if (jsonString == "\"\"") JSONObject() else JSONObject(jsonString)
            var jsonData = {};
            if (jsonString && jsonString !== '""') {
                try {
                    jsonData = (typeof jsonString === 'string') ? JSON.parse(jsonString) : jsonString;
                } catch (e) {
                    jsonData = {};
                }
            }

            // 2. 判断是否是 magnet 磁力链
            var isMagnet = url.toLowerCase().indexOf('magnet:') === 0;

            // 3. 构建 Extras
            var extras = {};

            // 标题三字段兼容 (title / displayName / forcename)
            if (jsonData.title) {
                extras.title = jsonData.title;
                extras.displayName = jsonData.title;
                extras.forcename = jsonData.title;
            }

            // 封面海报
            if (jsonData.poster) {
                extras.poster = jsonData.poster;
            }

            // media -> category
            if (jsonData.media) {
                extras.category = jsonData.media;
            }

            // data 对象透传
            if (jsonData.data && typeof jsonData.data === 'object') {
                extras.data = JSON.stringify(jsonData.data);
            }

            // 4. 构建 Intent 配置
            var intentConfig = {
                action: window.plugins.intentShim.ACTION_VIEW,
                url: url,
                category: "android.intent.category.BROWSABLE",
                extras: extras
            };

            // 对应 Kotlin: 非 magnet 需要设置 MIME 类型和 FLAG_GRANT_READ_URI_PERMISSION
            if (!isMagnet) {
                intentConfig.type = "application/x-bittorrent";
                // 1 对应 Intent.FLAG_GRANT_READ_URI_PERMISSION
                intentConfig.flags = 1; 
            }

            // 5. 发送 Intent
            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity(
                    intentConfig,
                    function () {
                        console.log('[Bridge] Torrent 启动成功');
                    },
                    function (err) {
                        console.error('[Bridge] 未找到可处理种子的应用(如 TorrServe):', err);
                    }
                );
                return true;
            }

            return false;
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
