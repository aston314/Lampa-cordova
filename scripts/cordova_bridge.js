/**
 * Lampa Cordova Bridge (无侵入原生适配器)
 * 功能：将 Lampa 原生 Android/AndroidJS 接口完整映射到 Cordova 插件
 * 依赖插件：
 *   - cordova-plugin-advanced-http (cordovaHTTP)
 *   - cordova-plugin-fetch (cordovaFetch)
 *   - com-darryncampbell-cordova-plugin-intent (intentShim)
 *   - cordova-plugin-inappbrowser
 *   - cordova-plugin-statusbar
 */

(function () {
    'use strict';

    // 0. 基础环境标志与证书信任
    if (!window._cordova_certs_accepted && window.cordovaHTTP) {
        cordovaHTTP.acceptAllCerts(true, function () {}, function () {});
        window._cordova_certs_accepted = true;
    }

    // =========================================================================
    // 1. window.Android 核心接口实现 (网络请求 / 播放器启动 / 应用退出)
    // =========================================================================
    window.Android = {
        /**
         * 退出应用
         */
        exit: function () {
            if (navigator.app && navigator.app.exitApp) {
                navigator.app.exitApp();
            } else if (navigator.device && navigator.device.exitApp) {
                navigator.device.exitApp();
            }
        },

        /**
         * 核心网络请求引擎 (支持 GET/POST/表单/JSON/自动证书信任/ddys降级)
         */
        httpReq: function (params, callbacks) {
            var secuses = callbacks.complite || function () {};
            var error = callbacks.error || function () {};

            if (!window._cordova_certs_accepted && window.cordovaHTTP) {
                cordovaHTTP.acceptAllCerts(true, function () {}, function () {});
                window._cordova_certs_accepted = true;
            }

            var url = params.url;
            var data = params.post_data;
            var headers = params.headers || {};
            var dataType = params.dataType || 'json';
            var contentType = params.contentType || '';

            var isJsonString = false;
            var requestContent = "";

            if (data) {
                if (typeof data === "string") {
                    requestContent = data;
                    try {
                        JSON.parse(requestContent);
                        isJsonString = true;
                        contentType = contentType || "application/json";
                    } catch (e) {
                        contentType = contentType || "application/x-www-form-urlencoded";
                    }
                } else if (typeof data === "object") {
                    contentType = "application/json";
                    requestContent = JSON.stringify(data);
                    isJsonString = true;
                }
            }

            if (requestContent !== "") {
                var hasContentType = false;
                for (var k in headers) {
                    if (k.toLowerCase() === 'content-type') {
                        hasContentType = true;
                        break;
                    }
                }
                if (!hasContentType) {
                    headers["Content-Type"] = contentType;
                }
            }

            function executeFetch(targetUrl, method, bodyContent) {
                var fetchOptions = {
                    method: method,
                    headers: headers
                };
                if (bodyContent) {
                    fetchOptions.body = bodyContent;
                }
                if (window.cordovaFetch && cordovaFetch.setTimeout) {
                    cordovaFetch.setTimeout = 60;
                }

                cordovaFetch(targetUrl, fetchOptions)
                    .then(function (response) {
                        if (response.status >= 200 && response.status < 400) {
                            return dataType === 'json' ? response.json() : response.text();
                        } else {
                            throw { status: response.status, error: response.statusText };
                        }
                    })
                    .then(function (parsedData) {
                        secuses(parsedData);
                    })
                    .catch(function (err) {
                        error({ status: (err && err.status) || 404 }, (err && err.error) || '');
                    });
            }

            if (!requestContent) {
                var isHttp = url && typeof url === 'string' && (url.indexOf('http://') === 0 || url.indexOf('https://') === 0);
                var isSpecialDdys = url && url.indexOf('ddys') !== -1;

                if (isSpecialDdys || !isHttp) {
                    executeFetch(url, 'GET', null);
                } else {
                    cordovaHTTP.get(url, {}, headers, function (response) {
                        if (dataType === 'json') {
                            try {
                                secuses(JSON.parse(response.data));
                            } catch (e) {
                                error({ status: response.status }, response.error);
                            }
                        } else {
                            secuses(response.data);
                        }
                    }, function (response) {
                        error({ status: response.status }, response.error);
                    });
                }
            } else {
                if (!isJsonString) {
                    var formObj = {};
                    requestContent.split('&').forEach(function (pair) {
                        var parts = pair.split('=');
                        if (parts[0]) {
                            formObj[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1] || '');
                        }
                    });

                    cordovaHTTP.post(url, formObj, headers, function (response) {
                        if (dataType === 'json') {
                            try {
                                secuses(JSON.parse(response.data));
                            } catch (e) {
                                error({ status: response.status }, response.error);
                            }
                        } else {
                            secuses(response.data);
                        }
                    }, function (response) {
                        error({ status: response.status }, response.error);
                    });
                } else {
                    executeFetch(url, 'POST', requestContent);
                }
            }
        },

        /**
         * 外部播放器调起与时间线/进度同步 (支持包名直启与自动回退)
         */
        openPlayer: function (url, data) {
            data = data || {};
            var pos = parseInt((data.timeline ? data.timeline.time || -1 : -1) * 1000);

            var intentExtra = {
                title: data.title || data.path || '',
                position: pos,
                return_result: true,
                sticky: false,
                from_start: false,
                forcename: data.title || data.path || '',
                startfrom: pos,
                forcedirect: true,
                forceresume: true
            };

            var intentConfig = {
                action: window.plugins.intentShim.ACTION_VIEW,
                url: data.url || url,
                position: pos,
                type: "video/*",
                extras: intentExtra
            };

            // 读取预设的默认播放器包名 (例如: org.videolan.vlc, net.gtvbox.videoplayer 等)
            var chosenPlayer = localStorage.getItem('lampa_default_player') || '';
            if (chosenPlayer) {
                intentConfig.package = chosenPlayer;
            }

            function launchVideoIntent(config, isRetry) {
                window.plugins.intentShim.startActivityForResult(config, function (itent) {
                    var extras = itent.extras || {};
                    var time = (extras.position || extras.extra_position) / 1000;
                    var duration = (extras.duration || extras.extra_duration) / 1000;
                    var percent = 100;
                    if (duration > 0) {
                        percent = parseInt((time * 100) / duration);
                    }

                    if (time && data.timeline) {
                        data.timeline.time = time;
                        data.timeline.duration = duration;
                        data.timeline.percent = percent;

                        if (typeof data.timeline.handler === 'function') {
                            data.timeline.handler(percent, time, duration);
                        }

                        if (window.Lampa && Lampa.Timeline && typeof Lampa.Timeline.update === 'function') {
                            Lampa.Timeline.update(data.timeline);
                        } else if (typeof Timeline !== 'undefined' && typeof Timeline.update === 'function') {
                            Timeline.update(data.timeline);
                        }
                    }
                }, function (err) {
                    // 安全降级机制：如果指定包名的播放器未安装/打开失败，自动移除包名回退到系统播放器选择菜单
                    if (!isRetry && config.package) {
                        console.log("[Player] 指定播放器启动失败，自动回退到系统选择器...");
                        var fallbackConfig = Object.assign({}, config);
                        delete fallbackConfig.package;
                        launchVideoIntent(fallbackConfig, true);
                    } else {
                        console.log("Failed to open video URL via Android Intent", err);
                    }
                });
            }

            launchVideoIntent(intentConfig, false);
        }
    };

    // =========================================================================
    // 2. window.AndroidJS 扩展接口实现 (版本/播放器/语音/磁力/YouTube)
    // =========================================================================
    window.AndroidJS = {
        /**
         * 退出应用
         */
        exit: function () {
            window.Android.exit();
        },

        /**
         * 伪造 Lampa Android 原生客户端版本号，满足平台检查
         */
        appVersion: function () {
            return '3.3.3';
        },

        /**
         * 清除/重置默认播放器 (呼出多语言选择菜单)
         */
        clearDefaultPlayer: function () {
            if (window.selectDefaultPlayerMenu) {
                window.selectDefaultPlayerMenu();
            } else {
                localStorage.removeItem('lampa_default_player');
            }
        },

        /**
         * 调起原生语音识别
         */
        voiceStart: function () {
            if (!window.plugins || !window.plugins.intentShim) return;

            var curL = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'en';
            var voiceExtras = {
                "android.speech.extra.LANGUAGE_MODEL": "free_form",
                "android.speech.extra.MAX_RESULTS": 1
            };

            if (curL === 'zh') {
                voiceExtras["android.speech.extra.PROMPT"] = "请说出影片名称...";
            }

            window.plugins.intentShim.startActivityForResult({
                action: "android.speech.action.RECOGNIZE_SPEECH",
                extras: voiceExtras
            }, function (result) {
                var extras = result.extras || {};
                var matches = extras['android.speech.extra.RESULTS'] || extras.results;
                if (matches) {
                    var text = Array.isArray(matches) ? matches[0] : matches;
                    if (text && window.voiceResult) {
                        window.voiceResult(text);
                    }
                }
            }, function (err) {
                console.warn('[Voice] 语音识别取消或未安装语音服务:', err);
                if (window.Lampa && Lampa.Noty) {
                    var failMsg = (curL === 'zh') ? '未检测到可用语音服务' : 'Voice service not available';
                    Lampa.Noty.show(failMsg);
                }
            });
        },

        /**
         * 调起系统外部应用播放 YouTube
         */
        openYoutube: function (link) {
            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity({
                    action: window.plugins.intentShim.ACTION_VIEW,
                    url: link
                }, function () {}, function () {
                    console.log("Failed to open Youtube URL via Android Intent");
                });
            }
        },

        /**
         * 调起外部播放器 (InAppBrowser 系统浏览器模式)
         */
        openPlayer: function (link, data) {
            if (window.cordova && cordova.InAppBrowser) {
                cordova.InAppBrowser.open(link, '_system');
            }
        },

        /**
         * 调起种子/磁力链客户端 (例如 TorrServer / BitTorrent)
         */
        openTorrentLink: function (urlOrMagnet, extraJson) {
            var intentExtra = {
                action: "play",
                data: { lampa: true }
            };

            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity({
                    action: window.plugins.intentShim.ACTION_VIEW,
                    url: urlOrMagnet,
                    extras: intentExtra
                }, function () {}, function () {
                    console.log('Failed to open magnet URL via Android Intent');
                });
            }
        },

        /**
         * 频道与书签安全空实现 (防止报错)
         */
        updateChannel: function (where) {},
        saveBookmarks: function () {}
    };

    // =========================================================================
    // 3. 初始参数预设 (代替原脚本中多条修改默认设置的正则)
    // =========================================================================
    try {
        if (!localStorage.getItem('lampa_cordova_initiale')) {
            localStorage.setItem('lampa_cordova_initiale', 'true');
            // 关闭屏保
            localStorage.setItem('screensaver', 'false');
            // 默认设备名
            localStorage.setItem('device_name', 'Lampa Cordova');
            // 默认内置集成键盘
            localStorage.setItem('keyboard_type', 'integrate');
        }
    } catch (e) {
        console.warn('[Bridge] 初始化出厂配置异常:', e);
    }

    // =========================================================================
    // 4. 原生底层监听：全屏沉浸、隐藏状态栏
    // =========================================================================
    document.addEventListener('deviceready', function () {
        if (window.StatusBar) {
            window.StatusBar.hide();
        }
    }, false);

})();
