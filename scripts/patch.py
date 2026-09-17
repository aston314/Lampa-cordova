import os
import sys
import re
import json
import shutil
import urllib.request
import urllib.parse

UPSTREAM_DIR = "upstream_code"

# 防御性保障：确保目标目录存在
os.makedirs(UPSTREAM_DIR, exist_ok=True)

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

    message = "上游 yumata/lampa 源码有更新，但以下核心规则未匹配成功，已自动终止打包：\n\n"
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


# ================= 1. 读取并解析 plugins/plugins.json 远程预装插件配置 =================
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
                        print(f"[Success] 读取预装远程插件: {p.get('name', '未命名')} -> {p.get('url')}")
    except Exception as e:
        print(f"[Warning] 读取 plugins/plugins.json 异常: {e}")
else:
    print("[Info] 未找到 plugins/plugins.json，跳过远程插件预装。")

if not default_plugins_list:
    print("[Info] 当前无任何有效远程预装插件，将打包纯净版。")

DEFAULT_PLUGINS_JSON_STR = json.dumps(default_plugins_list, ensure_ascii=False)


# ================= 2. 同步 scripts/cordova_bridge.js 到待打包源码目录 =================
BRIDGE_SRC = os.path.join("scripts", "cordova_bridge.js")
BRIDGE_DST = os.path.join(UPSTREAM_DIR, "cordova_bridge.js")

if os.path.exists(BRIDGE_SRC):
    shutil.copyfile(BRIDGE_SRC, BRIDGE_DST)
    print(f"[Success] 成功同步原生桥接层文件: {BRIDGE_SRC} -> {BRIDGE_DST}")
else:
    print(f"[FATAL ERROR] 找不到桥接文件: {BRIDGE_SRC}，打包终止！")
    send_ntfy_alert(["找不到 scripts/cordova_bridge.js 文件"])
    sys.exit(1)


# ================= 3. 注入 index.html (引入 Bridge + 防盗链 + 全屏) =================
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
<script src="cordova_bridge.js"></script>
<style>
    html, body {
        background: #1d1f20 !important;
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    .welcome {
        transition: opacity 0.4s ease-out !important;
    }
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
                if (!exists) {
                    savedPlugins.push(dp);
                    modified = true;
                    console.log('[Init] 成功预装插件:', dp.name || dp.url);
                }
            });

            if (modified) {
                localStorage.setItem('plugins', JSON.stringify(savedPlugins));
            }
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
    print("[Success] index.html 注入就绪（已挂载 cordova_bridge.js）")
else:
    print("[FATAL ERROR] index.html 中未找到 <head> 标签！")
    send_ntfy_alert(["index.html 中未找到 <head> 标签"])
    sys.exit(1)


# ================= 4. 遍历并内嵌所有语言包 =================
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
                print(f"[Success] 解析语言包: {filename} -> 代码: {lang_code}")
            except Exception as e:
                print(f"[Warning] 解析语言包 {filename} 失败: {e}")

lang_entries = [f'"{code}": {obj_str}' for code, obj_str in all_embedded_langs.items()]
embedded_langs_js = "{\n" + ",\n".join(lang_entries) + "\n}"

ALL_LANG_EMBEDDED_CODE = (
    "var embedded_langs = " + embedded_langs_js + ";\n"
    "    if (embedded_langs[code]) {\n"
    "      Lang.AddTranslation(code, embedded_langs[code]);\n"
    "      loadTask();\n"
    "    } else if (['ru', 'en'].indexOf(code) >= 0) loadTask();"
)


# ================= 5. 扫描本地 plugins 目录 =================
LOCAL_PLUGINS_DIR = "plugins"
local_plugin_pushes = ["puts.push('./plugins/modification.js');"]

if os.path.isdir(LOCAL_PLUGINS_DIR):
    for filename in sorted(os.listdir(LOCAL_PLUGINS_DIR)):
        if filename.endswith(".js") and not filename.startswith("."):
            local_plugin_pushes.append(f"puts.push('./plugins/{filename}');")
            print(f"[Success] 发现本地插件: {filename}")

LOCAL_PLUGINS_INJECT_CODE = "\n        ".join(local_plugin_pushes)


# ================= 6. 极简核心替换规则（仅保留最精简的 5 条内部补丁） =================
STRICT_RULES = [
    {
        "name": "禁用频道更新 updateChannel 避免 DOM 节点查找崩溃",
        "pattern": r"if\s*\(\s*checkVersion\(28\)\s*\)\s*AndroidJS\.updateChannel\(where\);",
        "new": "if (checkVersion(28)) !!window.cordova ? null : AndroidJS.updateChannel(where);"
    },
    {
        "name": "修复 updateChannels 中 AndroidJS.saveBookmarks 语法崩溃",
        "pattern": r"typeof\s+AndroidJS\.saveBookmarks\s*!==\s*['\"]undefined['\"]",
        "new": "typeof AndroidJS !== 'undefined' && typeof AndroidJS.saveBookmarks !== 'undefined'"
    },
    # {
    #     "name": "海报播放 action: play 注入 1",
    #     "pattern": r"poster:\s*SERVER\.movie\.img,\s*media:\s*SERVER\.movie\.name\s*\?\s*'tv'\s*:\s*'movie',\s*data:\s*\{",
    #     "new": "poster: SERVER.movie.img,\n          media: SERVER.movie.name ? 'tv' : 'movie',\n          action: \"play\",\n          data: {"
    # },
    # {
    #     "name": "海报播放 action: play 注入 2",
    #     "pattern": r"poster:\s*SERVER\.object\.poster,\s*media:\s*SERVER\.movie\.name\s*\?\s*'tv'\s*:\s*'movie',\s*data:\s*\{",
    #     "new": "poster: SERVER.object.poster,\n        media: SERVER.movie.name ? 'tv' : 'movie',\n        action: \"play\",\n        data: {"
    # },
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
    }
]

TARGET_FILES = [
    os.path.join(UPSTREAM_DIR, "index.html"),
    os.path.join(UPSTREAM_DIR, "app.min.js")
]

print("\n[Info] 开始进行核心补丁匹配与校验...")

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
    print("=" * 65)
    print("[FATAL ERROR] 存在未通过校验的规则，正在发送通知...")
    send_ntfy_alert(failed_rules)
    print("=" * 65)
    sys.exit(1)

for file_path, content in file_data.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"\n[Success] 全部 {len(STRICT_RULES)} 条核心规则验证通过，精简架构就绪！准许打包 APK。\n")
