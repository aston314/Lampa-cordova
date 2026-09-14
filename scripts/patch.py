import os
import sys
import re
import urllib.request
import urllib.parse

UPSTREAM_DIR = "upstream_code"

# 读取构建环境变量
REPO_NAME = os.environ.get("REPO_NAME", "your_user/your_repo").strip()
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


# ================= 1. 注入 index.html (Cordova + 语言分流在线更新 + 遥控器菜单) =================
html_file = os.path.join(UPSTREAM_DIR, "index.html")

if not os.path.exists(html_file):
    print(f"[FATAL ERROR] 找不到入口文件: {html_file}，打包终止！")
    send_ntfy_alert(["找不到入口文件 index.html"])
    sys.exit(1)

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

cordova_init_code = f"""
<script src="cordova.js"></script>
<style>
    /* Lampa 风格高颜值暗黑更新弹窗与渐变进度条 */
    .aston-update-mask {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(12px);
        display: flex; align-items: center; justify-content: center;
        z-index: 999999; font-family: sans-serif;
    }}
    .aston-update-box {{
        background: #18181c; width: 520px; max-width: 90%;
        border-radius: 16px; padding: 28px 32px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.9), 0 0 0 1px rgba(255,255,255,0.1);
        color: #fff; box-sizing: border-box; text-align: left;
    }}
    .aston-update-title {{
        font-size: 24px; font-weight: bold; margin-bottom: 8px; color: #fff;
    }}
    .aston-update-badge {{
        display: inline-block; background: #ffaa00; color: #000;
        font-size: 13px; font-weight: bold; padding: 3px 10px;
        border-radius: 6px; margin-bottom: 16px;
    }}
    .aston-update-desc {{
        font-size: 15px; color: #aaa; line-height: 1.6; margin-bottom: 24px;
    }}
    .aston-update-bar-bg {{
        height: 10px; background: rgba(255,255,255,0.12);
        border-radius: 5px; overflow: hidden; margin-bottom: 12px;
    }}
    .aston-update-bar-fill {{
        height: 100%; width: 0%;
        background: linear-gradient(90deg, #ffaa00, #ff5500);
        border-radius: 5px; transition: width 0.15s ease-out;
    }}
    .aston-update-status-row {{
        display: flex; justify-content: space-between;
        font-size: 14px; color: #888; margin-bottom: 20px;
    }}
    .aston-update-btn-row {{
        display: flex; justify-content: flex-end; gap: 14px;
    }}
    .aston-update-btn {{
        background: rgba(255,255,255,0.1); color: #fff; border: none;
        padding: 12px 24px; border-radius: 8px; font-size: 16px;
        font-weight: bold; cursor: pointer; transition: all 0.2s;
    }}
    .aston-update-btn.focus, .aston-update-btn:focus {{
        background: #ffaa00; color: #000; outline: none;
        transform: scale(1.05); box-shadow: 0 0 15px rgba(255,170,0,0.5);
    }}
</style>
<script>
    (function () {{
        window.CURRENT_BUILD_CODE = {BUILD_NUMBER};
        var REPO_PATH = "{REPO_NAME}";

        // --- 预装插件：自动注入 TMDB 代理插件 ---
        try {{
            var defaultPluginUrl = 'http://cub.red/plugin/tmdb-proxy';
            var savedPlugins = JSON.parse(localStorage.getItem('plugins') || '[]');
            var exists = savedPlugins.some(function (p) {{
                return (typeof p === 'string' && p === defaultPluginUrl) || (p && p.url === defaultPluginUrl);
            }});
            if (!exists) {{
                savedPlugins.push({{
                    url: defaultPluginUrl,
                    status: 1,
                    name: 'TMDB Proxy',
                    author: 'CUB'
                }});
                localStorage.setItem('plugins', JSON.stringify(savedPlugins));
            }}
        }} catch (e) {{}}

        // --- 高颜值应用内下载与安装 ---
        function startInAppUpdate(downloadUrl, versionName) {{
            var mask = document.createElement('div');
            mask.className = 'aston-update-mask';
            mask.innerHTML = 
                '<div class=\"aston-update-box\">' +
                '  <div class=\"aston-update-title\">' + (Lampa.Lang ? Lampa.Lang.translate('aston_update_downloading') : '正在下载更新') + '</div>' +
                '  <div class=\"aston-update-badge\">' + versionName + '</div>' +
                '  <div class=\"aston-update-bar-bg\"><div id=\"aston_bar\" class=\"aston-update-bar-fill\"></div></div>' +
                '  <div class=\"aston-update-status-row\">' +
                '    <span id=\"aston_loaded\">0 MB / 0 MB</span>' +
                '    <span id=\"aston_pct\" style=\"color:#ffaa00;font-weight:bold;\">0%</span>' +
                '  </div>' +
                '  <div class=\"aston-update-btn-row\">' +
                '    <button id=\"aston_cancel_btn\" class=\"aston-update-btn focus\">' + (Lampa.Lang ? Lampa.Lang.translate('aston_update_cancel') : '取消') + '</button>' +
                '  </div>' +
                '</div>';
            document.body.appendChild(mask);

            var cancelBtn = document.getElementById('aston_cancel_btn');
            cancelBtn.focus();

            var xhr = new XMLHttpRequest();
            xhr.open('GET', downloadUrl, true);
            xhr.responseType = 'blob';

            cancelBtn.onclick = function () {{
                xhr.abort();
                mask.remove();
                if (Lampa.Controller) Lampa.Controller.toggle('content');
            }};

            xhr.onprogress = function (e) {{
                if (e.lengthComputable) {{
                    var pct = Math.round((e.loaded / e.total) * 100);
                    var loadedMB = (e.loaded / (1024 * 1024)).toFixed(1);
                    var totalMB = (e.total / (1024 * 1024)).toFixed(1);
                    document.getElementById('aston_bar').style.width = pct + '%';
                    document.getElementById('aston_pct').innerText = pct + '%';
                    document.getElementById('aston_loaded').innerText = loadedMB + ' MB / ' + totalMB + ' MB';
                }}
            }};

            xhr.onload = function () {{
                if (xhr.status === 200) {{
                    document.getElementById('aston_loaded').innerText = (Lampa.Lang ? Lampa.Lang.translate('aston_update_installing') : '下载完成，正在打开安装器...');
                    var blob = xhr.response;

                    window.resolveLocalFileSystemURL(cordova.file.cacheDirectory, function (dirEntry) {{
                        dirEntry.getFile('update.apk', {{ create: true, overwrite: true }}, function (fileEntry) {{
                            fileEntry.createWriter(function (fileWriter) {{
                                fileWriter.onwriteend = function () {{
                                    mask.remove();
                                    window.plugins.intentShim.startActivity({{
                                        action: 'android.intent.action.VIEW',
                                        url: fileEntry.toURL(),
                                        type: 'application/vnd.android.package-archive',
                                        flags: [268435456, 1]
                                    }}, function () {{}}, function (err) {{
                                        cordova.InAppBrowser.open(downloadUrl, '_system');
                                    }});
                                }};
                                fileWriter.write(blob);
                            }});
                        }});
                    }});
                }} else {{
                    alert('下载失败，状态码: ' + xhr.status);
                    mask.remove();
                }}
            }};

            xhr.onerror = function () {{
                alert('网络连接失败，请检查网络');
                mask.remove();
            }};

            xhr.send();
        }}

        // --- 在线检测更新（包含中文自动加速、其他语言走官方直链） ---
        window.checkLampaUpdate = function (isManual) {{
            var checkUrl = 'https://cdn.jsdelivr.net/gh/' + REPO_PATH + '@main/version.json?t=' + new Date().getTime();
            
            var xhr = new XMLHttpRequest();
            xhr.open('GET', checkUrl, true);
            xhr.timeout = 8000;

            xhr.onload = function () {{
                if (xhr.status === 200) {{
                    try {{
                        var info = JSON.parse(xhr.responseText);
                        if (info.versionCode > window.CURRENT_BUILD_CODE) {{
                            // 关键逻辑：检测用户当前选择的语言
                            var currentLang = (window.Lampa && Lampa.Storage ? Lampa.Storage.get('language') : localStorage.getItem('language')) || 'ru';
                            var isChinese = (currentLang === 'zh');

                            // 中文用户优先走 mirror_url 加速，海外用户走 direct_url 官方直链
                            var finalDownloadUrl = isChinese ? (info.mirror_url || info.direct_url) : (info.direct_url || info.mirror_url);

                            var mask = document.createElement('div');
                            mask.className = 'aston-update-mask';
                            mask.innerHTML = 
                                '<div class=\"aston-update-box\">' +
                                '  <div class=\"aston-update-title\">' + (Lampa.Lang ? Lampa.Lang.translate('aston_update_found') : '发现新版本') + '</div>' +
                                '  <div class=\"aston-update-badge\">' + info.version + ' (Build ' + info.versionCode + ')</div>' +
                                '  <div class=\"aston-update-desc\">' + (info.description || '已同步上游源码，修复细节并优化性能，建议更新。') + '</div>' +
                                '  <div class=\"aston-update-btn-row\">' +
                                '    <button id=\"aston_later\" class=\"aston-update-btn\">' + (Lampa.Lang ? Lampa.Lang.translate('aston_update_later') : '稍后再说') + '</button>' +
                                '    <button id=\"aston_now\" class=\"aston-update-btn focus\">' + (Lampa.Lang ? Lampa.Lang.translate('aston_update_now') : '立即更新') + '</button>' +
                                '  </div>' +
                                '</div>';
                            document.body.appendChild(mask);

                            var btnNow = document.getElementById('aston_now');
                            var btnLater = document.getElementById('aston_later');
                            btnNow.focus();

                            btnNow.onkeydown = function(e) {{
                                if (e.keyCode === 37) btnLater.focus();
                            }};
                            btnLater.onkeydown = function(e) {{
                                if (e.keyCode === 39) btnNow.focus();
                            }};

                            btnNow.onclick = function () {{
                                mask.remove();
                                startInAppUpdate(finalDownloadUrl, info.version);
                            }};

                            btnLater.onclick = function () {{
                                mask.remove();
                                if (Lampa.Controller) Lampa.Controller.toggle('content');
                            }};
                        }} else {{
                            if (isManual && window.Lampa && Lampa.Noty) {{
                                Lampa.Noty.show(Lampa.Lang.translate('aston_update_latest'));
                            }}
                        }}
                    }} catch (e) {{}}
                }}
            }};

            xhr.onerror = function () {{
                if (isManual && window.Lampa && Lampa.Noty) {{
                    Lampa.Noty.show('无法连接到更新服务器');
                }}
            }};

            xhr.send();
        }};

        // --- 安全清理 WebView 缓存后退出 ---
        function cleanCacheAndExit() {{
            if (window.resolveLocalFileSystemURL && window.cordova && cordova.file && cordova.file.cacheDirectory) {{
                window.resolveLocalFileSystemURL(cordova.file.cacheDirectory, function (dirEntry) {{
                    var reader = dirEntry.createReader();
                    reader.readEntries(function (entries) {{
                        var total = entries.length;
                        if (total === 0) {{
                            if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
                            return;
                        }}
                        var done = 0;
                        var onFinish = function () {{
                            done++;
                            if (done >= total && navigator.app && navigator.app.exitApp) {{
                                navigator.app.exitApp();
                            }}
                        }};
                        entries.forEach(function (entry) {{
                            if (entry.isDirectory) {{
                                entry.removeRecursively(onFinish, onFinish);
                            }} else {{
                                entry.remove(onFinish, onFinish);
                            }}
                        }});
                    }}, function () {{
                        if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
                    }});
                }}, function () {{
                    if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
                }});
            }} else {{
                if (navigator.app && navigator.app.exitApp) navigator.app.exitApp();
            }}
        }}

        // --- 遥控器设置键快捷菜单（12 种全语言自动适配） ---
        function triggerAstonQuickMenu() {{
            if (window.Lampa && Lampa.Player && Lampa.Player.opened && Lampa.Player.opened()) {{
                return;
            }}

            if (window.Lampa && Lampa.Select && Lampa.Lang) {{
                if (!window._aston_menu_lang_inited) {{
                    Lampa.Lang.add({{
                        aston_menu_title: {{
                            zh: '快捷菜单', en: 'Quick Menu', ru: 'Быстрое меню', uk: 'Швидке меню',
                            be: 'Хуткае меню', bg: 'Бързо меню', cs: 'Rychlé menu', fr: 'Menu rapide',
                            he: 'תפריט מהיר', pl: 'Szybkie menu', pt: 'Menu rápido', ro: 'Meniu rapid'
                        }},
                        aston_menu_check_update: {{
                            zh: '检查更新', en: 'Check for Updates', ru: 'Проверить обновления', uk: 'Перевірити оновлення',
                            be: 'Праверыць абнаўленні', bg: 'Проверка за актуализации', cs: 'Zkontrolovat aktualizace', fr: 'Vérifier les mises à jour',
                            he: 'בדוק עדכונים', pl: 'Sprawdź aktualizacje', pt: 'Verificar atualizações', ro: 'Verifică actualizări'
                        }},
                        aston_menu_check_update_descr: {{
                            zh: '在线检查是否有新版本 APK', en: 'Check for latest APK online', ru: 'Проверить наличие нового APK', uk: 'Перевірити новий APK',
                            be: 'Праверыць новы APK анлайн', bg: 'Онлайн проверка за нов APK', cs: 'Zkontrolovat novou verzi online', fr: 'Vérifier la dernière version',
                            he: 'בדוק גרסה חדשה ברשת', pl: 'Sprawdź nową wersję online', pt: 'Verificar nova versão online', ro: 'Verifică versiunea nouă online'
                        }},
                        aston_menu_reload: {{
                            zh: '重新加载', en: 'Reload', ru: 'Перезагрузить', uk: 'Перезавантажити',
                            be: 'Перазагрузіць', bg: 'Презареждане', cs: 'Znovu načíst', fr: 'Recharger',
                            he: 'טעינה מחדש', pl: 'Przeładuj', pt: 'Recarregar', ro: 'Reîncărcare'
                        }},
                        aston_menu_reload_descr: {{
                            zh: '刷新当前界面与数据', en: 'Refresh interface and data', ru: 'Обновить интерфейс и данные', uk: 'Оновити інтерфейс та дані',
                            be: 'Абнавіць інтэрфейс і дадзеныя', bg: 'Опресняване на интерфейса и данните', cs: 'Obnovit rozhraní a data', fr: 'Actualiser l\'interface et les données',
                            he: 'רענון הממשק והנתונים', pl: 'Odśwież interfejs i dane', pt: 'Atualizar interface e dados', ro: 'Reîmprospătează interfața și datele'
                        }},
                        aston_menu_exit: {{
                            zh: '退出应用', en: 'Exit', ru: 'Выход', uk: 'Вихід',
                            be: 'Выхад', bg: 'Изход', cs: 'Ukončit', fr: 'Quitter',
                            he: 'יציאה', pl: 'Wyjście', pt: 'Sair', ro: 'Ieșire'
                        }},
                        aston_menu_exit_descr: {{
                            zh: '清理临时缓存并退出 Lampa', en: 'Clean cache and exit Lampa', ru: 'Очистить кэш и выйти из Lampa', uk: 'Очистити кеш та вийти з Lampa',
                            be: 'Ачысціць кэш і выйсці з Lampa', bg: 'Изчистване на кеша и изход', cs: 'Vymazat mezipaměť a ukončit', fr: 'Vider le cache et quitter',
                            he: 'ניקוי מטמון ויציאה מ-Lampa', pl: 'Wyczyść pamięć podręczną i wyjdź', pt: 'Limpar cache e sair', ro: 'Curăță memoria cache și ieși'
                        }},
                        aston_update_found: {{ zh: '发现新版本', en: 'New Version Available', ru: 'Доступна новая версия', uk: 'Доступна нова версія', be: 'Даступная новая версія', bg: 'Налична е нова версия', cs: 'Nová verze k dispozici', fr: 'Nouvelle version disponible', he: 'גרסה חדשה זמינה', pl: 'Dostępna nowa wersja', pt: 'Nova versão disponível', ro: 'Versiune nouă disponibilă' }},
                        aston_update_now: {{ zh: '立即更新', en: 'Update Now', ru: 'Обновить', uk: 'Оновити', be: 'Абнавіць', bg: 'Обнови', cs: 'Aktualizovat', fr: 'Mettre à jour', he: 'עדכן עכשיו', pl: 'Aktualizuj', pt: 'Atualizar agora', ro: 'Actualizează acum' }},
                        aston_update_later: {{ zh: '稍后再说', en: 'Later', ru: 'Позже', uk: 'Пізніше', be: 'Пазней', bg: 'По-късно', cs: 'Později', fr: 'Plus tard', he: 'מאוחר יותר', pl: 'Później', pt: 'Mais tarde', ro: 'Mai târziu' }},
                        aston_update_downloading: {{ zh: '正在下载更新', en: 'Downloading Update', ru: 'Загрузка обновления', uk: 'Завантаження оновлення', be: 'Загрузка абнаўлення', bg: 'Изтегляне на актуализацията', cs: 'Stahování aktualizace', fr: 'Téléchargement de la mise à jour', he: 'מוריד עדכון', pl: 'Pobieranie aktualizacji', pt: 'Baixando atualização', ro: 'Descărcare actualizare' }},
                        aston_update_installing: {{ zh: '下载完成，正在打开安装器...', en: 'Downloaded, opening installer...', ru: 'Загружено, запуск установщика...', uk: 'Завантажено, запуск інсталятора...', be: 'Загружана, запуск усталёўшчыка...', bg: 'Изтеглено, стартиране на инсталатора...', cs: 'Staženo, otevírání instalátoru...', fr: 'Téléchargé, ouverture du programme d\'installation...', he: 'הורד, פותח מתקין...', pl: 'Pobrano, otwieranie instalatora...', pt: 'Baixado, abrindo instalador...', ro: 'Descărcat, se deschide programul de instalare...' }},
                        aston_update_cancel: {{ zh: '取消', en: 'Cancel', ru: 'Отмена', uk: 'Скасувати', be: 'Адмена', bg: 'Отказ', cs: 'Zrušit', fr: 'Annuler', he: 'ביטול', pl: 'Anuluj', pt: 'Cancelar', ro: 'Anulare' }},
                        aston_update_latest: {{ zh: '已经是最新版本', en: 'Already up to date', ru: 'Уже последняя версия', uk: 'Вже остання версія', be: 'Ужо апошняя версія', bg: 'Вече е най-новата версия', cs: 'Již máte nejnovější verzi', fr: 'Déjà à jour', he: 'כבר הגרסה העדכנית ביותר', pl: 'Wersja jest aktualna', pt: 'Já está na versão mais recente', ro: 'Deja la cea mai recentă versiune' }}
                    }});
                    window._aston_menu_lang_inited = true;
                }}

                Lampa.Select.show({{
                    title: Lampa.Lang.translate('aston_menu_title'),
                    items: [
                        {{
                            title: Lampa.Lang.translate('aston_menu_check_update'),
                            subtitle: Lampa.Lang.translate('aston_menu_check_update_descr'),
                            onSelect: function () {{
                                window.checkLampaUpdate(true);
                            }}
                        }},
                        {{
                            title: Lampa.Lang.translate('aston_menu_reload'),
                            subtitle: Lampa.Lang.translate('aston_menu_reload_descr'),
                            onSelect: function () {{
                                window.location.reload();
                            }}
                        }},
                        {{
                            title: Lampa.Lang.translate('aston_menu_exit'),
                            subtitle: Lampa.Lang.translate('aston_menu_exit_descr'),
                            onSelect: function () {{
                                cleanCacheAndExit();
                            }}
                        }}
                    ],
                    onBack: function () {{
                        if (Lampa.Controller) {{
                            Lampa.Controller.toggle('content');
                        }}
                    }}
                }});
            }}
        }}

        // 监听遥控器按键：code === 0（设置键）及标准 82 / 93
        window.addEventListener('keydown', function (e) {{
            var code = e.keyCode || e.which;
            if (code === 0 || code === 82 || code === 93) {{
                e.preventDefault();
                e.stopPropagation();
                triggerAstonQuickMenu();
            }}
        }}, true);

        // Cordova 初始化后延时 3 秒开机静默检测一次更新
        document.addEventListener('deviceready', function () {{
            if (document.readyState === 'complete') {{
                if (navigator.splashscreen) navigator.splashscreen.hide();
            }} else {{
                window.addEventListener('load', function () {{
                    if (navigator.splashscreen) navigator.splashscreen.hide();
                }});
            }}

            document.addEventListener('menubutton', function (e) {{
                triggerAstonQuickMenu();
            }}, false);

            setTimeout(function () {{
                window.checkLampaUpdate(false);
            }}, 3000);
        }});
    }})();
</script>
"""

if "<head>" in html_content:
    html_content = html_content.replace("<head>", f"<head>\n{cordova_init_code}", 1)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[Success] index.html 成功注入双通道分流更新、预装插件与遥控器菜单脚本")
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

print("[Success] 所有 23 条规则校验 100% 通过，双通道更新与全功能补丁就绪！准许打包 APK。\n")
