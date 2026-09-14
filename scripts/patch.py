import os
import sys
import re
import urllib.request
import urllib.parse

UPSTREAM_DIR = "upstream_code"

# 自动自适应提取 GitHub 仓库名称（如 owner/repo）
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


# ================= 1. 注入 index.html (按键最优先 + 语法安全 + 在线更新) =================
html_file = os.path.join(UPSTREAM_DIR, "index.html")

if not os.path.exists(html_file):
    print(f"[FATAL ERROR] 找不到入口文件: {html_file}，打包终止！")
    send_ntfy_alert(["找不到入口文件 index.html"])
    sys.exit(1)

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# 包含 Cordova、高颜值更新弹窗 UI、下载进度条、开机静默检测与遥控器菜单
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

        // --- 核心安全保护函数：弹出快捷操作菜单 ---
        function triggerAstonQuickMenu() {{
            if (window.Lampa && Lampa.Player && Lampa.Player.opened && Lampa.Player.opened()) {{
                return;
            }}

            if (window.Lampa && Lampa.Select && Lampa.Lang) {{
                if (!window._aston_menu_lang_inited) {{
                    Lampa.Lang.add({{
                        aston_menu_title: {{
                            zh: "快捷菜单", en: "Quick Menu", ru: "Быстрое меню", uk: "Швидке меню",
                            be: "Хуткае меню", bg: "Бързо меню", cs: "Rychlé menu", fr: "Menu rapide",
                            he: "תפריט מהיר", pl: "Szybkie menu", pt: "Menu rápido", ro: "Meniu rapid"
                        }},
                        aston_menu_check_update: {{
                            zh: "检查更新", en: "Check for Updates", ru: "Проверить обновления", uk: "Перевірити оновлення",
                            be: "Праверыць абнаўленні", bg: "Проверка за актуализации", cs: "Zkontrolovat aktualizace", fr: "Vérifier les mises à jour",
                            he: "בדוק עדכונים", pl: "Sprawdź aktualizacje", pt: "Verificar atualizações", ro: "Verifică actualizări"
                        }},
                        aston_menu_check_update_descr: {{
                            zh: "在线检查是否有新版本 APK", en: "Check for latest APK online", ru: "Проверить наличие нового APK", uk: "Перевірити новий APK",
                            be: "Праверыць новы APK анлайн", bg: "Онлайн проверка за нов APK", cs: "Zkontrolovat novou verzi online", fr: "Vérifier la dernière version",
                            he: "בדוק גרסה חדשה ברשת", pl: "Sprawdź nową wersję online", pt: "Verificar nova versão online", ro: "Verifică versiunea nouă online"
                        }},
                        aston_menu_reload: {{
                            zh: "重新加载", en: "Reload", ru: "Перезагрузить", uk: "Перезавантажити",
                            be: "Перазагрузіць", bg: "Презареждане", cs: "Znovu načíst", fr: "Recharger",
                            he: "טעינה מחדש", pl: "Przeładuj", pt: "Recarregar", ro: "Reîncărcare"
                        }},
                        aston_menu_reload_descr: {{
                            zh: "刷新当前界面与数据", en: "Refresh interface and data", ru: "Обновить интерфейс и данные", uk: "Оновити інтерфейс та дані",
                            be: "Абнавіць інтэрфейс і дадзеныя", bg: "Опресняване на интерфейса и данните", cs: "Obnovit rozhraní a data", fr: "Actualiser l'interface et les données",
                            he: "רענון הממשק והנתונים", pl: "Odśwież interfejs i dane", pt: "Atualizar interface e dados", ro: "Reîmprospătează interfața și datele"
                        }},
                        aston_menu_exit: {{
                            zh: "退出应用", en: "Exit", ru: "Выход", uk: "Вихід",
                            be: "Выхад", bg: "Изход", cs: "Ukončit", fr: "Quitter",
                            he: "יציאה", pl: "Wyjście", pt: "Sair", ro: "Ieșire"
                        }},
                        aston_menu_exit_descr: {{
                            zh: "清理临时缓存并退出 Lampa", en: "Clean cache and exit Lampa", ru: "Очистить кэш и выйти из Lampa", uk: "Очистити кеш та вийти з Lampa",
                            be: "Ачысціць кэш і выйсці з Lampa", bg: "Изчистване на кеша и изход", cs: "Vymazat mezipaměť a ukončit", fr: "Vider le cache et quitter",
                            he: "ניקוי מטמון ויציאה מ-Lampa", pl: "Wyczyść pamięć podręczną i wyjdź", pt: "Limpar cache e sair", ro: "Curăță memoria cache și ieși"
                        }},
                        aston_update_found: {{ zh: "发现新版本", en: "New Version Available", ru: "Доступна новая версия", uk: "Доступна нова версія", be: "Даступная новая версія", bg: "Налична е нова версия", cs: "Nová verze k dispozici", fr: "Nouvelle version disponible", he: "גרסה חדשה זמינה", pl: "Dostępna nowa wersja", pt: "Nova versão disponível", ro: "Versiune nouă disponibilă" }},
                        aston_update_now: {{ zh: "立即更新", en: "Update Now", ru: "Обновить", uk: "Оновити", be: "Абнавіць", bg: "Обнови", cs: "Aktualizovat", fr: "Mettre à jour", he: "עדכן עכשיו", pl: "Aktualizuj", pt: "Atualizar agora", ro: "Actualizează acum" }},
                        aston_update_later: {{ zh: "稍后再说", en: "Later", ru: "Позже", uk: "Пізніше", be: "Пазней", bg: "По-късно", cs: "Později", fr: "Plus tard", he: "מאוחר יותר", pl: "Później", pt: "Mais tarde", ro: "Mai târziu" }},
                        aston_update_downloading: {{ zh: "正在下载更新", en: "Downloading Update", ru: "Загрузка обновления", uk: "Завантаження оновлення", be: "Загрузка абнаўлення", bg: "Изтегляне на актуализацията", cs: "Stahování aktualizace", fr: "Téléchargement de la mise à jour", he: "מוריד עדכון", pl: "Pobieranie aktualizacji", pt: "Baixando atualização", ro: "Descărcare actualizare" }},
                        aston_update_installing: {{ zh: "下载完成，正在打开安装器...", en: "Downloaded, opening installer...", ru: "Загружено, запуск установщика...", uk: "Завантажено, запуск інсталятора...", be: "Загружана, запуск усталёўшчыка...", bg: "Изтеглено, стартиране на инсталатора...", cs: "Staženo, otevírání instalátoru...", fr: "Ouverture de l'installateur...", he: "הורד, פותח מתקין...", pl: "Pobrano, otwieranie instalatora...", pt: "Baixado, abrindo instalador...", ro: "Descărcat, se deschide programul de instalare..." }},
                        aston_update_cancel: {{ zh: "取消", en: "Cancel", ru: "Отмена", uk: "Скасувати", be: "Адмена", bg: "Отказ", cs: "Zrušit", fr: "Annuler", he: "ביטול", pl: "Anuluj", pt: "Cancelar", ro: "Anulare" }},
                        aston_update_latest: {{ zh: "已经是最新版本", en: "Already up to date", ru: "Уже последняя версия", uk: "Вже остання версія", be: "Ужо апошняя версія", bg: "Вече е най-новата версия", cs: "Již máte nejnovější verzi", fr: "Déjà à jour", he: "כבר הגרסה העדכנית ביותר", pl: "Wersja jest aktualna", pt: "Já está na versão mais recente", ro: "Deja la cea mai recentă versiune" }}
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

        // 【最优先注册】：遥控器按键监听（保证设置键永远第一时间响应）
        window.addEventListener('keydown', function (e) {{
            var code = e.keyCode || e.which;
            if (code === 0 || code === 82 || code === 93) {{
                e.preventDefault();
                e.stopPropagation();
                triggerAstonQuickMenu();
            }}
        }}, true);

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
