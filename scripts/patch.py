import os
import sys
import re
import json
import shutil
import urllib.request
import urllib.parse

UPSTREAM_DIR = "upstream_code"
os.makedirs(UPSTREAM_DIR, exist_ok=True)

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

def send_ntfy_alert(failed_rule_names):
    ntfy_topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not ntfy_topic:
        return
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    action_url = f"https://github.com/{repo}/actions/runs/{run_id}" if run_id and repo else ""
    message = "上游源码有更新，以下规则未匹配成功：\n\n" + "\n".join([f"❌ {n}" for n in failed_rule_names])
    query_params = {"title": "⚠️ Lampa 源码规则熔断报警", "priority": "urgent", "tags": "warning,skull"}
    if action_url:
        query_params["click"] = action_url
    url = f"https://ntfy.sh/{ntfy_topic}?" + urllib.parse.urlencode(query_params)
    req = urllib.request.Request(url, data=message.encode("utf-8"))
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[Warning] ntfy 发送失败: {e}")

# ================= 1. 读取 plugins.json =================
REMOTE_PLUGINS_FILE = os.path.join("plugins", "plugins.json")
default_plugins_list = []
if os.path.isfile(REMOTE_PLUGINS_FILE):
    try:
        with open(REMOTE_PLUGINS_FILE, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            if isinstance(loaded_data, list):
                for p in loaded_data:
                    if isinstance(p, dict) and p.get("status") == 1 and p.get("url"):
                        default_plugins_list.append(p)
    except Exception:
        pass
DEFAULT_PLUGINS_JSON_STR = json.dumps(default_plugins_list, ensure_ascii=False)

# ================= 2. 同步 scripts/cordova_bridge.js =================
BRIDGE_SRC = os.path.join("scripts", "cordova_bridge.js")
BRIDGE_DST = os.path.join(UPSTREAM_DIR, "cordova_bridge.js")
if os.path.exists(BRIDGE_SRC):
    shutil.copyfile(BRIDGE_SRC, BRIDGE_DST)
    print(f"[Success] 成功同步桥接文件: {BRIDGE_SRC} -> {BRIDGE_DST}")
else:
    print(f"[FATAL ERROR] 找不到: {BRIDGE_SRC}")
    send_ntfy_alert(["找不到 scripts/cordova_bridge.js"])
    sys.exit(1)

# ================= 3. 注入 index.html =================
html_file = os.path.join(UPSTREAM_DIR, "index.html")
if not os.path.exists(html_file):
    sys.exit(1)

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

cordova_init_template = r"""
<meta name="referrer" content="no-referrer" />
<script src="cordova.js"></script>
<script src="cordova_bridge.js"></script>
<style>
    html, body { background: #1d1f20 !important; margin: 0; padding: 0; overflow: hidden; }
    .welcome { transition: opacity 0.4s ease-out !important; }
</style>
<script>
    (function () {
        window.CURRENT_BUILD_CODE = __BUILD_NUMBER__;
        window.CURRENT_REPO = "__REPO_NAME__";
        try {
            var defaultPlugins = __DEFAULT_PLUGINS_JSON__;
            var savedPlugins = JSON.parse(localStorage.getItem('plugins') || '[]');
            var modified = false;
            defaultPlugins.forEach(function (dp) {
                if (!dp || !dp.url || dp.status === 0) return;
                var exists = savedPlugins.some(function (p) {
                    return (typeof p === 'string' && p === dp.url) || (p && p.url === dp.url);
                });
                if (!exists) { savedPlugins.push(dp); modified = true; }
            });
            if (modified) localStorage.setItem('plugins', JSON.stringify(savedPlugins));
        } catch (e) {}
    })();
</script>
"""
cordova_init_code = (
    cordova_init_template
    .replace("__BUILD_NUMBER__", str(BUILD_NUMBER))
    .replace("__REPO_NAME__", REPO_NAME)
    .replace("__DEFAULT_PLUGINS_JSON__", DEFAULT_PLUGINS_JSON_STR)
)

if "<head>" in html_content:
    html_content = html_content.replace("<head>", "<head>\n" + cordova_init_code, 1)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

# ================= 4. 语言包内嵌 =================
lang_dir = os.path.join(UPSTREAM_DIR, "lang")
all_embedded_langs = {}
if os.path.exists(lang_dir):
    for filename in sorted(os.listdir(lang_dir)):
        if filename.endswith(".js") and filename != "meta.js":
            lang_code = filename[:-3]
            try:
                with open(os.path.join(lang_dir, filename), "r", encoding="utf-8") as f:
                    raw_content = f.read()
                clean_obj = re.sub(r"^\s*export\s+default\s*", "", raw_content).strip()
                if clean_obj.endswith(";"):
                    clean_obj = clean_obj[:-1]
                all_embedded_langs[lang_code] = clean_obj
            except Exception:
                pass

lang_entries = [f'"{code}": {obj_str}' for code, obj_str in all_embedded_langs.items()]
embedded_langs_js = "{\n" + ",\n".join(lang_entries) + "\n}"
ALL_LANG_EMBEDDED_CODE = (
    "var embedded_langs = " + embedded_langs_js + ";\n"
    "    if (embedded_langs[code]) {\n"
    "      Lang.AddTranslation(code, embedded_langs[code]);\n"
    "      loadTask();\n"
    "    } else if (['ru', 'en'].indexOf(code) >= 0) loadTask();"
)

# ================= 5. 扫描本地 plugins =================
LOCAL_PLUGINS_DIR = "plugins"
local_plugin_pushes = ["puts.push('./plugins/modification.js');"]
if os.path.isdir(LOCAL_PLUGINS_DIR):
    for filename in sorted(os.listdir(LOCAL_PLUGINS_DIR)):
        if filename.endswith(".js") and not filename.startswith("."):
            local_plugin_pushes.append(f"puts.push('./plugins/{filename}');")
LOCAL_PLUGINS_INJECT_CODE = "\n        ".join(local_plugin_pushes)

# ================= 6. 原汁原味的网络请求代码模板 (原版 100% 可用逻辑) =================
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

      } else {
        Android.httpReq(params, {
          complite: secuses,
          error: error
        });
      };"""

# ================= 7. 最终精炼规则（保留 6 条核心） =================
STRICT_RULES = [
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
        "name": "全语言包自动内嵌",
        "pattern": r"if\s*\(\s*\['ru',\s*'en'\]\.indexOf\(code\)\s*>=\s*0\s*\)\s*loadTask\(\);",
        "new": ALL_LANG_EMBEDDED_CODE
    },
    {
        "name": "强制本地加载核心解码库 vender",
        "pattern": r"return\s+window\.location\.protocol\s*==\s*['\"]file:['\"]\s*\|\|\s*window\.location\.href\.indexOf\(['\"]chrome-extension['\"]\)\s*>\s*-1\s*\?\s*object\$2\.github_lampa\s*\+\s*['\"]vender/['\"]\s*\+\s*lib\s*:\s*['\"]\./vender/['\"]\s*\+\s*lib;",
        "new": "return './vender/' + lib;"
    },
    {
        "name": "动态本地插件自动加载注册",
        "pattern": r"puts\.push\(['\"]\./plugins/modification\.js['\"]\);",
        "new": LOCAL_PLUGINS_INJECT_CODE
    },
    # 👇 把这句你原来 100% 能稳定工作的网络替换原封不动加回！
    {
        "name": "Cordova HTTP/Fetch 网络请求引擎注入",
        "pattern": r"Android\.httpReq\(\s*params\s*,\s*\{\s*complite\s*:\s*secuses\s*,\s*error\s*:\s*error\s*\}\s*\);",
        "new": CORDOVA_HTTP_REQ_CODE
    }
]

TARGET_FILES = [
    os.path.join(UPSTREAM_DIR, "index.html"),
    os.path.join(UPSTREAM_DIR, "app.min.js")
]

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
        print(f"❌ [VERIFY FAILED] 规则【{rule_name}】未匹配！\n   Pattern: {pattern}")
        has_error = True
        failed_rules.append(rule_name)
    else:
        print(f"✅ [VERIFY PASSED] 规则【{rule_name}】通过（替换 {total_replaced} 处）")

if has_error:
    send_ntfy_alert(failed_rules)
    sys.exit(1)

for file_path, content in file_data.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"\n[Success] 全部 6 条核心规则验证通过，原生网络通道与 Bridge 完美结合！准许打包。\n")
