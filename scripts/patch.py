import os
import sys
import re
import urllib.request
import urllib.parse

UPSTREAM_DIR = "upstream_code"

# 自动提取 GitHub 仓库名称（如 owner/repo）
def get_current_repo():
    repo = os.environ.get("REPO_NAME", "").strip()
    if repo and repo != "your_user/your_repo":
        return repo
    try:
        remote_url = os.popen("git remote get-url origin").read().strip()
        match = re.search(r"github\.com[:/]([^/]+/[^/.]+)", remote_url)
        if match:
            return match.group(1).replace(".git", "")
    except Exception:
        pass
    return "owner/repo"

REPO_NAME = get_current_repo()
BUILD_NUMBER = int(os.environ.get("BUILD_NUMBER", "1"))

# ================= 0. 发送 ntfy.sh 手机告警函数 =================
def send_ntfy_alert(failed_rule_names):
    ntfy_topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not ntfy_topic:
        print("[Info] 未配置 NTFY_TOPIC，跳过手机告警通知。")
        return

    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    action_url = f"https://github.com/{repo}/actions/runs/{run_id}" if run_id and repo else ""

    message = "上游 yumata/lampa 源码有更新，但以下规则未匹配成功，已自动终止打包：\n\n"
    for name in failed_rule_names:
        message += f"❌ {name}\n"
    message += "\n请点击此通知直达 GitHub Actions 查看详情并更新规则。"

    query_params = {
        "title": "⚠️ Lampa 源码规则熔断报警",
        "priority": "urgent",
        "tags": "warning,skull"
    }
    if action_url:
        query_params["click"] = action_url

    url = f"https://ntfy.sh/{ntfy_topic}?" + urllib.parse.urlencode(query_params)
    req = urllib.request.Request(url, data=message.encode("utf-8"))

    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"[Info] 🔔 已成功向 ntfy.sh/{ntfy_topic} 发送手机故障告警通知！")
    except Exception as e:
        print(f"[Warning] ntfy.sh 通知发送失败: {e}")


# ================= 1. 注入 index.html (防盗链 + 顶栏更新角标 + 遥控器菜单 + 缓存清理) =================
html_file = os.path.join(UPSTREAM_DIR, "index.html")

if not os.path.exists(html_file):
    print(f"[FATAL ERROR] 找不到入口文件: {html_file}，打包终止！")
    send_ntfy_alert(["找不到入口文件 index.html"])
    sys.exit(1)

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

cordova_init_template = r"""
<meta name="referrer" content="no-referrer" />
<script src="cordova.js"></script>
<style>
    /* 顶栏更新高亮小图标与红点角标 */
    .head__action.aston-update-action {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .aston-update-dot {
        position: absolute;
        top: 6px;
        right: 6px;
        width: 8px;
        height: 8px;
        background: #ff3b30;
        border-radius: 50%;
        box-shadow: 0 0 8px #ff3b30;
        pointer-events: none;
    }
    /* 遥控器选中顶栏图标时的金色辉光 */
    .head__action.aston-update-action.focus {
        background: rgba(255, 170, 0, 0.2) !important;
        border-radius: 50%;
        transform: scale(1.15);
    }
    .head__action.aston-update-action.focus svg {
        stroke: #ffaa00 !important;
    }
</style>
<script>
    (function () {
        window.CURRENT_BUILD_CODE = __BUILD_NUMBER__;
        var REPO_PATH = "__REPO_NAME__";

        // --- 预装插件：自动注入 TMDB 代理插件 ---
        try {
            var defaultPluginUrl = 'http://cub.red/plugin/tmdb-proxy';
            var savedPlugins = JSON.parse(localStorage.getItem('plugins') || '[]');
            var exists = savedPlugins.some(function (p) {
                return (typeof p === 'string' && p === defaultPluginUrl) || (p && p.url === defaultPluginUrl);
            });
            if (!exists) {
                savedPlugins.push({
                    url: defaultPluginUrl,
                    status: 1,
                    name: 'TMDB Proxy',
                    author: 'CUB'
                });
                localStorage.setItem('plugins', JSON.stringify(savedPlugins));
            }
        } catch (e) {}

        // --- 安全清理 WebView 缓存后退出 ---
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
                            if (entry.isDirectory) entry.removeRecursively(onFinish, onFinish);
                            else entry.remove(onFinish, onFinish);
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

        // --- 多语言取词函数 ---
        function t(key, fallback) {
            return (window.Lampa && Lampa.Lang && Lampa.Lang.translate(key)) || fallback;
        }

        // --- 深度修复安装包解析错误与外部存储路径 ---
        function startUpdateDownload(downloadUrl, versionName) {
            if (window.Lampa && Lampa.Noty) {
                Lampa.Noty.show(t('aston_update_start', '开始下载更新包...'));
            }

            var xhr = new XMLHttpRequest();
            xhr.open('GET', downloadUrl, true);
            xhr.responseType = 'blob';

            xhr.onprogress = function (e) {
                if (e.lengthComputable && window.Lampa && Lampa.Noty) {
                    var pct = Math.round((e.loaded / e.total) * 100);
                    var loadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
                    var totalMB = (e.total / (1024 * 1024)).toFixed(1);
                    Lampa.Noty.show(t('aston_update_downloading', '正在下载') + ' ' + versionName + ': ' + pct + '% (' + loadedMB + '/' + totalMB + ' MB)');
                }
            };

            xhr.onload = function () {
                if (xhr.status === 200) {
                    if (window.Lampa && Lampa.Noty) {
                        Lampa.Noty.show(t('aston_update_installing', '下载完成，正在唤起安装器...'));
                    }
                    var blob = xhr.response;
                    var targetDir = cordova.file.externalCacheDirectory || cordova.file.cacheDirectory;

                    window.resolveLocalFileSystemURL(targetDir, function (dirEntry) {
                        // 彻底粉碎删除旧文件，防止尾部碎片引发解析错误
                        dirEntry.getFile('update.apk', { create: false }, function (oldFile) {
                            oldFile.remove(function () {
                                writeNewApk(dirEntry, blob, downloadUrl);
                            }, function () {
                                writeNewApk(dirEntry, blob, downloadUrl);
                            });
                        }, function () {
                            writeNewApk(dirEntry, blob, downloadUrl);
                        });
                    });
                } else {
                    if (window.Lampa && Lampa.Noty) Lampa.Noty.show(t('aston_update_failed', '下载失败') + ': ' + xhr.status);
                }
            };

            function writeNewApk(dirEntry, blob, fallbackUrl) {
                dirEntry.getFile('update.apk', { create: true, overwrite: true }, function (fileEntry) {
                    fileEntry.createWriter(function (fileWriter) {
                        fileWriter.onwriteend = function () {
                            var installUrl = fileEntry.nativeURL || fileEntry.toURL();
                            window.plugins.intentShim.startActivity({
                                action: 'android.intent.action.VIEW',
                                url: installUrl,
                                type: 'application/vnd.android.package-archive',
                                flags: [268435456, 1]
                            }, function () {}, function (err) {
                                if (window.cordova && cordova.InAppBrowser) {
                                    cordova.InAppBrowser.open(fallbackUrl, '_system');
                                }
                            });
                        };
                        fileWriter.write(blob);
                    });
                });
            }

            xhr.onerror = function () {
                if (window.Lampa && Lampa.Noty) Lampa.Noty.show(t('aston_update_error', '下载出错，请检查网络连接'));
            };

            xhr.send();
        }

        // --- 注册 12 种全语言字典 ---
        function initAstonI18n() {
            if (window._aston_menu_lang_inited || !window.Lampa || !Lampa.Lang) return;
            Lampa.Lang.add({
                aston_menu_title: {
                    zh: '快捷菜单', en: 'Quick Menu', ru: 'Быстрое меню', uk: 'Швидке меню',
                    be: 'Хуткае меню', bg: 'Бързо меню', cs: 'Rychlé menu', fr: 'Menu rapide',
                    he: 'תפריט מהיר', pl: 'Szybkie menu', pt: 'Menu rápido', ro: 'Meniu rapid'
                },
                aston_menu_check_update: {
                    zh: '检查更新', en: 'Check for Updates', ru: 'Проверить обновления', uk: 'Перевірити оновлення',
                    be: 'Праверыць абнаўленні', bg: 'Проверка за актуализации', cs: 'Zkontrolovat aktualizace', fr: 'Vérifier les mises à jour',
                    he: 'בדוק עדכונים', pl: 'Sprawdź aktualizacje', pt: 'Verificar atualizações', ro: 'Verifică actualizări'
                },
                aston_menu_check_update_descr: {
                    zh: '在线检查是否有新版本 APK', en: 'Check for latest APK online', ru: 'Проверить наличие нового APK', uk: 'Перевірити новий APK',
                    be: 'Праверыць новы APK анлайн', bg: 'Онлайн проверка за нов APK', cs: 'Zkontrolovat novou verzi online', fr: 'Vérifier la dernière version',
                    he: 'בדוק גרסה חדשה ברשת', pl: 'Sprawdź nową wersję online', pt: 'Verificar nova versão online', ro: 'Verifică versiunea nouă online'
                },
                aston_menu_reload: {
                    zh: '重新加载', en: 'Reload', ru: 'Перезагрузить', uk: 'Перезавантажити',
                    be: 'Перазагрузіць', bg: 'Презареждане', cs: 'Znovu načíst', fr: 'Recharger',
                    he: 'טעינה מחדש', pl: 'Przeładuj', pt: 'Recarregar', ro: 'Reîncărcare'
                },
                aston_menu_reload_descr: {
                    zh: '刷新当前界面与数据', en: 'Refresh interface and data', ru: 'Обновить интерфейс и данные', uk: 'Оновити інтерфейс та дані',
                    be: 'Абнавіць інтэрфейс і дадзеныя', bg: 'Опресняване на интерфейса и данните', cs: 'Obnovit rozhraní a data', fr: "Actualiser l'interface et les données",
                    he: 'רענון הממשק והנתונים', pl: 'Odśwież interfejs i dane', pt: 'Atualizar interface e dados', ro: 'Reîmprospătează interfața și datele'
                },
                aston_menu_exit: {
                    zh: '退出应用', en: 'Exit', ru: 'Выход', uk: 'Вихід',
                    be: 'Выхад', bg: 'Изход', cs: 'Ukončit', fr: 'Quitter',
                    he: 'יציאה', pl: 'Wyjście', pt: 'Sair', ro: 'Ieșire'
                },
                aston_menu_exit_descr: {
                    zh: '清理临时缓存并退出 Lampa', en: 'Clean cache and exit Lampa', ru: 'Очистить кэш и выйти из Lampa', uk: 'Очистити кеш та вийти з Lampa',
                    be: 'Ачысціць кэш і выйсці з Lampa', bg: 'Изчистване на кеша и изход', cs: 'Vymazat mezipaměť a ukončit', fr: 'Vider le cache et quitter',
                    he: 'ניקוי מטמון ויציאה מ-Lampa', pl: 'Wyczyść pamięć podręczną i wyjdź', pt: 'Limpar cache e sair', ro: 'Curăță memoria cache și ieși'
                },
                aston_update_found: { zh: '发现新版本', en: 'New Version Available', ru: 'Доступна новая версия', uk: 'Доступна нова версія', be: 'Даступная новая версія', bg: 'Налична е нова версия', cs: 'Nová verze k dispozici', fr: 'Nouvelle version disponible', he: 'גרסה חדשה זמינה', pl: 'Dostępna nowa wersja', pt: 'Nova versão disponível', ro: 'Versiune nouă disponibilă' },
                aston_update_now: { zh: '立即更新', en: 'Update Now', ru: 'Обновить', uk: 'Оновити', be: 'Абнавіць', bg: 'Обнови', cs: 'Aktualizovat', fr: 'Mettre à jour', he: 'עדכן עכשיו', pl: 'Aktualizuj', pt: 'Atualizar agora', ro: 'Actualizează acum' },
                aston_update_later: { zh: '稍后再说', en: 'Later', ru: 'Позже', uk: 'Пізніше', be: 'Пазней', bg: 'По-късно', cs: 'Později', fr: 'Plus tard', he: 'מאוחר יותר', pl: 'Później', pt: 'Mais tarde', ro: 'Mai târziu' },
                aston_update_start: { zh: '开始下载更新包...', en: 'Starting update download...', ru: 'Запуск загрузки обновления...', uk: 'Початок завантаження оновлення...', be: 'Пачатак загрузкі абнаўлення...', bg: 'Стартиране на изтеглянето...', cs: 'Zahájení stahování...', fr: 'Démarrage du téléchargement...', he: 'מתחיל להוריד עדכון...', pl: 'Rozpoczynanie pobierania...', pt: 'Iniciando download...', ro: 'Se începe descărcarea...' },
                aston_update_downloading: { zh: '正在下载', en: 'Downloading', ru: 'Загрузка', uk: 'Завантаження', be: 'Загрузка', bg: 'Изтегляне', cs: 'Stahování', fr: 'Téléchargement', he: 'מוריד', pl: 'Pobieranie', pt: 'Baixando', ro: 'Descărcare' },
                aston_update_installing: { zh: '下载完成，正在唤起系统安装器...', en: 'Downloaded, opening installer...', ru: 'Загружено, запуск установщика...', uk: 'Завантажено, запуск інсталятора...', be: 'Загружана, запуск усталёўшчыка...', bg: 'Изтеглено, отваряне на инсталатора...', cs: 'Staženo, otevírání instalátoru...', fr: "Ouverture de l'installateur...", he: 'הורד, פותח מתקין...', pl: 'Pobrano, otwieranie instalatora...', pt: 'Baixado, abrindo instalador...', ro: 'Descărcat, deschidere instalator...' },
                aston_update_failed: { zh: '下载失败', en: 'Download failed', ru: 'Ошибка загрузки', uk: 'Помилка завантаження', be: 'Памылка загрузкі', bg: 'Грешка при изтегляне', cs: 'Stahování selhalo', fr: 'Échec du téléchargement', he: 'ההורדה נכשלה', pl: 'Pobieranie nie powiodło się', pt: 'Falha no download', ro: 'Descărcare eșuată' },
                aston_update_error: { zh: '下载出错，请检查网络连接', en: 'Download error, please check connection', ru: 'Ошибка загрузки, проверьте сеть', uk: 'Помилка завантаження, перевірте мережу', be: 'Памылка загрузкі, праверце сетку', bg: 'Грешка при изтегляне, проверете мрежата', cs: 'Chyba stahování, zkontrolujte síť', fr: 'Erreur de téléchargement, vérifiez le réseau', he: 'שגיאת הורדה, בדוק חיבור לרשת', pl: 'Błąd pobierania, sprawdź połączenie', pt: 'Erro no download, verifique a conexão', ro: 'Eroare de descărcare, verificați rețeaua' },
                aston_update_latest: { zh: '已经是最新版本', en: 'Already up to date', ru: 'Уже последняя версия', uk: 'Вже остання версія', be: 'Ужо апошняя версія', bg: 'Вече е най-новата версия', cs: 'Již máte nejnovější verzi', fr: 'Déjà à jour', he: 'כבר הגרסה העדכנית ביותר', pl: 'Wersja jest aktualna', pt: 'Já está na versão mais recente', ro: 'Deja la cea mai recentă versiune' },
                aston_update_checking: { zh: '正在检查更新，请稍候...', en: 'Checking for updates, please wait...', ru: 'Проверка обновлений...', uk: 'Перевірка оновлень...', be: 'Праверка абнаўленняў...', bg: 'Проверка за актуализации...', cs: 'Kontrola aktualizací...', fr: 'Vérification des mises à jour...', he: 'בודק עדכונים...', pl: 'Sprawdzanie aktualizacji...', pt: 'Verificando atualizações...', ro: 'Se verifică actualizările...' },
                aston_update_sub: { zh: '在线极速下载并覆盖升级', en: 'Download and update online', ru: 'Онлайн загрузка и обновление', uk: 'Онлайн завантаження та оновлення', be: 'Анлайн загрузка і абнаўленне', bg: 'Онлайн изтегляне и обновяване', cs: 'Online stažení a aktualizace', fr: 'Télécharger et mettre à jour en ligne', he: 'הורד ועדכן באופן מקוון', pl: 'Pobierz i zaktualizuj online', pt: 'Baixar e atualizar online', ro: 'Descărcați și actualizați online' }
            });
            window._aston_menu_lang_inited = true;
        }

        // --- 弹出版本详情与确认升级对话框 ---
        function showUpdateDialog(info, dlUrl, showVer) {
            initAstonI18n();
            if (window.Lampa && Lampa.Select) {
                Lampa.Select.show({
                    title: t('aston_update_found', '发现新版本') + ' ' + showVer,
                    items: [
                        {
                            title: t('aston_update_now', '立即更新'),
                            subtitle: t('aston_update_sub', '在线极速下载并覆盖升级'),
                            onSelect: function () {
                                startUpdateDownload(dlUrl, showVer);
                            }
                        },
                        {
                            title: t('aston_update_later', '稍后再说'),
                            subtitle: '',
                            onSelect: function () {}
                        }
                    ],
                    onBack: function () {
                        if (Lampa.Controller) Lampa.Controller.toggle('head');
                    }
                });
            }
        }

        // --- 【核心创新】：在顶栏 Header 插入带红色角标的更新按钮 ---
        function renderHeaderUpdateBadge(info, dlUrl, showVer) {
            // 防止重复添加
            if (document.getElementById('aston_header_update_btn')) return;

            var targetHeader = document.querySelector('.head__actions') || document.querySelector('.head');
            if (!targetHeader) return;

            var btn = document.createElement('div');
            btn.id = 'aston_header_update_btn';
            btn.className = 'head__action selector aston-update-action';
            btn.setAttribute('tabindex', '0');
            btn.setAttribute('title', '发现新版本');

            // 绿色/黄色下载图标 + 右上角微光红点角标
            btn.innerHTML = 
                '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffaa00" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
                '  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>' +
                '  <polyline points="7 10 12 15 17 10"></polyline>' +
                '  <line x1="12" y1="15" x2="12" y2="3"></line>' +
                '</svg>' +
                '<span class="aston-update-dot"></span>';

            // 插入到顶栏动作区最前面
            targetHeader.insertBefore(btn, targetHeader.firstChild);

            // 遥控器按下确定 (hover:enter) 或鼠标点击时唤起弹窗
            var onTrigger = function (e) {
                if (e) { e.preventDefault(); e.stopPropagation(); }
                showUpdateDialog(info, dlUrl, showVer);
            };

            btn.onclick = onTrigger;
            btn.onkeydown = function (e) {
                if (e.keyCode === 13) onTrigger(e); // 遥控器 OK 键
            };

            console.log('[Update] 已成功在顶栏 Header 挂载更新角标');
        }

        // --- 在线检测更新核心函数 ---
        function checkLampaUpdate(isManual) {
            initAstonI18n();
            var curL = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'ru';
            var isZh = (curL === 'zh');

            var checkUrl = isZh 
                ? 'https://ghfast.top/https://raw.githubusercontent.com/' + REPO_PATH + '/main/version.json?t=' + new Date().getTime()
                : 'https://raw.githubusercontent.com/' + REPO_PATH + '/main/version.json?t=' + new Date().getTime();

            if (isManual && window.Lampa && Lampa.Noty) {
                Lampa.Noty.show(t('aston_update_checking', '正在检查更新，请稍候...'));
            }

            var xhr = new XMLHttpRequest();
            xhr.open('GET', checkUrl, true);
            xhr.timeout = 10000;

            xhr.onload = function () {
                if (xhr.status === 200) {
                    try {
                        var info = JSON.parse(xhr.responseText);
                        if (info.versionCode > window.CURRENT_BUILD_CODE) {
                            var dlUrl = isZh ? (info.mirror_url || info.direct_url) : (info.direct_url || info.mirror_url);
                            var showVer = info.versionName || info.version || ('Build ' + info.versionCode);

                            if (isManual) {
                                // 手动按菜单时：直接弹窗
                                showUpdateDialog(info, dlUrl, showVer);
                            } else {
                                // 开机自动检测时：优雅挂载顶栏小角标，0 打扰用户！
                                renderHeaderUpdateBadge(info, dlUrl, showVer);
                            }
                        } else {
                            if (isManual && window.Lampa && Lampa.Noty) {
                                Lampa.Noty.show(t('aston_update_latest', '当前已经是最新版本') + ' (' + (info.versionName || ('Build ' + window.CURRENT_BUILD_CODE)) + ')');
                            }
                        }
                    } catch (e) {
                        if (isManual && window.Lampa && Lampa.Noty) Lampa.Noty.show('解析更新版本数据异常');
                    }
                } else {
                    if (isManual && window.Lampa && Lampa.Noty) Lampa.Noty.show('检查失败: 服务器响应 ' + xhr.status);
                }
            };

            xhr.onerror = function () {
                if (isManual && window.Lampa && Lampa.Noty) Lampa.Noty.show('连接更新服务器失败，请检查网络');
            };

            xhr.ontimeout = function () {
                if (isManual && window.Lampa && Lampa.Noty) Lampa.Noty.show('检查更新超时，请重试');
            };

            xhr.send();
        }

        // --- 弹出快捷操作菜单 ---
        function triggerAstonQuickMenu() {
            if (window.Lampa && Lampa.Player && Lampa.Player.opened && Lampa.Player.opened()) {
                return;
            }

            if (window.Lampa && Lampa.Select) {
                initAstonI18n();

                Lampa.Select.show({
                    title: t('aston_menu_title', '快捷菜单'),
                    items: [
                        {
                            title: t('aston_menu_check_update', '检查更新'),
                            subtitle: t('aston_menu_check_update_descr', '在线检查是否有新版本 APK'),
                            onSelect: function () {
                                checkLampaUpdate(true);
                            }
                        },
                        {
                            title: t('aston_menu_reload', '重新加载'),
                            subtitle: t('aston_menu_reload_descr', '刷新当前界面与数据'),
                            onSelect: function () {
                                window.location.reload();
                            }
                        },
                        {
                            title: t('aston_menu_exit', '退出应用'),
                            subtitle: t('aston_menu_exit_descr', '清理临时缓存并退出 Lampa'),
                            onSelect: function () {
                                cleanCacheAndExit();
                            }
                        }
                    ],
                    onBack: function () {
                        if (Lampa.Controller) {
                            Lampa.Controller.toggle('content');
                        }
                    }
                });
            }
        }

        // 监听遥控器设置键(0)及标准 82 / 93
        window.addEventListener('keydown', function (e) {
            var code = e.keyCode || e.which;
            if (code === 0 || code === 82 || code === 93) {
                e.preventDefault();
                e.stopPropagation();
                triggerAstonQuickMenu();
            }
        }, true);

        // Cordova 初始化后等待 Lampa 顶栏就绪，触发静默检测
        document.addEventListener('deviceready', function () {
            if (document.readyState === 'complete') {
                if (navigator.splashscreen) navigator.splashscreen.hide();
            } else {
                window.addEventListener('load', function () {
                    if (navigator.splashscreen) navigator.splashscreen.hide();
                });
            }

            if (window.StatusBar) {
                window.StatusBar.hide();
            }

            document.addEventListener('menubutton', function (e) {
                triggerAstonQuickMenu();
            }, false);

            // 智能侦测：当 Lampa 顶栏完全渲染好后，自动静默检测并挂载角标
            var checkHeaderTimer = setInterval(function () {
                if (document.querySelector('.head__actions') || document.querySelector('.head')) {
                    clearInterval(checkHeaderTimer);
                    setTimeout(function () {
                        checkLampaUpdate(false);
                    }, 1000);
                }
            }, 500);

            setTimeout(function () { clearInterval(checkHeaderTimer); }, 30000);
        });
    })();
</script>
"""

# 用精准替换注入变量
cordova_init_code = cordova_init_template.replace("__BUILD_NUMBER__", str(BUILD_NUMBER)).replace("__REPO_NAME__", REPO_NAME)

if "<head>" in html_content:
    html_content = html_content.replace("<head>", "<head>\n" + cordova_init_code, 1)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[Success] index.html 成功注入顶栏角标更新、防盗链与遥控器菜单")
else:
    print("[FATAL ERROR] index.html 中未找到 <head> 标签，打包终止！")
    send_ntfy_alert(["index.html 中未找到 <head> 标签"])
    sys.exit(1)


# ================= 2. 自动遍历并批量内嵌所有语言包 =================
lang_dir = os.path.join(UPSTREAM_DIR, "lang")
all_embedded_langs = {}

if os.path.exists(lang_dir):
    for filename in sorted(os.listdir(lang_dir)):
        if filename.endswith(".js") and filename != "meta.js":
            lang_code = filename[:-3]
            filepath = os.path.join(lang_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                
                clean_obj = re.sub(r"^\s*export\s+default\s*", "", raw_content).strip()
                if clean_obj.endswith(";"):
                    clean_obj = clean_obj[:-1]
                
                all_embedded_langs[lang_code] = clean_obj
                print(f"[Success] 发现并成功解析语言包: {filename} -> 代码: {lang_code}")
            except Exception as e:
                print(f"[Warning] 解析语言包 {filename} 失败: {e}")

lang_entries = []
for code, obj_str in all_embedded_langs.items():
    lang_entries.append(f'"{code}": {obj_str}')

embedded_langs_js = "{\n" + ",\n".join(lang_entries) + "\n}"

ALL_LANG_EMBEDDED_CODE = (
    "var embedded_langs = " + embedded_langs_js + ";\n"
    "    if (embedded_langs[code]) {\n"
    "      Lang.AddTranslation(code, embedded_langs[code]);\n"
    "      loadTask();\n"
    "    } else if (['ru', 'en'].indexOf(code) >= 0) loadTask();"
)


# ================= 3. 定义大段代码模板 =================

CORDOVA_HTTP_REQ_CODE = r"""if (!!window.cordova) {

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
          if (url.includes('ddys')) {
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

      } else {
        Android.httpReq(params, {
          complite: secuses,
          error: error
        });
      };"""

OPEN_YOUTUBE_CODE = r"""window.plugins.intentShim.startActivity({
          action : window.plugins.intentShim.ACTION_VIEW,
          url : link
        }, function() {
        }, function() {
          console.log("Failed to open Youtube URL via Android Intent");
        });"""

OPEN_TORRENT_MAGNET_CODE = r"""else {
        intentExtra = {
          action: "play",
          data: {
            lampa: true
          }
        }
        };
      window.plugins.intentShim.startActivity(
      {
          action: window.plugins.intentShim.ACTION_VIEW,
          url: magnet,
          extras: intentExtra
      },
      function() {},
      function() {console.log('Failed to open magnet URL via Android Intent')}
      );
      //AndroidJS.openTorrentLink(magnet, JSON.stringify(intentExtra));"""

OPEN_TORRENT_SERVER_CODE = r"""window.plugins.intentShim.startActivity(
        {
            action: window.plugins.intentShim.ACTION_VIEW,
            url: SERVER.object.MagnetUri || SERVER.object.Link,
            extras: intentExtra
        },
        function() {},
        function() {console.log('Failed to open magnet URL via Android Intent')}
        );
        //AndroidJS.openTorrentLink(SERVER.object.MagnetUri || SERVER.object.Link, JSON.stringify(intentExtra));"""

OPEN_PLAYER_INTENT_CODE = r"""//Android.openPlayer(data.url, data);
     //{
      var intentExtra = {
          title: data.title || data.path,
          position: parseInt((data.timeline ? data.timeline.time || -1 : -1) * 1000),
          return_result: true,
          sticky: false,
          from_start: false,
          forcename: data.title || data.path,
          startfrom: parseInt((data.timeline ? data.timeline.time || -1 : -1) * 1000),
          forcedirect: true,
          forceresume: true,
        };
        window.plugins.intentShim.startActivityForResult({
          action : window.plugins.intentShim.ACTION_VIEW,
          url : data.url,
          position: parseInt((data.timeline ? data.timeline.time || -1 : -1) * 1000),
          type : "video/*",
          extras: intentExtra
        }, function(itent) {
          var time, duration, percent;
          time = (itent.extras.position || itent.extras.extra_position) / 1000;
          duration = (itent.extras.duration || itent.extras.extra_duration) / 1000;
          (duration > 0) ? percent = parseInt(time * 100 / duration) : percent = 100;
          
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
          };
        }, function() {
          console.log("Failed to open video URL via Android Intent");
        });"""

VERSION_CODE_FALLBACK_CODE = r"""var versionCode;
        if (typeof AndroidJS !== 'undefined') {
            var current = AndroidJS.appVersion().split('-');
            versionCode = current.pop();
        } else {
            versionCode = 28;
        };"""


# ================= 4. 严格替换规则列表（共 23 项） =================
STRICT_RULES = [
    {
        "name": "退出代码替换 Android.exit()",
        "pattern": r"Android\.exit\(\)",
        "new": "!!window.cordova ? navigator.app.exitApp() : Android.exit()"
    },
    {
        "name": "退出代码替换 AndroidJS.exit()",
        "pattern": r"AndroidJS\.exit\(\)",
        "new": "!!window.cordova ? navigator.app.exitApp() : AndroidJS.exit()"
    },
    {
        "name": "禁用默认播放器清除 clearDefaultPlayer",
        "pattern": r"if\s*\(\s*checkVersion\(15\)\s*\)\s*AndroidJS\.clearDefaultPlayer\(\);",
        "new": "if (checkVersion(15)) !!window.cordova ? null : AndroidJS.clearDefaultPlayer();"
    },
    {
        "name": "禁用频道更新 updateChannel",
        "pattern": r"if\s*\(\s*checkVersion\(28\)\s*\)\s*AndroidJS\.updateChannel\(where\);",
        "new": "if (checkVersion(28)) !!window.cordova ? null : AndroidJS.updateChannel(where);"
    },
    {
        "name": "禁用语音启动 voiceStart",
        "pattern": r"if\s*\(\s*checkVersion\(25\)\s*\)\s*AndroidJS\.voiceStart\(\);",
        "new": "if (checkVersion(25)) !!window.cordova ? null : AndroidJS.voiceStart();"
    },
    {
        "name": "YouTube 外部 Intent 打开",
        "pattern": r"AndroidJS\.openYoutube\(\s*link\s*\);",
        "new": OPEN_YOUTUBE_CODE
    },
    {
        "name": "外部播放器 InAppBrowser 调起",
        "pattern": r"AndroidJS\.openPlayer\(\s*link\s*,\s*JSON\.stringify\(data\)\s*\);",
        "new": "!!window.cordova ? cordova.InAppBrowser.open(link, '_system') : AndroidJS.openPlayer(link, JSON.stringify(data));"
    },
    {
        "name": "磁力链接 Intent 调起 1",
        "pattern": r"AndroidJS\.openTorrentLink\(\s*magnet\s*,\s*JSON\.stringify\(intentExtra\)\s*\);",
        "new": OPEN_TORRENT_MAGNET_CODE
    },
    {
        "name": "磁力链接 Intent 调起 2",
        "pattern": r"AndroidJS\.openTorrentLink\(\s*SERVER\.object\.MagnetUri\s*\|\|\s*SERVER\.object\.Link\s*,\s*JSON\.stringify\(intentExtra\)\s*\);",
        "new": OPEN_TORRENT_SERVER_CODE
    },
    {
        "name": "外部播放器 Intent 调起与进度回传",
        "pattern": r"Android\.openPlayer\(\s*data\.url\s*,\s*data\s*\);",
        "new": OPEN_PLAYER_INTENT_CODE
    },
    {
        "name": "应用版本号伪装 3.3.3",
        "pattern": r"AndroidJS\.appVersion\(\);",
        "new": "(!!window.cordova ? '3.3.3' : AndroidJS.appVersion());"
    },
    {
        "name": "媒体标题匹配扩展 item.name",
        "pattern": r"if\s*\(\s*params\.original_title\s*==\s*item\.original_title\s*\|\|\s*params\.title\s*==\s*item\.title\s*\)\s*\{",
        "new": "if (params.original_title == item.original_title || params.title == item.title || params.original_title == item.name) {"
    },
    {
        "name": "重置 SERVER.movie 状态",
        "pattern": r"SERVER\.hash\s*=\s*hash;\s*if\s*\(movie\)\s*SERVER\.movie\s*=\s*movie;",
        "new": "SERVER.hash = hash;\n    SERVER.movie = \"\";\n    if (movie) SERVER.movie = movie;"
    },
    {
        "name": "海报播放 action: play 注入 1",
        "pattern": r"poster:\s*SERVER\.movie\.img,\s*media:\s*SERVER\.movie\.name\s*\?\s*'tv'\s*:\s*'movie',\s*data:\s*\{",
        "new": "poster: SERVER.movie.img,\n          media: SERVER.movie.name ? 'tv' : 'movie',\n          action: \"play\",\n          data: {"
    },
    {
        "name": "海报播放 action: play 注入 2",
        "pattern": r"poster:\s*SERVER\.object\.poster,\s*media:\s*SERVER\.movie\.name\s*\?\s*'tv'\s*:\s*'movie',\s*data:\s*\{",
        "new": "poster: SERVER.object.poster,\n        media: SERVER.movie.name ? 'tv' : 'movie',\n        action: \"play\",\n        data: {"
    },
    {
        "name": "允许在 Cordova 下激活 AndroidJS 平台逻辑分支",
        "pattern": r"if\s*\(\s*typeof AndroidJS !== 'undefined'\s*\)",
        "new": "if (typeof AndroidJS !== 'undefined' || !!window.cordova)"
    },
    {
        "name": "修复 AndroidJS.appVersion 崩溃并设置 versionCode=28 兜底",
        "pattern": r"var\s+current\s*=\s*AndroidJS\.appVersion\(\)\.split\('-'\);[\s\S]*?var\s+versionCode\s*=\s*current\.pop\(\);",
        "new": VERSION_CODE_FALLBACK_CODE
    },
    {
        "name": "平台集成标识 lampa -> integrate",
        "pattern": r"\},\s*'lampa'\);",
        "new": "}, 'integrate');"
    },
    {
        "name": "Cordova HTTP/Fetch 网络请求引擎大段注入（单例优化与规范Promise版）",
        "pattern": r"Android\.httpReq\(\s*params\s*,\s*\{\s*complite\s*:\s*secuses\s*,\s*error\s*:\s*error\s*\}\s*\);",
        "new": CORDOVA_HTTP_REQ_CODE
    },
    {
        "name": "修复 updateChannels 中 AndroidJS.saveBookmarks 语法崩溃",
        "pattern": r"typeof\s+AndroidJS\.saveBookmarks\s*!==\s*['\"]undefined['\"]",
        "new": "typeof AndroidJS !== 'undefined' && typeof AndroidJS.saveBookmarks !== 'undefined'"
    },
    {
        "name": "全语言包自动内嵌（全语言离线支持、0秒切换、彻底告别语法错误）",
        "pattern": r"if\s*\(\s*\['ru',\s*'en'\]\.indexOf\(code\)\s*>=\s*0\s*\)\s*loadTask\(\);",
        "new": ALL_LANG_EMBEDDED_CODE
    },
    {
        "name": "默认关闭屏保 screensaver",
        "pattern": r"trigger\(\s*['\"]screensaver['\"]\s*,\s*true\s*\);",
        "new": "trigger('screensaver', false);"
    },
    {
        "name": "强制本地加载 hls/dash/qrcode 核心解码库（免联网GitHub、秒开在线播放）",
        "pattern": r"return\s+window\.location\.protocol\s*==\s*['\"]file:['\"]\s*\|\|\s*window\.location\.href\.indexOf\(['\"]chrome-extension['\"]\)\s*>\s*-1\s*\?\s*object\$2\.github_lampa\s*\+\s*['\"]vender/['\"]\s*\+\s*lib\s*:\s*['\"]\./vender/['\"]\s*\+\s*lib;",
        "new": "return './vender/' + lib;"
    }
]

TARGET_FILES = [
    os.path.join(UPSTREAM_DIR, "index.html"),
    os.path.join(UPSTREAM_DIR, "app.min.js")
]

print("\n[Info] 开始进行严格代码替换与校验...")

file_data = {}
for file_path in TARGET_FILES:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            file_data[file_path] = f.read()

has_error = False
failed_rules = []

for rule in STRICT_RULES:
    rule_name = rule["name"]
    pattern = rule["pattern"]
    new_text = rule["new"]
    total_replaced = 0
    
    for file_path, content in file_data.items():
        new_content, count = re.subn(pattern, lambda m: new_text, content)
        if count > 0:
            file_data[file_path] = new_content
            total_replaced += count
            print(f"  -> 在 {os.path.basename(file_path)} 中成功匹配并替换了 {count} 处")

    if total_replaced == 0:
        print(f"❌ [VERIFY FAILED] 规则【{rule_name}】失败！未在代码中匹配到目标段落。\n   Pattern: {pattern}")
        has_error = True
        failed_rules.append(rule_name)
    else:
        print(f"✅ [VERIFY PASSED] 规则【{rule_name}】验证通过（共替换 {total_replaced} 处）\n")

if has_error:
    print("=" * 65)
    print("[FATAL ERROR] 存在未通过校验的替换规则，正在向手机发送报警通知...")
    send_ntfy_alert(failed_rules)
    print("[FATAL ERROR] 为保证 APK 可用性，工作流已主动终止！")
    print("=" * 65)
    sys.exit(1)

for file_path, content in file_data.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("[Success] 所有 23 条规则校验 100% 通过，顶栏角标更新与全套补丁就绪！准许打包 APK。\n")
