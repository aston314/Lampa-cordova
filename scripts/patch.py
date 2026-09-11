import os
import re

# ================= 1. 向 index.html 注入 Cordova 初始化脚本 =================
HTML_FILE = os.path.join("upstream_code", "index.html")

if os.path.exists(HTML_FILE):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 包含 cordova.js 和你的 deviceready 监听逻辑
    # 注意：加了一个 readystate 判断，防止页面 load 发生在 deviceready 之前导致闪屏无法关闭
    cordova_init_code = """
    <script src="cordova.js"></script>
    <script>
        document.addEventListener('deviceready', function () {
            // 隐藏启动图（兼容 load 事件已提前触发的情况）
            if (document.readyState === 'complete') {
                if (navigator.splashscreen) navigator.splashscreen.hide();
            } else {
                window.addEventListener('load', function() {
                    if (navigator.splashscreen) navigator.splashscreen.hide();
                });
            }

            // 隐藏顶部状态栏
            if (window.StatusBar) {
                window.StatusBar.hide();
            }
        });
    </script>
    """

    # 注入到 <head> 标签之后
    if "<head>" in html_content:
        html_content = html_content.replace("<head>", f"<head>\n{cordova_init_code}", 1)
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print("[Success] Injected Cordova scripts into index.html")
    else:
        print("[Warning] <head> tag not found in index.html")


# ================= 2. 替换 app.min.js 中的主方法 =================
TARGET_FILE = os.path.join("upstream_code", "app.min.js")

if os.path.exists(TARGET_FILE):
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 在这里写你的特定方法替换逻辑
    # content = content.replace("oldMethod()", "newCordovaMethod()")

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Success] Patched methods in {TARGET_FILE}")
