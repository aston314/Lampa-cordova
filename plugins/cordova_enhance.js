(function () {
    'use strict';

    // ================= 0. 单例保护：杜绝热重载/二次载入导致的事件重复挂载 =================
    if (window._aston_update_inited) {
        console.log('[AstonUpdate] 插件已在内存中运行，跳过重复注册');
        return;
    }
    window._aston_update_inited = true;

    // 动态获取常量，彻底杜绝顶部闭包过早固化为 1 导致的误报新版本
    function getBuildCode() {
        return window.CURRENT_BUILD_CODE || 1;
    }

    function getRepoPath() {
        return window.CURRENT_REPO || 'owner/repo';
    }

    // ================= 1. 样式注入（含遥控器选中、鼠标悬浮与原生聚焦对齐） =================
    function injectStyles() {
        if (document.getElementById('aston-update-style')) return;
        var style = document.createElement('style');
        style.id = 'aston-update-style';
        style.type = 'text/css';
        style.innerHTML = 
            '.head__action.aston-update-action { position: relative; display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; }' +
            '.aston-update-dot { position: absolute; top: 4px; right: 4px; width: 8px; height: 8px; background: #ff3b30; border-radius: 50%; box-shadow: 0 0 6px #ff3b30; pointer-events: none; }' +
            '.aston-update-ring { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform: rotate(-90deg); display: none; pointer-events: none; }' +
            /* 核心修复：对齐遥控器选中(.focus)、鼠标悬停(:hover)与键盘聚焦(:focus)，底色纯白圆角 */
            '.head__action.aston-update-action.focus, .head__action.aston-update-action:hover, .head__action.aston-update-action:focus { background: #fff !important; color: #000 !important; border-radius: 50%; outline: none; }';
        document.head.appendChild(style);
    }

    // ================= 2. 12 国全语言字典（修复希伯来语西里尔字符污染） =================
    function initAstonI18n() {
        if (window._aston_full_lang_inited || !window.Lampa || !Lampa.Lang) return;
        Lampa.Lang.add({
            aston_menu_title: { zh: '快捷菜单', en: 'Quick Menu', ru: 'Быстрое меню', uk: 'Швидке меню', be: 'Хуткае меню', bg: 'Бързо меню', cs: 'Rychlé menu', fr: 'Menu rapide', he: 'תפריט מהיר', pl: 'Szybkie menu', pt: 'Menu rápido', ro: 'Meniu rapid' },
            aston_menu_player: { zh: '默认播放器', en: 'Default Player', ru: 'Плеер по умолчанию', uk: 'Плеєр за замовчуванням', be: 'Плэер па змаўчанні', bg: 'Плейър по подразбиране', cs: 'Výchozí přehrávač', fr: 'Lecteur par défaut', he: 'נגן ברירת מחדל', pl: 'Domyślny odtwarzacz', pt: 'Reprodutor padrão', ro: 'Player implicit' },
            aston_player_system: { zh: '系统选择 / 每次询问', en: 'System Chooser / Always ask', ru: 'Системный выбор / Спрашивать', uk: 'Системний вибір / Запитувати', be: 'Сістэмны выбар / Пытацца', bg: 'Избор от системата / Винаги питай', cs: 'Systémový výběr / Vždy se ptát', fr: 'Sélecteur système / Toujours demander', he: 'בורר המערכת / שאל תמיד', pl: 'Wybór systemowy / Zawsze pytaj', pt: 'Seletor do sistema / Sempre perguntar', ro: 'Selector de sistem / Întreabă mereu' },
            aston_player_set_done: { zh: '已设置默认播放器', en: 'Default player set to', ru: 'Плеер установлен', uk: 'Плеєр встановлено', be: 'Плэер усталяваны', bg: 'Плейърът е зададен', cs: 'Výchozí přehrávač nastaven', fr: 'Lecteur par défaut défini sur', he: 'נגן ברירת מחדל הוגדר', pl: 'Ustawiono domyślny odtwarzacz', pt: 'Reprodutor padrão definido', ro: 'Player implicit setat' },
            // 字符集修复：原 'טעינה מחדш' (含俄语ш) 已修正为标准希伯来语 'טעינה מחדש'
            aston_menu_reload: { zh: '重新加载', en: 'Reload', ru: 'Перезагрузить', uk: 'Перезавантажити', be: 'Перазагрузіць', bg: 'Презареждане', cs: 'Znovu načíst', fr: 'Recharger', he: 'טעינה מחדש', pl: 'Przeładuj', pt: 'Recarregar', ro: 'Reîncărcare' },
            aston_menu_reload_descr: { zh: '刷新当前界面与数据', en: 'Refresh interface and data', ru: 'Обновить интерфейс и данные', uk: 'Оновити інтерфейс та дані', be: 'Абнавіць інтэрфейс і дадзеныя', bg: 'Опресняване на интерфейса и данните', cs: 'Obnovit rozhraní a data', fr: "Actualiser l'interface et les données", he: 'רענון הממשק והנתונים', pl: 'Odśwież interfejs i dane', pt: 'Atualizar interface e dados', ro: 'Reîmprospătează interfața și datele' },
            aston_menu_exit: { zh: '退出应用', en: 'Exit', ru: 'Выход', uk: 'Вихід', be: 'Выхад', bg: 'Изход', cs: 'Ukončit', fr: 'Quitter', he: 'יציאה', pl: 'Wyjście', pt: 'Sair', ro: 'Ieșire' },
            aston_menu_exit_descr: { zh: '清理临时缓存并退出 Lampa', en: 'Clean cache and exit Lampa', ru: 'Очистить кэш и выйти из Lampa', uk: 'Очистити кеш та вийти з Lampa', be: 'Ачысціць кэш і выйсці з Lampa', bg: 'Изчистване на кеша и изход', cs: 'Vymazat mezipaměť a ukončit', fr: 'Vider le cache et quitter', he: 'ניקוי מטמון ויציאה מ-Lampa', pl: 'Wyczyść pamięć podręczną i wyjdź', pt: 'Limpar cache e sair', ro: 'Curăță memoria cache și ieși' },
            aston_update_found: { zh: '发现新版本', en: 'New Version Available', ru: 'Доступна новая версия', uk: 'Доступна нова версія', be: 'Даступная новая версія', bg: 'Налична е нова версия', cs: 'Nová verze k dispozici', fr: 'Nouvelle version disponible', he: 'גרסה חדשה זמינה', pl: 'Dostępna nowa wersja', pt: 'Nova versão disponível', ro: 'Versiune nouă disponibilă' },
            aston_update_now: { zh: '立即更新', en: 'Update Now', ru: 'Обновить', uk: 'Оновити', be: 'Абнавіць', bg: 'Обнови', cs: 'Aktualizovat', fr: 'Mettre à jour', he: 'עדכן עכשיו', pl: 'Aktualizuj', pt: 'Atualizar agora', ro: 'Actualizează acum' },
            aston_update_later: { zh: '稍后再说', en: 'Later', ru: 'Позже', uk: 'Пізніше', be: 'Пазней', bg: 'По-късно', cs: 'Později', fr: 'Plus tard', he: 'מאוחר יותר', pl: 'Później', pt: 'Mais tarde', ro: 'Mai târziu' },
            aston_update_start: { zh: '开始下载更新包...', en: 'Starting update download...', ru: 'Запуск загрузки обновления...', uk: 'Початок завантаження оновлення...', be: 'Пачатак загрузкі абнаўлення...', bg: 'Стартиране на изтеглянето...', cs: 'Zahájení stahování...', fr: 'Démarrage du téléchargement...', he: 'מתחיל להוריד עדכון...', pl: 'Rozpoczynanie pobierania...', pt: 'Iniciando download...', ro: 'Se începe descărcarea...' },
            aston_update_downloading: { zh: '正在下载', en: 'Downloading', ru: 'Загрузка', uk: 'Завантаження', be: 'Загрузка', bg: 'Изтегляне', cs: 'Stahování', fr: 'Téléchargement', he: 'מוריד', pl: 'Pobieranie', pt: 'Baixando', ro: 'Descărcare' },
            aston_update_installing: { zh: '下载完成，正在唤起系统安装器...', en: 'Downloaded, opening installer...', ru: 'Загружено, запуск установщика...', uk: 'Завантажено, запуск інсталятора...', be: 'Загружана, запуск усталёўшчыка...', bg: 'Изтеглено, отваряне на инсталатора...', cs: 'Staženo, otevírání instalátoru...', fr: "Ouverture de l'installateur...", he: 'הורד, פותח מתקין...', pl: 'Pobrano, otwieranie instalatora...', pt: 'Baixado, abrindo instalador...', ro: 'Descărcat, deschidere instalator...' },
            aston_update_failed: { zh: '下载失败', en: 'Download failed', ru: 'Ошибка загрузки', uk: 'Помилка завантаження', be: 'Памылка загрузкі', bg: 'Грешка при изтегляне', cs: 'Stahování selhalo', fr: 'Échec du téléchargement', he: 'ההורדה נכשלה', pl: 'Pobieranie nie powiodło się', pt: 'Falha no download', ro: 'Descărcare eșuată' },
            aston_update_error: { zh: '下载出错，请检查网络连接', en: 'Download error, please check connection', ru: 'Ошибка загрузки, проверьте сеть', uk: 'Помилка завантаження, перевірте мережу', be: 'Памылка загрузкі, праверце сетку', bg: 'Грешка при изтегляне, проверете мрежата', cs: 'Chyba stahování, zkontrolujte síť', fr: 'Erreur de téléchargement, vérifiez le réseau', he: 'שגיאת הורדה, בדוק חיבור לרשת', pl: 'Błąd pobierania, sprawdź połączenie', pt: 'Erro no download, verifique a conexão', ro: 'Eroare de descărcare, verificați rețeaua' },
            aston_update_timeout: { zh: '下载超时，请重试', en: 'Download timed out, please retry', ru: 'Время загрузки истекло', uk: 'Час завантаження минув', be: 'Час загрузкі скончыўся', bg: 'Времето за изтегляне изтече', cs: 'Časový limit stahování vypršel', fr: 'Délai de téléchargement dépassé', he: 'זמן ההורדה תם', pl: 'Przekroczono limit czasu pobierania', pt: 'Tempo limite de download esgotado', ro: 'Timpul de descărcare a expirat' },
            aston_update_sub: { zh: '在线极速下载并覆盖升级', en: 'Download and update online', ru: 'Онлайн загрузка и обновление', uk: 'Онлайн завантаження та оновлення', be: 'Анлайн загрузка і абнаўленне', bg: 'Онлайн изтегляне и обновяване', cs: 'Online stažení a aktualizace', fr: 'Télécharger et mettre à jour en ligne', he: 'הורד ועדכן באופן מקוון', pl: 'Pobierz i zaktualizuj online', pt: 'Baixar e atualizar online', ro: 'Descărcați și actualizați online' }
        });
        window._aston_full_lang_inited = true;
    }

    function t(key, fallback) {
        return (window.Lampa && Lampa.Lang && Lampa.Lang.translate(key)) || fallback;
    }

    // ================= 3. 缓存清理与安全退出 =================
    function cleanCacheAndExit() {
        if (window.resolveLocalFileSystemURL && window.cordova && cordova.file && cordova.file.cacheDirectory) {
            window.resolveLocalFileSystemURL(cordova.file.cacheDirectory, function (dirEntry) {
                var reader = dirEntry.createReader();
                reader.readEntries(function (entries) {
                    var total = entries.length;
                    if (total === 0) {
                        if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
                        return;
                    }
                    var done = 0;
                    var onFinish = function () {
                        done++;
                        if (done >= total && navigator.app && navigator.app.exitApp) {
                            navigator.app.exitApp();
                        }
                    };
                    entries.forEach(function (entry) {
                        if (entry.isDirectory) {
                            entry.removeRecursively(onFinish, onFinish);
                        } else {
                            entry.remove(onFinish, onFinish);
                        }
                    });
                }, function (err) {
                    console.warn('[AstonUpdate] 遍历缓存文件失败:', err);
                    if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
                });
            }, function (err) {
                console.warn('[AstonUpdate] 解析本地缓存目录失败:', err);
                if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
            });
        } else {
            if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
        }
    }

    // ================= 4. 原生设置：播放器多语言选择菜单 =================
    window.selectDefaultPlayerMenu = function () {
        initAstonI18n();
        var curL = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'ru';
        var isZh = (curL === 'zh');
        var currentPackage = localStorage.getItem('lampa_default_player') || '';

        var players = [
            { title: t('aston_player_system', '系统选择 / 每次询问'), package: '', desc: isZh ? '不锁定特定 App，每次弹出系统列表' : 'Always show system chooser' },
            { title: isZh ? 'DDD 视频播放器' : 'DDD Video Player', package: 'top.rootu.dddplayer', desc: isZh ? '专为大屏打造的高性能播放器' : 'Fast Android TV video player' },
            { title: 'Vimu Media Player', package: 'net.gtvbox.videoplayer', desc: isZh ? 'Android TV 顶级画质与全景声播放器' : 'High quality Android TV media player' },
            { title: isZh ? 'MX Player Pro (专业版)' : 'MX Player Pro', package: 'com.mxtech.videoplayer.pro', desc: isZh ? '经典硬件解码万能播放器' : 'Advanced hardware acceleration' },
            { title: isZh ? 'MX Player (标准版)' : 'MX Player', package: 'com.mxtech.videoplayer.ad', desc: isZh ? '通用免费版本' : 'Standard free edition' },
            { title: 'VLC for Android', package: 'org.videolan.vlc', desc: isZh ? '开源强劲播放器' : 'Open-source media player' },
            { title: 'Just Player', package: 'com.brouken.player', desc: isZh ? '轻量现代 ExoPlayer 引擎' : 'Lightweight ExoPlayer' },
            { title: 'Kodi', package: 'org.xbmc.kodi', desc: isZh ? '强大家庭影音中心' : 'Ultimate home theater' }
        ];

        var items = players.map(function (item) {
            var isCur = (item.package === currentPackage);
            return {
                title: (isCur ? '✓ ' : '') + item.title,
                subtitle: item.desc,
                selected: isCur,
                onSelect: function () {
                    if (item.package) {
                        localStorage.setItem('lampa_default_player', item.package);
                        localStorage.setItem('lampa_default_player_name', item.title);
                    } else {
                        localStorage.removeItem('lampa_default_player');
                        localStorage.removeItem('lampa_default_player_name');
                    }
                    if (window.Lampa && Lampa.Noty) {
                        Lampa.Noty.show(t('aston_player_set_done', '已设置默认播放器') + ': ' + item.title);
                    }
                    if (Lampa.Controller) Lampa.Controller.toggle('settings');
                }
            };
        });

        if (window.Lampa && Lampa.Select) {
            Lampa.Select.show({
                title: t('aston_menu_player', '默认播放器'),
                items: items,
                onBack: function () {
                    if (Lampa.Controller) Lampa.Controller.toggle('settings');
                }
            });
        }
    };

    // ================= 5. 遥控器设置键快捷菜单 =================
    function triggerAstonQuickMenu() {
        if (window.Lampa && Lampa.Player && Lampa.Player.opened && Lampa.Player.opened()) return;

        if (window.Lampa && Lampa.Select) {
            initAstonI18n();
            Lampa.Select.show({
                title: t('aston_menu_title', '快捷菜单'),
                items: [
                    {
                        title: t('aston_menu_reload', '重新加载'),
                        subtitle: t('aston_menu_reload_descr', '刷新当前界面与数据'),
                        onSelect: function () { window.location.reload(); }
                    },
                    {
                        title: t('aston_menu_exit', '退出应用'),
                        subtitle: t('aston_menu_exit_descr', '清理临时缓存并退出 Lampa'),
                        onSelect: function () { cleanCacheAndExit(); }
                    }
                ],
                onBack: function () {
                    if (Lampa.Controller) Lampa.Controller.toggle('content');
                }
            });
        }
    }

    // ================= 6. 极速下载与安装唤起（补齐错误与超时处理） =================
    function startUpdateDownload(downloadUrl, versionName) {
        var dot = document.getElementById('aston_update_dot');
        var ringSvg = document.getElementById('aston_update_ring_svg');
        var ringFill = document.getElementById('aston_ring_fill');

        function resetBadge() {
            if (ringSvg) ringSvg.style.display = 'none';
            if (dot) dot.style.display = 'block';
        }

        if (dot) dot.style.display = 'none';
        if (ringSvg) ringSvg.style.display = 'block';
        if (ringFill) ringFill.style.strokeDashoffset = '94.25';

        if (window.Lampa && Lampa.Noty) {
            Lampa.Noty.show(t('aston_update_start', '开始下载更新包...'));
        }

        var xhr = new XMLHttpRequest();
        xhr.open('GET', downloadUrl, true);
        xhr.responseType = 'blob';
        xhr.timeout = 180000; // 下载宽限 3 分钟

        xhr.onprogress = function (e) {
            if (e.lengthComputable) {
                var pct = Math.round((e.loaded / e.total) * 100);
                var loadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
                var totalMB = (e.total / (1024 * 1024)).toFixed(1);
                if (window.Lampa && Lampa.Noty) {
                    Lampa.Noty.show(t('aston_update_downloading', '正在下载') + ' ' + versionName + ': ' + pct + '% (' + loadedMB + '/' + totalMB + ' MB)');
                }
                if (ringFill) {
                    ringFill.style.strokeDashoffset = (94.25 * (1 - (pct / 100))).toFixed(2);
                }
            }
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                if (ringFill) ringFill.style.strokeDashoffset = '0';
                if (window.Lampa && Lampa.Noty) {
                    Lampa.Noty.show(t('aston_update_installing', '下载完成，正在唤起系统安装器...'));
                }
                var blob = xhr.response;
                var targetDir = (window.cordova && cordova.file && (cordova.file.externalCacheDirectory || cordova.file.cacheDirectory)) || '';

                if (!targetDir || !window.resolveLocalFileSystemURL) {
                    window.open(downloadUrl, '_system');
                    return;
                }

                window.resolveLocalFileSystemURL(targetDir, function (dirEntry) {
                    dirEntry.getFile('update.apk', { create: false }, function (oldFile) {
                        oldFile.remove(function () {
                            writeNewApk(dirEntry, blob, downloadUrl);
                        }, function () {
                            writeNewApk(dirEntry, blob, downloadUrl);
                        });
                    }, function () {
                        writeNewApk(dirEntry, blob, downloadUrl);
                    });
                }, function (err) {
                    console.warn('[AstonUpdate] 目录解析失败，降级外部下载:', err);
                    resetBadge();
                    if (window.cordova && cordova.InAppBrowser) {
                        cordova.InAppBrowser.open(downloadUrl, '_system');
                    }
                });
            } else {
                resetBadge();
                if (window.Lampa && Lampa.Noty) Lampa.Noty.show(t('aston_update_failed', '下载失败') + ': ' + xhr.status);
            }
        };

        // 核心加固：fileWriter 增加 onerror 回调，杜绝无感静默卡死
        function writeNewApk(dirEntry, blob, fallbackUrl) {
            dirEntry.getFile('update.apk', { create: true, overwrite: true }, function (fileEntry) {
                fileEntry.createWriter(function (fileWriter) {
                    fileWriter.onwriteend = function () {
                        var installUrl = fileEntry.nativeURL || fileEntry.toURL();
                        if (window.plugins && window.plugins.intentShim) {
                            window.plugins.intentShim.startActivity({
                                action: 'android.intent.action.VIEW',
                                url: installUrl,
                                type: 'application/vnd.android.package-archive',
                                flags: [268435456, 1]
                            }, function () {}, function (err) {
                                console.warn('[AstonUpdate] Intent 调起失败，降级外部打开:', err);
                                if (window.cordova && cordova.InAppBrowser) {
                                    cordova.InAppBrowser.open(fallbackUrl, '_system');
                                }
                            });
                        }
                    };
                    fileWriter.onerror = function (err) {
                        console.warn('[AstonUpdate] 文件写入失败，降级外部下载:', err);
                        resetBadge();
                        if (window.cordova && cordova.InAppBrowser) {
                            cordova.InAppBrowser.open(fallbackUrl, '_system');
                        }
                    };
                    fileWriter.write(blob);
                });
            }, function (err) {
                console.warn('[AstonUpdate] 创建安装包文件句柄失败:', err);
                resetBadge();
                if (window.cordova && cordova.InAppBrowser) {
                    cordova.InAppBrowser.open(fallbackUrl, '_system');
                }
            });
        }

        xhr.onerror = function (err) {
            console.warn('[AstonUpdate] 安装包下载网络错误:', err);
            resetBadge();
            if (window.Lampa && Lampa.Noty) Lampa.Noty.show(t('aston_update_error', '下载出错，请检查网络连接'));
        };

        xhr.ontimeout = function () {
            console.warn('[AstonUpdate] 安装包下载连接超时');
            resetBadge();
            if (window.Lampa && Lampa.Noty) Lampa.Noty.show(t('aston_update_timeout', '下载超时，请重试'));
        };

        xhr.send();
    }

    function showUpdateDialog(info, dlUrl, showVer) {
        initAstonI18n();
        if (window.Lampa && Lampa.Select) {
            var controller_enabled = (Lampa.Controller && Lampa.Controller.enabled()) ? Lampa.Controller.enabled().name : 'head';
            var doRestoreFocus = function () {
                if (Lampa.Controller) Lampa.Controller.toggle(controller_enabled);
            };

            Lampa.Select.show({
                title: t('aston_update_found', '发现新版本') + ' ' + showVer,
                items: [
                    {
                        title: t('aston_update_now', '立即更新'),
                        subtitle: t('aston_update_sub', '在线极速下载并覆盖升级'),
                        onSelect: function () { startUpdateDownload(dlUrl, showVer); }
                    },
                    {
                        title: t('aston_update_later', '稍后再说'),
                        subtitle: '',
                        onSelect: doRestoreFocus
                    }
                ],
                onBack: doRestoreFocus
            });
        }
    }

    // ================= 7. 渲染顶栏更新角标（补齐 hover:focus 焦点状态切换） =================
    function renderHeaderUpdateBadge(info, dlUrl, showVer) {
        if (document.getElementById('aston_header_update_btn')) return;

        var targetHeader = document.querySelector('.head__actions') || document.querySelector('.head');
        if (!targetHeader) return;

        initAstonI18n();
        var btn = document.createElement('div');
        btn.id = 'aston_header_update_btn';
        btn.className = 'head__action selector aston-update-action';
        btn.setAttribute('tabindex', '0');
        btn.setAttribute('title', t('aston_update_found', '发现新版本'));

        btn.innerHTML = 
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">' +
            '  <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>' +
            '</svg>' +
            '<span id="aston_update_dot" class="aston-update-dot"></span>' +
            '<svg id="aston_update_ring_svg" class="aston-update-ring" viewBox="0 0 36 36">' +
            '  <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="2.5"></circle>' +
            '  <circle id="aston_ring_fill" cx="18" cy="18" r="15" fill="none" stroke="#ffaa00" stroke-width="2.5" stroke-dasharray="94.25" stroke-dashoffset="94.25" stroke-linecap="round" style="transition: stroke-dashoffset 0.15s linear;"></circle>' +
            '</svg>';

        var searchBtn = targetHeader.querySelector('.open--search');
        if (searchBtn) {
            targetHeader.insertBefore(btn, searchBtn);
        } else {
            targetHeader.insertBefore(btn, targetHeader.firstChild);
        }

        var isClicking = false;
        var onTrigger = function (e) {
            if (e && e.preventDefault) e.preventDefault();
            if (e && e.stopPropagation) e.stopPropagation();
            if (isClicking) return;
            isClicking = true;
            setTimeout(function () { isClicking = false; }, 500);

            setTimeout(function () {
                showUpdateDialog(info, dlUrl, showVer);
            }, 150);
        };

        // 核心修复：监听 Lampa 原生遥控器 hover:focus / hover:blur 事件切换选中态
        if (window.$) {
            $(btn)
                .on('hover:enter click', onTrigger)
                .on('hover:focus', function () {
                    $(this).addClass('focus');
                })
                .on('hover:blur', function () {
                    $(this).removeClass('focus');
                });
        } else {
            btn.onclick = onTrigger;
            btn.onfocus = function () { btn.classList.add('focus'); };
            btn.onblur = function () { btn.classList.remove('focus'); };
        }
    }

    // ================= 8. 在线检测更新核心 =================
    function checkUpdate() {
        var curL = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'ru';
        var isZh = (curL === 'zh');
        var repo = getRepoPath();
        var currentBuild = getBuildCode();

        var checkUrl = isZh 
            ? 'https://ghfast.top/https://raw.githubusercontent.com/' + repo + '/main/version.json?t=' + Date.now()
            : 'https://raw.githubusercontent.com/' + repo + '/main/version.json?t=' + Date.now();

        var xhr = new XMLHttpRequest();
        xhr.open('GET', checkUrl, true);
        xhr.timeout = 10000;
        xhr.onload = function () {
            if (xhr.status === 200) {
                try {
                    var info = JSON.parse(xhr.responseText);
                    if (info.versionCode > currentBuild) {
                        var dlUrl = isZh ? (info.mirror_url || info.direct_url) : (info.direct_url || info.mirror_url);
                        var showVer = info.versionName || info.version || ('Build ' + info.versionCode);
                        renderHeaderUpdateBadge(info, dlUrl, showVer);
                    }
                } catch (e) {
                    console.warn('[AstonUpdate] 解析 version.json 异常:', e);
                }
            }
        };
        xhr.onerror = function (err) {
            console.warn('[AstonUpdate] 检测更新网络错误:', err);
        };
        xhr.ontimeout = function () {
            console.warn('[AstonUpdate] 检测更新连接超时 (10s)');
        };
        xhr.send();
    }

    // ================= 9. 全局按键监听（修复输入框/搜索框按 R 劫持 Bug） =================
    window.addEventListener('keydown', function (e) {
        var code = e.keyCode || e.which;

        // 核心修复：在输入框打字、输入网址时，绝不劫持按键（避免字母 R 被捕获）
        var tag = (e.target && e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || (e.target && e.target.isContentEditable)) {
            return;
        }

        // 仅在非输入场景下拦截遥控器 Menu/设置键：0(底层键), 82(Menu键), 93(上下文菜单键)
        if (code === 0 || code === 82 || code === 93) {
            e.preventDefault();
            e.stopPropagation();
            triggerAstonQuickMenu();
        }
    }, true);

    document.addEventListener('menubutton', function () {
        triggerAstonQuickMenu();
    }, false);

    // ================= 10. 双重检查启动引擎（彻底消除事件错过的竞态隐患） =================
    function startEngine() {
        injectStyles();
        initAstonI18n();

        var hasChecked = false;
        function doCheckOnce() {
            if (hasChecked) return;
            hasChecked = true;
            setTimeout(checkUpdate, 1000);
        }

        // 判定 1：若顶栏节点早已渲染完成，立即执行
        if (document.querySelector('.head__actions') || document.querySelector('.head')) {
            doCheckOnce();
            return;
        }

        // 判定 2：若顶栏未出，挂载 Lampa 生命周期监听
        if (window.Lampa && Lampa.Listener) {
            Lampa.Listener.follow('app', function (e) {
                if (e.type === 'ready') doCheckOnce();
            });
        }

        // 判定 3：轮询兜底，抓到节点立即触发，30秒后自动销毁定时器
        var pollTimer = setInterval(function () {
            if (document.querySelector('.head__actions') || document.querySelector('.head')) {
                clearInterval(pollTimer);
                doCheckOnce();
            }
        }, 500);

        setTimeout(function () { clearInterval(pollTimer); }, 30000);
    }

    if (window.Lampa) {
        startEngine();
    } else {
        document.addEventListener('DOMContentLoaded', startEngine);
    }
})();
