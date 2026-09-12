import os
import sys

UPSTREAM_DIR = "upstream_code"

# ================= 1. 严格检查并注入 index.html =================
html_file = os.path.join(UPSTREAM_DIR, "index.html")

if not os.path.exists(html_file):
    print(f"[FATAL ERROR] 找不到入口文件: {html_file}，打包终止！")
    sys.exit(1)

with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

cordova_init_code = """
<script src="cordova.js"></script>
<script>
    document.addEventListener('deviceready', function () {
        // 隐藏启动闪屏
        if (document.readyState === 'complete') {
            if (navigator.splashscreen) navigator.splashscreen.hide();
        } else {
            window.addEventListener('load', function() {
                if (navigator.splashscreen) navigator.splashscreen.hide();
            });
        }

        // 隐藏顶部状态栏（全屏）
        if (window.StatusBar) {
            window.StatusBar.hide();
        }
    });
</script>
"""

if "<head>" in html_content:
    html_content = html_content.replace("<head>", f"<head>\n{cordova_init_code}", 1)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[Success] index.html 注入 Cordova 初始化脚本成功")
else:
    print("[FATAL ERROR] index.html 中未找到 <head> 标签，无法注入 cordova.js，打包终止！")
    sys.exit(1)


# ================= 2. 严格校验并替换 app.min.js =================
target_js_file = os.path.join(UPSTREAM_DIR, "app.min.js")

if not os.path.exists(target_js_file):
    print(f"[FATAL ERROR] 找不到目标核心文件: {target_js_file}，打包终止！")
    sys.exit(1)

with open(target_js_file, "r", encoding="utf-8") as f:
    js_content = f.read()

# 在这里定义对 app.min.js 的【必选】严格替换规则列表
# 格式: (规则描述, 原始必须存在的代码, 替换后的代码)
STRICT_RULES = [
    (
        "替换 Android.exit() 退出代码",
        "Android.exit()",
        "!!window.cordova ? navigator.app.exitApp() : Android.exit()"
    ),
    (
        "替换 AndroidJS.exit() 退出代码",
        "AndroidJS.exit()",
        "!!window.cordova ? navigator.app.exitApp() : AndroidJS.exit()"
    ),
    # 以后如果你有其他必须替换的逻辑，直接按格式加在下方即可：
    # ("播放器调用替换", "oldPlayer()", "newCordovaPlayer()"),
]

print(f"\n[Info] 开始对 {target_js_file} 进行严格替换校验...")

has_error = False

for rule_name, old_code, new_code in STRICT_RULES:
    count = js_content.count(old_code)
    if count == 0:
        print(f"❌ [VERIFY FAILED] 规则【{rule_name}】未找到目标代码: \"{old_code}\"")
        has_error = True
    else:
        js_content = js_content.replace(old_code, new_code)
        print(f"✅ [VERIFY PASSED] 规则【{rule_name}】成功匹配并替换 {count} 处")

# 如果有任意一条必选规则没有匹配到，直接熔断报错退出
if has_error:
    print("\n" + "="*60)
    print("[FATAL ERROR] app.min.js 关键代码替换校验失败！")
    print("上游源码可能有变动，为了防止生成不可用的 APK，工作流已主动终止。")
    print("="*60)
    sys.exit(1)

# 全部规则校验通过，才真正写入文件
with open(target_js_file, "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"\n[Success] 所有严格规则均已验证通过，{target_js_file} 修改完成！准许打包。\n")
