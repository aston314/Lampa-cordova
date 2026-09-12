import os
import sys
import re

UPSTREAM_DIR = "upstream_code"

# ================= 1. 注入 index.html (Cordova.js + 闪屏/状态栏) =================
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
        // 隐藏启动闪屏（兼容 load 事件）
        if (document.readyState === 'complete') {
            if (navigator.splashscreen) navigator.splashscreen.hide();
        } else {
            window.addEventListener('load', function() {
                if (navigator.splashscreen) navigator.splashscreen.hide();
            });
        }

        // 隐藏顶部状态栏（全屏沉浸）
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
    print("[Success] index.html 成功注入 Cordova 初始化与状态栏/闪屏脚本")
else:
    print("[FATAL ERROR] index.html 中未找到 <head> 标签，打包终止！")
    sys.exit(1)


# ================= 2. 定义大段代码模板 =================

# 模板 1: Cordova 网络请求实现
CORDOVA_HTTP_REQ_CODE = r"""if (!!window.cordova) {

        function tryParseJSON(str) {
          try {
            JSON.parse(str);
            return true;
          } catch (e) {
            return false;
          }
        };

        function queryStringToJSON(str) {
          var pairs = str.split('&');
          var result = {};

          for (var i = 0; i < pairs.length; i++) {
            var pair = pairs[i].split('=');
            var name = decodeURIComponent(pair[0]);
            var value = decodeURIComponent(pair[1] || '');

            if (name.length) {
              if (result.hasOwnProperty(name)) {
                if (!Array.isArray(result[name])) {
                  result[name] = [result[name]];
                }
                result[name].push(value);
              } else {
                result[name] = value;
              }
            }
          }
          return result;
        };

        var url = params.url;
        var data = params.post_data;
        var headers = params.headers;
        var contentType = params.contentType;
        var requestContent = "";

        if (data) {
          if (typeof data === "string") {
            requestContent = data;
            contentType = tryParseJSON(requestContent) ? "application/json" : "application/x-www-form-urlencoded";
          } else if (typeof data === "object") {
            contentType = "application/json";
            requestContent = JSON.stringify(data);
          }
        };

        if (requestContent !== "") {
          if (!headers) {
            headers = {};
          }

          if (!headers.hasOwnProperty("Content-Type")) {
            if (headers.hasOwnProperty("Content-Type")) {
              contentType = headers["Content-Type"] || contentType;
              delete headers["Content-Type"];
            } else if (headers.hasOwnProperty("content-type")) {
              contentType = headers["content-type"] || contentType;
              delete headers["content-type"];
            }

            headers["Content-Type"] = contentType;
          }
        };

        var finalRequestContent = requestContent;
        var finalHeaders = headers;

        var dataType = params.dataType || 'json';

        var para_fetch = {};
        para_fetch.headers = finalHeaders;

        if (!finalRequestContent) {
        if (url.includes('ddys')) {
            para_fetch.method = 'GET';
            cordovaFetch(url, para_fetch)
              .then(function (response) {
                if (dataType == 'json') {
                  return {
                    c: response.json(),
                    s: response.status,
                    t: response.statusText
                  };
                } else if (dataType == 'text') {
                  return {
                    response,
                    c: response.text(),
                    s: response.status,
                    t: response.statusText
                  };
                };
              }).then(function (responseData) {
                if (responseData.s === 200) {
                  secuses(responseData.c._result)
                } else {
                  error({
                    status: responseData.s
                  }, '');
                }
              }).catch(function (err) {
                error({
                  status: 404
                }, '');
                console.error(err)
              });
          } else {
          cordovaHTTP.acceptAllCerts(true, function () {
          }, function () {
          });
          cordovaHTTP.get(url, {}, (!finalHeaders ? {} : finalHeaders), function (response) {
            if (dataType == 'json') {
              try {
                secuses(JSON.parse(response.data));
              } catch (e) {
                error({
                  status: response.status
                }, response.error);
              }
            } else if (dataType == 'text') {
              secuses(response.data)
            };
          }, function (response) {
            error({
              status: response.status
            }, response.error);
          });
          }
        } else {
          para_fetch.method = 'POST';
          para_fetch.body = finalRequestContent;
          if (data !== null) {
            if (!tryParseJSON(finalRequestContent)) {
              cordovaHTTP.acceptAllCerts(true, function () {
              }, function () {
              });
              cordovaHTTP.post(url, queryStringToJSON(finalRequestContent), (!finalHeaders ? {} : finalHeaders), function (response) {
                if (dataType == 'json') {
                  try {
                    secuses(JSON.parse(response.data));
                  } catch (e) {
                    error({
                      status: response.status
                    }, response.error);
                  }
                } else if (dataType == 'text') {
                  secuses(response.data)
                };
              }, function (response) {
                error({
                  status: response.status
                }, response.error);
              });
            } else {
              cordovaFetch.setTimeout = 60;
              cordovaFetch(url, para_fetch)
                .then(function (response) {
                  if (dataType == 'json') {
                    return {
                      c: response.json(),
                      s: response.status,
                      t: response.statusText
                    };
                  } else if (dataType == 'text') {
                    return {
                      response,
                      c: response.text(),
                      s: response.status,
                      t: response.statusText
                    };
                  };
                }).then(function (responseData) {
                  if (responseData.s === 200) {
                    secuses(responseData.c._result)
                  } else {
                    error({
                      status: responseData.s
                    }, '');
                  }
                }).catch(function (err) {
                  error({
                    status: 404
                  }, '');
                  console.error(err)
                });
            }
          }
        }
      } else {
        Android.httpReq(params, {
          complite: secuses,
          error: error
        });
      };"""

# 模板 2: YouTube Intent 调起
OPEN_YOUTUBE_CODE = r"""window.plugins.intentShim.startActivity({
          action : window.plugins.intentShim.ACTION_VIEW,
          url : link
        }, function() {
        }, function() {
          console.log("Failed to open Youtube URL via Android Intent");
        });"""

# 模板 3: 磁力链接 Intent 1
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

# 模板 4: 磁力链接 Intent 2
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

# 模板 5: 外部播放器调起与时间轴回传
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
            var new_result = {};
            new_result.hash = data.timeline.hash;
            new_result.time = time;
            new_result.duration = duration;
            new_result.percent = percent;
            
            data.timeline.handler(percent, time, duration);
            data.timeline.time =time;
            data.timeline.duration = duration;
            data.timeline.percent = percent;
            
            Timeline.update(new_result);
          };
        }, function() {
          console.log("Failed to open video URL via Android Intent");
        });"""

# 模板 6: 版本号 fallback
VERSION_CODE_FALLBACK_CODE = r"""var versionCode;
        if (typeof AndroidJS !== 'undefined') {
            var current = AndroidJS.appVersion().split('-');
            versionCode = current.pop();
        } else {
            versionCode = 28;
        };"""


# ================= 3. 严格替换规则列表（共 19 项） =================
STRICT_RULES = [
    {
        "name": "允许在 Cordova 下激活 AndroidJS 平台逻辑分支",
        "pattern": r"if\s*\(\s*typeof AndroidJS !== 'undefined'\s*\)",
        "new": "if (typeof AndroidJS !== 'undefined' || !!window.cordova)"
    },
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
        "name": "Cordova HTTP/Fetch 网络请求引擎大段注入",
        "pattern": r"Android\.httpReq\(\s*params\s*,\s*\{\s*complite\s*:\s*secuses\s*,\s*error\s*:\s*error\s*\}\s*\);",
        "new": CORDOVA_HTTP_REQ_CODE
    }
]

# 待检查的目标文件
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

# 逐条严格比对替换
for rule in STRICT_RULES:
    rule_name = rule["name"]
    pattern = rule["pattern"]
    new_text = rule["new"]
    total_replaced = 0
    
    for file_path, content in file_data.items():
        new_content, count = re.subn(pattern, new_text, content)
        if count > 0:
            file_data[file_path] = new_content
            total_replaced += count
            print(f"  -> 在 {os.path.basename(file_path)} 中成功匹配并替换了 {count} 处")

    if total_replaced == 0:
        print(f"❌ [VERIFY FAILED] 规则【{rule_name}】失败！未在代码中匹配到目标段落。\n   Pattern: {pattern}")
        has_error = True
    else:
        print(f"✅ [VERIFY PASSED] 规则【{rule_name}】验证通过（共替换 {total_replaced} 处）\n")

# 只要有任何一条规则未替换成功，立刻熔断终止打包
if has_error:
    print("=" * 65)
    print("[FATAL ERROR] 存在未通过校验的替换规则，为保证 APK 可用性，工作流已主动终止！")
    print("=" * 65)
    sys.exit(1)

# 全部验证通过后写回文件
for file_path, content in file_data.items():
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("[Success] 所有 19 条规则校验 100% 通过，文件已安全写回！准许打包 APK。\n")
