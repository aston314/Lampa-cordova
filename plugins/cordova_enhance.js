(function () {
    'use strict';

    // ================= 0. 单例保护 =================
    if (window._aston_update_inited) {
        return;
    }
    window._aston_update_inited = true;

    function getBuildCode() {
        return window.CURRENT_BUILD_CODE || 1;
    }

    function getRepoPath() {
        return window.CURRENT_REPO || 'owner/repo';
    }

    // ================= 0.1 纯 ES5 SHA-256 算法 =================
    function sha256ArrayBuffer(arrayBuffer) {
        var K = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        ];
        var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];

        function rightRotate(value, amount) {
            return (value >>> amount) | (value << (32 - amount));
        }

        var bytes = new Uint8Array(arrayBuffer);
        var origLen = bytes.length;
        var bitLenLow = (origLen * 8) >>> 0;
        var bitLenHigh = Math.floor(origLen / 0x20000000);

        var totalLen = Math.ceil((origLen + 9) / 64) * 64;
        var padded = new Uint8Array(totalLen);
        padded.set(bytes);
        padded[origLen] = 0x80;

        var end = totalLen;
        padded[end - 1] = bitLenLow & 0xff;
        padded[end - 2] = (bitLenLow >>> 8) & 0xff;
        padded[end - 3] = (bitLenLow >>> 16) & 0xff;
        padded[end - 4] = (bitLenLow >>> 24) & 0xff;
        padded[end - 5] = bitLenHigh & 0xff;
        padded[end - 6] = (bitLenHigh >>> 8) & 0xff;
        padded[end - 7] = (bitLenHigh >>> 16) & 0xff;
        padded[end - 8] = (bitLenHigh >>> 24) & 0xff;

        var view = new DataView(padded.buffer);
        var w = new Array(64);
        var chunkStart, i;

        for (chunkStart = 0; chunkStart < totalLen; chunkStart += 64) {
            for (i = 0; i < 16; i++) {
                w[i] = view.getUint32(chunkStart + i * 4, false);
            }
            for (i = 16; i < 64; i++) {
                var s0 = rightRotate(w[i - 15], 7) ^ rightRotate(w[i - 15], 18) ^ (w[i - 15] >>> 3);
                var s1 = rightRotate(w[i - 2], 17) ^ rightRotate(w[i - 2], 19) ^ (w[i - 2] >>> 10);
                w[i] = (w[i - 16] + s0 + w[i - 7] + s1) | 0;
            }

            var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];

            for (i = 0; i < 64; i++) {
                var S1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
                var ch = (e & f) ^ (~e & g);
                var temp1 = (h + S1 + ch + K[i] + w[i]) | 0;
                var S0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
                var maj = (a & b) ^ (a & c) ^ (b & c);
                var temp2 = (S0 + maj) | 0;

                h = g;
                g = f;
                f = e;
                e = (d + temp1) | 0;
                d = c;
                c = b;
                b = a;
                a = (temp1 + temp2) | 0;
            }

            H[0] = (H[0] + a) | 0;
            H[1] = (H[1] + b) | 0;
            H[2] = (H[2] + c) | 0;
            H[3] = (H[3] + d) | 0;
            H[4] = (H[4] + e) | 0;
            H[5] = (H[5] + f) | 0;
            H[6] = (H[6] + g) | 0;
            H[7] = (H[7] + h) | 0;
        }

        var hex = '';
        for (i = 0; i < 8; i++) {
            hex += ('00000000' + (H[i] >>> 0).toString(16)).slice(-8);
        }
        return hex;
    }

    function computeBlobSha256(blob, callback) {
        var reader = new FileReader();
        reader.onload = function () {
            var buffer = reader.result;
            if (window.crypto && crypto.subtle && typeof crypto.subtle.digest === 'function') {
                try {
                    crypto.subtle.digest('SHA-256', buffer).then(function (hashBuf) {
                        var hashArr = Array.from(new Uint8Array(hashBuf));
                        var hex = hashArr.map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
                        callback(null, hex);
                    }).catch(function () {
                        callback(null, sha256ArrayBuffer(buffer));
                    });
                    return;
                } catch (e) {}
            }
            try {
                callback(null, sha256ArrayBuffer(buffer));
            } catch (e) {
                callback(e, null);
            }
        };
        reader.onerror = function () {
            callback(reader.error || new Error('FileReader error'), null);
        };
        reader.readAsArrayBuffer(blob);
    }

    // ================= 1. 样式注入 =================
    function injectStyles() {
        if (document.getElementById('aston-update-style')) return;
        var style = document.createElement('style');
        style.id = 'aston-update-style';
        style.type = 'text/css';
        style.innerHTML =
            '.head__action.aston-update-action { position: relative; display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; }' +
            '.aston-update-dot { position: absolute; top: 4px; right: 4px; width: 8px; height: 8px; background: #ff3b30; border-radius: 50%; box-shadow: 0 0 6px #ff3b30; pointer-events: none; }' +
            '.aston-update-ring { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform: rotate(-90deg); display: none; pointer-events: none; }' +
            '.head__action.aston-update-action.focus, .head__action.aston-update-action:hover, .head__action.aston-update-action:focus { background: #fff !important; color: #000 !important; border-radius: 50%; outline: none; }';
        document.head.appendChild(style);
    }

    // ================= 2. 12 国全语言字典 =================
    function initAstonI18n() {
        if (window._aston_full_lang_inited || !window.Lampa || !Lampa.Lang) return;
        Lampa.Lang.add({
            aston_menu_title: { zh: '快捷菜单', en: 'Quick Menu', ru: 'Быстрое меню', uk: 'Швидке меню', be: 'Хуткае меню', bg: 'Бързо меню', cs: 'Rychlé menu', fr: 'Menu rapide', he: 'תפריט מהיר', pl: 'Szybkie menu', pt: 'Menu rápido', ro: 'Meniu rapid' },
            aston_menu_player: { zh: '默认播放器', en: 'Default Player', ru: 'Плеер по умолчанию', uk: 'Плеєр за замовчуванням', be: 'Плэер па змаўчанні', bg: 'Плейър по подразбиране', cs: 'Výchozí přehrávač', fr: 'Lecteur par défaut', he: 'נגן ברירת מחדל', pl: 'Domyślny odtwarzacz', pt: 'Reprodutor padrão', ro: 'Player implicit' },
            aston_player_system: { zh: '系统选择 / 每次询问', en: 'System Chooser / Always ask', ru: 'Системный выбор / Спрашивать', uk: 'Системний вибір / Запитувати', be: 'Сістэмны выбар / Пытацца', bg: 'Избор от системата / Винаги питай', cs: 'Systémový výběr / Vždy se ptát', fr: 'Sélecteur système / Toujours demander', he: 'בורר המערכת / שאל תמיד', pl: 'Wybór systemowy / Zawsze pytaj', pt: 'Seletor do sistema / Sempre perguntar', ro: 'Selector de sistem / Întreabă mereu' },
            aston_player_set_done: { zh: '已设置默认播放器', en: 'Default player set to', ru: 'Плеер установлен', uk: 'Плеєр встановлено', be: 'Плэер усталяваны', bg: 'Плейърът е зададен', cs: 'Výchozí přehrávač nastaven', fr: 'Lecteur par défaut défini sur', he: 'נגן ברירת מחדל הוגדר', pl: 'Ustawiono domyślny odtwarzacz', pt: 'Reprodutor padrão definido', ro: 'Player implicit setat' },
            aston_menu_reload: { zh: '重新加载', en: 'Reload', ru: 'Перезагрузить', uk: 'Перезавантажити', be: 'Перазагрузіць', bg: 'Презареждане', cs: 'Znovu načíst', fr: 'Recharger', he: 'טעינה מחדש', pl: 'Przeładuj', pt: 'Recarregar', ro: 'Reîncărcare' },
            aston_menu_reload_descr: { zh: '刷新当前界面与数据', en: 'Refresh interface and data', ru: 'Обновить интерфейс и данные', uk: 'Оновити інтерфейс та дані', be: 'Абнавіць інтэрфейс і дадзеныя', bg: 'Опресняване на интерфейса и данните', cs: 'Obnovit rozhraní a data', fr: "Actualiser l'interface et les données", he: 'רענון הממשק והנתונים', pl: 'Odśwież interfejs i dane', pt: 'Atualizar interface e dados', ro: 'Reîmprospătează interfața și datele' },
            aston_menu_exit: { zh: '退出应用', en: 'Exit', ru: 'Выход', uk: 'Вихід', be: 'Выхад', bg: 'Изход', cs: 'Ukončit', fr: 'Quitter', he: 'יציאה', pl: 'Wyjście', pt: 'Sair', ro: 'Ieșire' },
            aston_menu_exit_descr: { zh: '清理临时缓存并退出 Lampa', en: 'Clean cache and exit Lampa', ru: 'Очистить кэш и выйти из Lampa', uk: 'Очистити кеш та вийти з Lampa', be: 'Ачысціць кэш і выйсці з Lampa', bg: 'Изчистване на кеша и изход', cs: 'Vymazat mezipaměť a ukončit', fr: 'Vider le cache et quitter', he: 'ניקוי מטמון ויציאה מ-Lampa', pl: 'Wyczyść pamięć podręczną i wyjdź', pt: 'Limpar cache e sair', ro: 'Curăță memoria cache și ieși' },
            aston_update_found: { zh: '发现新版本', en: 'New Version Available', ru: 'Доступна новая версия', uk: 'Доступна нова версія', be: 'Даступная новая версія', bg: 'Налична е нова версия', cs: 'Nová verze k dispozici', fr: 'Nouvelle version disponible', he: 'גרסה חדשה זמינה', pl: 'Dostępna nowa wersja', pt: 'Nova versão disponível', ro: 'Versiune nouă disponibilă' },
            aston_update_now: { zh: '立即更新', en: 'Update Now', ru: 'Обновить', uk: 'Оновити', be: 'Абнавіць', bg: 'Обнови', cs: 'Aktualizovat', fr: 'Mettre à jour', he: 'עדכן עכשיו', pl: 'Aktualizuj', pt: 'Atualizar agora', ro: 'Actualizează acum' },
            aston_update_later: { zh: '稍后再说', en: 'Later', ru: 'Позже', uk: 'Пізніше', be: 'Пазней', bg: 'По-късно', cs: 'Později', fr: 'Plus tard', he: 'מאוחר יותר', pl: 'Później', pt: 'Mais tarde', ro: 'Mai târziu' },
            aston_update_start: { zh: '开始下载更新包...', en: 'Starting update download...', ru: 'Запуск загрузки обновления...', uk: 'Початок завантаження оновлення...', be: 'Пачатак загрузкі абнаўлення...', bg: 'Стартиране на изтеглянето...', cs: 'Zahájení stahování...', fr: 'Démarrage du téléchargement...', he: 'מתחיל להוריד עדכון...', pl: 'Rozpoczynanie pobierania...', pt: 'Iniciando download...', ro: 'Se începe descărcarea...' },
            aston_update_downloading: { zh: '正在下载', en: 'Downloading', ru: 'Загрузка', uk: 'Завантаження', be: 'Загрузка', bg: 'Изтегляне', cs: 'Stahování', fr: 'Téléchargement', he: 'מוריד', pl: 'Pobieranie', pt: 'Baixando', ro: 'Descărcare' },
            aston_update_verifying: { zh: '校验安装包完整性...', en: 'Verifying package integrity...', ru: 'Проверка целостности пакета...', uk: 'Перевірка цілісності пакета...', be: 'Праверка цэласнасці пакета...', bg: 'Проверка на целостта на пакета...', cs: 'Ověřování integrity balíčku...', fr: "Vérification de l'intégrité du paquet...", he: 'מאמת את שלמות החבילה...', pl: 'Weryfikacja integralności pakietu...', pt: 'Verificando integridade do pacote...', ro: 'Se verifică integritatea pachetului...' },
            aston_update_installing: { zh: '下载完成，正在唤起系统安装器...', en: 'Downloaded, opening installer...', ru: 'Загружено, запуск установщика...', uk: 'Завантажено, запуск інсталятора...', be: 'Загружана, запуск усталёўшчыка...', bg: 'Изтеглено, отваряне на инсталатора...', cs: 'Staženo, otevírání instalátoru...', fr: "Ouverture de l'installateur...", he: 'הורד, פותח מתקין...', pl: 'Pobrano, otwieranie instalatora...', pt: 'Baixado, abrindo instalador...', ro: 'Descărcat, deschidere instalator...' },
            aston_update_failed: { zh: '下载失败', en: 'Download failed', ru: 'Ошибка загрузки', uk: 'Помилка завантаження', be: 'Памылка загрузкі', bg: 'Грешка при изтегляне', cs: 'Stahování selhalo', fr: 'Échec du téléchargement', he: 'ההורדה נכשלה', pl: 'Pobieranie nie powiodło się', pt: 'Falha no download', ro: 'Descărcare eșuată' },
            aston_update_error: { zh: '下载出错，请检查网络连接', en: 'Download error, please check connection', ru: 'Ошибка загрузки, проверьте сеть', uk: 'Помилка завантаження, перевірте мережу', be: 'Памылка загрузкі, праверце сетку', bg: 'Грешка при изтегляне, проверете мрежата', cs: 'Chyba stahování, zkontrolujte síť', fr: 'Erreur de téléchargement, vérifiez le réseau', he: 'שגיאת הורדה, בדוק חיבור לרשת', pl: 'Błąd pobierania, sprawdź połączenie', pt: 'Erro no download, verifique a conexão', ro: 'Eroare de descărcare, verificați rețeaua' },
            aston_update_timeout: { zh: '下载超时，请重试', en: 'Download timed out, please retry', ru: 'Время загрузки истекло', uk: 'Час завантаження минув', be: 'Час загрузкі скончыўся', bg: 'Времето за изтегляне изтече', cs: 'Časový limit stahování vypršel', fr: 'Délai de téléchargement dépassé', he: 'זמן ההורדה תם', pl: 'Przekroczono limit czasu pobierania', pt: 'Tempo limite de download esgotado', ro: 'Timpul de descărcare a expirat' },
            aston_update_corrupt: {
                zh: '安装包校验失败（文件损坏或不完整），请重试',
                en: 'Package verification failed (corrupted or incomplete), please retry',
                ru: 'Проверка пакета не пройдена (файл повреждён), повторите попытку',
                uk: 'Перевірка пакета не пройдена (файл пошкоджено), повторіть спробу',
                be: 'Праверка пакета не пройдзена (файл пашкоджаны), паспрабуйце зноў',
                bg: 'Проверката на пакета е неуспешна (повреден файл), опитайте отново',
                cs: 'Ověření balíčku selhalo (poškozený soubor), zkuste to znovu',
                fr: "Échec de la vérification du paquet (fichier corrompu), veuillez réessayer",
                he: 'אימות החבילה נכשל (קובץ פגום), אנא נסה שוב',
                pl: 'Weryfikacja pakietu nie powiodła się (uszkodzony plik), spróbuj ponownie',
                pt: 'Falha na verificação do pacote (arquivo corrompido), tente novamente',
                ro: 'Verificarea pachetului a eșuat (fișier corupt), vă rugăm să reîncercați'
            },
            aston_update_sub: { zh: '在线极速下载并覆盖升级', en: 'Download and update online', ru: 'Онлайн загрузка и обновление', uk: 'Онлайн завантаження та оновлення', be: 'Анлайн загрузка і абнаўленне', bg: 'Онлайн изтегляне и обновяване', cs: 'Online stažení a aktualizace', fr: 'Télécharger et mettre à jour en ligne', he: 'הורד ועדכן באופן מקוון', pl: 'Pobierz i zaktualizuj online', pt: 'Baixar e atualizar online', ro: 'Descărcați și actualizați online' }
        });
        window._aston_full_lang_inited = true;
    }

    function t(key, fallback) {
        return (window.Lampa && Lampa.Lang && Lampa.Lang.translate(key)) || fallback;
    }

    // ================= 3. 缓存清理与退出 =================
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
                }, function () {
                    if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
                });
            }, function () {
                if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
            });
        } else {
            if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
        }
    }

    // ================= 4. 播放器选择菜单 =================
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

    var lastMenuTrigger = 0;
    function triggerAstonQuickMenuThrottled() {
        var now = Date.now();
        if (now - lastMenuTrigger < 800) return;
        lastMenuTrigger = now;
        triggerAstonQuickMenu();
    }

    // ================= 6. 极速下载 + 纯 Lampa.Loading 交互（彻底剔除 Noty） =================
    var isUpdating = false;

    function startUpdateDownload(downloadUrl, versionName, info) {
        if (isUpdating) return;
        isUpdating = true;

        var dot = document.getElementById('aston_update_dot');
        var ringSvg = document.getElementById('aston_update_ring_svg');
        var ringFill = document.getElementById('aston_ring_fill');

        // 彻底关掉 Loading 遮罩并复位
        function stopAndReset() {
            isUpdating = false;
            if (window.Lampa && Lampa.Loading) {
                Lampa.Loading.stop();
            }
            if (ringSvg) ringSvg.style.display = 'none';
            if (dot) dot.style.display = 'block';
        }

        // 错误处理：在 Loading 界面中央展示错误文字 2.5 秒，让用户看清，随后关闭复位，0 个 Noty！
        function showErrorAndStop(errorMsg) {
            if (window.Lampa && Lampa.Loading) {
                Lampa.Loading.setText(errorMsg);
                setTimeout(stopAndReset, 2500);
            } else {
                stopAndReset();
            }
        }

        if (dot) dot.style.display = 'none';
        if (ringSvg) ringSvg.style.display = 'block';
        if (ringFill) ringFill.style.strokeDashoffset = '94.25';

        // 启动 Loading 阻塞遮罩（首参传 false，按遥控器按键彻底静默不取消）
        if (window.Lampa && Lampa.Loading) {
            Lampa.Loading.start(false, t('aston_update_start', '开始下载更新包...'));
        }

        var xhr = new XMLHttpRequest();
        xhr.open('GET', downloadUrl, true);
        xhr.responseType = 'blob';
        xhr.timeout = 180000; // 3 分钟超时

        // 原位刷新下载进度
        xhr.onprogress = function (e) {
            if (e.lengthComputable) {
                var pct = Math.round((e.loaded / e.total) * 100);
                var loadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
                var totalMB = (e.total / (1024 * 1024)).toFixed(1);
                var progressText = t('aston_update_downloading', '正在下载') + ' ' + versionName + ': ' + pct + '% (' + loadedMB + '/' + totalMB + ' MB)';

                if (window.Lampa && Lampa.Loading) {
                    Lampa.Loading.setText(progressText);
                }
                if (ringFill) {
                    ringFill.style.strokeDashoffset = (94.25 * (1 - (pct / 100))).toFixed(2);
                }
            }
        };

        xhr.onload = function () {
            if (xhr.status !== 200) {
                showErrorAndStop(t('aston_update_failed', '下载失败') + ': ' + xhr.status);
                return;
            }

            var blob = xhr.response;

            // 仅进行 SHA-256 哈希校验
            if (info && info.sha256) {
                if (window.Lampa && Lampa.Loading) {
                    Lampa.Loading.setText(t('aston_update_verifying', '校验安装包完整性...'));
                }

                setTimeout(function () {
                    computeBlobSha256(blob, function (err, hex) {
                        if (err || (hex.toLowerCase() !== String(info.sha256).trim().toLowerCase())) {
                            showErrorAndStop(t('aston_update_corrupt', '安装包校验失败（文件损坏或不完整），请重试'));
                            return;
                        }
                        proceedToInstall(blob, downloadUrl, ringFill, stopAndReset, showErrorAndStop);
                    });
                }, 50);
            } else {
                proceedToInstall(blob, downloadUrl, ringFill, stopAndReset, showErrorAndStop);
            }
        };

        xhr.onerror = function () {
            showErrorAndStop(t('aston_update_error', '下载出错，请检查网络连接'));
        };

        xhr.ontimeout = function () {
            showErrorAndStop(t('aston_update_timeout', '下载超时，请重试'));
        };

        xhr.send();
    }

    function proceedToInstall(blob, downloadUrl, ringFill, stopAndReset, showErrorAndStop) {
        if (ringFill) ringFill.style.strokeDashoffset = '0';

        if (window.Lampa && Lampa.Loading) {
            Lampa.Loading.setText(t('aston_update_installing', '下载完成，正在唤起系统安装器...'));
        }

        var targetDir = (window.cordova && cordova.file && (cordova.file.externalCacheDirectory || cordova.file.cacheDirectory)) || '';
        if (!targetDir || !window.resolveLocalFileSystemURL) {
            stopAndReset();
            window.open(downloadUrl, '_system');
            return;
        }

        window.resolveLocalFileSystemURL(targetDir, function (dirEntry) {
            dirEntry.getFile('update.apk', { create: false }, function (oldFile) {
                oldFile.remove(function () {
                    writeNewApk(dirEntry, blob, downloadUrl, stopAndReset);
                }, function () {
                    writeNewApk(dirEntry, blob, downloadUrl, stopAndReset);
                });
            }, function () {
                writeNewApk(dirEntry, blob, downloadUrl, stopAndReset);
            });
        }, function () {
            stopAndReset();
            if (window.cordova && cordova.InAppBrowser) {
                cordova.InAppBrowser.open(downloadUrl, '_system');
            }
        });
    }

    function writeNewApk(dirEntry, blob, fallbackUrl, stopAndReset) {
        dirEntry.getFile('update.apk', { create: true, overwrite: true }, function (fileEntry) {
            fileEntry.createWriter(function (fileWriter) {
                fileWriter.onwriteend = function () {
                    var installUrl = fileEntry.nativeURL || fileEntry.toURL();

                    // 写入完成，在调起安装器的瞬间关掉 Loading 遮罩
                    if (window.Lampa && Lampa.Loading) {
                        Lampa.Loading.stop();
                    }

                    if (window.plugins && window.plugins.intentShim) {
                        window.plugins.intentShim.startActivity({
                            action: 'android.intent.action.VIEW',
                            url: installUrl,
                            type: 'application/vnd.android.package-archive',
                            flags: [268435456, 1]
                        }, function () {
                            stopAndReset();
                        }, function () {
                            stopAndReset();
                            if (window.cordova && cordova.InAppBrowser) {
                                cordova.InAppBrowser.open(fallbackUrl, '_system');
                            }
                        });
                    } else {
                        stopAndReset();
                        if (window.cordova && cordova.InAppBrowser) {
                            cordova.InAppBrowser.open(fallbackUrl, '_system');
                        } else {
                            window.open(fallbackUrl, '_system');
                        }
                    }
                };
                fileWriter.onerror = function () {
                    stopAndReset();
                    if (window.cordova && cordova.InAppBrowser) {
                        cordova.InAppBrowser.open(fallbackUrl, '_system');
                    }
                };
                fileWriter.write(blob);
            });
        }, function () {
            stopAndReset();
            if (window.cordova && cordova.InAppBrowser) {
                cordova.InAppBrowser.open(fallbackUrl, '_system');
            }
        });
    }

    // ================= 7. 升级提示对话框 =================
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
                        onSelect: function () {
                            startUpdateDownload(dlUrl, showVer, info);
                        }
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

    // ================= 8. 顶栏角标渲染 =================
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

    // ================= 9. 动态检查更新核心 =================
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
                } catch (e) {}
            }
        };
        xhr.send();
    }

    // ================= 10. 全局按键监听 =================
    window.addEventListener('keydown', function (e) {
        var code = e.keyCode || e.which;

        var tag = (e.target && e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || (e.target && e.target.isContentEditable)) {
            return;
        }

        if (code === 0 || code === 82 || code === 93) {
            e.preventDefault();
            e.stopPropagation();
            triggerAstonQuickMenuThrottled();
        }
    }, true);

    document.addEventListener('menubutton', function () {
        triggerAstonQuickMenuThrottled();
    }, false);

    // ================= 11. 双重检查启动引擎 =================
    function startEngine() {
        injectStyles();
        initAstonI18n();

        var hasChecked = false;
        function doCheckOnce() {
            if (hasChecked) return;
            hasChecked = true;
            setTimeout(checkUpdate, 1000);
        }

        if (document.querySelector('.head__actions') || document.querySelector('.head')) {
            doCheckOnce();
            return;
        }

        if (window.Lampa && Lampa.Listener) {
            Lampa.Listener.follow('app', function (e) {
                if (e.type === 'ready') doCheckOnce();
            });
        }

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
