/**
 * Lampa Cordova Bridge (原生适配层)
 * 负责：外部播放器 Intent、版本伪装、默认配置与系统全屏
 */
(function () {
    'use strict';

    window.Android = {
        exit: function () {
            if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
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

    // 默认出厂配置预设
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
