/**
 * Lampa Cordova Bridge (无侵入原生适配器)
 * 自动拦截并实现 window.Android 与 window.AndroidJS 接口
 */
(function () {
    'use strict';

    if (!window._cordova_certs_accepted && window.cordovaHTTP) {
        cordovaHTTP.acceptAllCerts(true, function () {}, function () {});
        window._cordova_certs_accepted = true;
    }

    window.Android = {
        exit: function () {
            if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
        },

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
                if (!hasContentType) headers["Content-Type"] = contentType;
            }

            function executeFetch(targetUrl, method, bodyContent) {
                var fetchOptions = { method: method, headers: headers };
                if (bodyContent) fetchOptions.body = bodyContent;
                if (window.cordovaFetch && cordovaFetch.setTimeout) cordovaFetch.setTimeout = 60;

                cordovaFetch(targetUrl, fetchOptions)
                    .then(function (response) {
                        if (response.status >= 200 && response.status < 400) {
                            return dataType === 'json' ? response.json() : response.text();
                        } else {
                            throw { status: response.status, error: response.statusText };
                        }
                    })
                    .then(function (parsedData) { secuses(parsedData); })
                    .catch(function (err) { error({ status: (err && err.status) || 404 }, (err && err.error) || ''); });
            }

            if (!requestContent) {
                var isHttp = url && typeof url === 'string' && (url.indexOf('http://') === 0 || url.indexOf('https://') === 0);
                var isSpecialDdys = url && url.indexOf('ddys') !== -1;

                if (isSpecialDdys || !isHttp) {
                    executeFetch(url, 'GET', null);
                } else {
                    cordovaHTTP.get(url, {}, headers, function (response) {
                        if (dataType === 'json') {
                            try { secuses(JSON.parse(response.data)); } catch (e) { error({ status: response.status }, response.error); }
                        } else {
                            secuses(response.data);
                        }
                    }, function (response) { error({ status: response.status }, response.error); });
                }
            } else {
                if (!isJsonString) {
                    var formObj = {};
                    requestContent.split('&').forEach(function (pair) {
                        var parts = pair.split('=');
                        if (parts[0]) formObj[decodeURIComponent(parts[0])] = decodeURIComponent(parts[1] || '');
                    });

                    cordovaHTTP.post(url, formObj, headers, function (response) {
                        if (dataType === 'json') {
                            try { secuses(JSON.parse(response.data)); } catch (e) { error({ status: response.status }, response.error); }
                        } else {
                            secuses(response.data);
                        }
                    }, function (response) { error({ status: response.status }, response.error); });
                } else {
                    executeFetch(url, 'POST', requestContent);
                }
            }
        },

        openPlayer: function (url, data) {
            data = data || {};
            var pos = parseInt((data.timeline ? data.timeline.time || -1 : -1) * 1000);
            var intentExtra = {
                title: data.title || data.path || '',
                position: pos,
                return_result: true,
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

            var chosenPlayer = localStorage.getItem('lampa_default_player') || '';
            if (chosenPlayer) intentConfig.package = chosenPlayer;

            function launchVideoIntent(config, isRetry) {
                window.plugins.intentShim.startActivityForResult(config, function (itent) {
                    var extras = itent.extras || {};
                    var time = (extras.position || extras.extra_position) / 1000;
                    var duration = (extras.duration || extras.extra_duration) / 1000;
                    var percent = duration > 0 ? parseInt(time * 100 / duration) : 100;

                    if (time && data.timeline) {
                        data.timeline.time = time;
                        data.timeline.duration = duration;
                        data.timeline.percent = percent;
                        if (typeof data.timeline.handler === 'function') data.timeline.handler(percent, time, duration);
                        if (window.Lampa && Lampa.Timeline && typeof Lampa.Timeline.update === 'function') {
                            Lampa.Timeline.update(data.timeline);
                        } else if (typeof Timeline !== 'undefined' && typeof Timeline.update === 'function') {
                            Timeline.update(data.timeline);
                        }
                    }
                }, function (err) {
                    if (!isRetry && config.package) {
                        console.log("[Player] 默认播放器打开失败，回退到系统选择器...");
                        var fallback = Object.assign({}, config);
                        delete fallback.package;
                        launchVideoIntent(fallback, true);
                    } else {
                        console.log("Failed to open video URL via Android Intent", err);
                    }
                });
            }

            launchVideoIntent(intentConfig, false);
        }
    };

    window.AndroidJS = {
        appVersion: function () { return '3.3.3-24'; },
        exit: function () { window.Android.exit(); },
        clearDefaultPlayer: function () {
            if (window.selectDefaultPlayerMenu) window.selectDefaultPlayerMenu();
            else localStorage.removeItem('lampa_default_player');
        },
        openYoutube: function (link) {
            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity({ action: window.plugins.intentShim.ACTION_VIEW, url: link });
            }
        },
        openPlayer: function (link) {
            if (window.cordova && cordova.InAppBrowser) cordova.InAppBrowser.open(link, '_system');
        },
        openTorrentLink: function (urlOrMagnet) {
            if (window.plugins && window.plugins.intentShim) {
                window.plugins.intentShim.startActivity({
                    action: window.plugins.intentShim.ACTION_VIEW,
                    url: urlOrMagnet,
                    extras: { action: "play", data: { lampa: true } }
                });
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
        updateChannel: function () {},
        saveBookmarks: function () {}
    };

    // 默认出厂配置预设（替代正则修改配置）
    try {
        if (!localStorage.getItem('lampa_cordova_initiale')) {
            localStorage.setItem('lampa_cordova_initiale', 'true');
            localStorage.setItem('screensaver', 'false');
            localStorage.setItem('device_name', 'Lampa Cordova');
            localStorage.setItem('keyboard_type', 'integrate');
        }
    } catch (e) {}

    // 原生层全局监听：沉浸式状态栏隐藏
    document.addEventListener('deviceready', function () {
        if (window.StatusBar) window.StatusBar.hide();
    }, false);
})();
