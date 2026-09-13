import os
import sys
import re
import urllib.request
import urllib.parse

UPSTREAM_DIR = "upstream_code"

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


# ================= 1. 注入 index.html (Cordova + 预装 tmdb-proxy + 防盗链 + 缓存清理 + 菜单) =================
html_file = os.path.join(UPSTREAM_DIR, "index.html")

if not os.path.exists(html_file):
    print(f"[FATAL ERROR] 找不到入口文件: {html_file}，打包终止！")
    send_ntfy_alert(["找不到入口文件 index.html"])
    sys.exit(1)

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# 包含防盗链 meta 标签、预装插件、缓存清理与遥控器菜单
cordova_init_code = r"""
<meta name="referrer" content="no-referrer" />
<script src="cordova.js"></script>
<script>
    (function () {
        // --- 预装插件：自动注入 TMDB 代理插件（保留预装） ---
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
                console.log('[Init] 成功预装 TMDB 代理插件:', defaultPluginUrl);
            }
        } catch (e) {
            console.log('[Init] 预装插件检测跳过:', e);
        }

        // --- 安全清理 WebView 缓存后退出（保护老盒子存储） ---
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

        // --- 弹出快捷操作菜单（12 种全语言自动适配） ---
        function triggerAstonQuickMenu() {
            if (window.Lampa && Lampa.Player && Lampa.Player.opened && Lampa.Player.opened()) {
                return;
            }

            if (window.Lampa && Lampa.Select && Lampa.Lang) {
                if (!window._aston_menu_lang_inited) {
                    Lampa.Lang.add({
                        aston_menu_title: {
                            zh: '快捷菜单', en: 'Quick Menu', ru: 'Быстрое меню', uk: 'Швидке меню',
                            be: 'Хуткае меню', bg: 'Бързо меню', cs: 'Rychlé menu', fr: 'Menu rapide',
                            he: 'תפריט מהיר', pl: 'Szybkie menu', pt: 'Menu rápido', ro: 'Meniu rapid'
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
                        aston_menu_reload: {
                            zh: '重新加载', en: 'Reload', ru: 'Перезагрузить', uk: 'Перезавантажити',
                            be: 'Перазагрузіць', bg: 'Презареждане', cs: 'Znovu načíst', fr: 'Recharger',
                            he: 'טעינה מחדш', pl: 'Przeładuj', pt: 'Recarregar', ro: 'Reîncărcare'
                        },
                        aston_menu_reload_descr: {
                            zh: '刷新当前界面与数据', en: 'Refresh interface and data', ru: 'Обновить интерфейс и данные', uk: 'Оновити інтерфейс та дані',
                            be: 'Абнавіць інтэрфейс і дадзеныя', bg: 'Опресняване на интерфейса и данните', cs: 'Obnovit rozhraní a data', fr: 'Actualiser l\'interface et les données',
                            he: 'רענון הממשק והנתונים', pl: 'Odśwież interfejs i dane', pt: 'Atualizar interface e dados', ro: 'Reîmprospătează interfața și datele'
                        }
                    });
                    window._aston_menu_lang_inited = true;
                }

                Lampa.Select.show({
                    title: Lampa.Lang.translate('aston_menu_title'),
                    items: [
                        {
                            title: Lampa.Lang.translate('aston_menu_exit'),
                            subtitle: Lampa.Lang.translate('aston_menu_exit_descr'),
                            onSelect: function () {
                                cleanCacheAndExit();
                            }
                        },
                        {
                            title: Lampa.Lang.translate('aston_menu_reload'),
                            subtitle: Lampa.Lang.translate('aston_menu_reload_descr'),
                            onSelect: function () {
                                window.location.reload();
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

        // 监听遥控器按键：code === 0（设置键）及标准 82 / 93
        window.addEventListener('keydown', function (e) {
            var code = e.keyCode || e.which;
            if (code === 0 || code === 82 || code === 93) {
                e.preventDefault();
                e.stopPropagation();
                triggerAstonQuickMenu();
            }
        }, true);

        // Cordova 初始化
        document.addEventListener('deviceready', function () {
            if (document.readyState === 'complete') {
                if (navigator.splashscreen) navigator.splashscreen.hide();
            } else {
                window.addEventListener('load', function () {
                    if (navigator.splashscreen) navigator.splashscreen.hide();
                });
            }

            document.addEventListener('menubutton', function (e) {
                triggerAstonQuickMenu();
            }, false);
        });
    })();
</script>
"""

if "<head>" in html_content:
    html_content = html_content.replace("<head>", f"<head>\n{cordova_init_code}", 1)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[Success] index.html 成功注入防盗链穿透、预装 tmdb-proxy 与全功能脚本")
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

print("[Success] 所有 23 条规则校验 100% 通过，防盗链穿透与插件就绪！准许打包 APK。\n")
