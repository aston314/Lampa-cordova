# Lampa Plugins

Lampa plugins collection.

本项目用于存放适用于 **Lampa** 的 JavaScript 插件。所有插件均以 `.js` 文件形式提供，并遵循 Lampa 插件的基本编写规范。

---

## 🌐 Language / 语言 / Язык / Мова

* [🇨🇳 简体中文](#简体中文)
* [🇬🇧 English](#english)
* [🇷🇺 Русский](#русский)
* [🇺🇦 Українська](#українська)

---

<a id="简体中文"></a>

## 🇨🇳 简体中文

### 项目简介

这是一个用于存放 **Lampa JavaScript 插件**的插件仓库。

插件主要用于扩展 Lampa 的功能，例如：

* 添加或扩展影视资源源
* 增加视频解析功能
* 添加直播源
* 扩展播放器功能
* 添加字幕相关功能
* 修改或增强 Lampa 的界面功能
* 增加其他 Lampa 可扩展功能

所有插件均为 JavaScript 文件，并且必须以 `.js` 结尾。

### 插件要求

插件必须符合 Lampa 的插件加载方式和 JavaScript 编写规范。

基本要求：

1. 插件文件必须使用 `.js` 扩展名。
2. 插件应能够直接通过 Lampa 的插件机制加载。
3. 插件代码应尽量避免污染全局命名空间。
4. 插件应使用 Lampa 提供的 API 和扩展机制。
5. 不应修改与插件功能无关的 Lampa 核心代码。
6. 插件应尽可能兼容当前版本的 Lampa。
7. 插件中使用的第三方依赖应明确说明。
8. 插件名称、版本及主要功能应在代码中清晰定义。

### 推荐的插件结构

推荐使用类似下面的结构：

```javascript
(function () {
    'use strict';

    var plugin = {
        name: 'Plugin Name',
        version: '1.0.0'
    };

    // Plugin code

})();
```

如果插件需要使用 Lampa API，应按照 Lampa 的插件机制进行初始化。

例如：

```javascript
(function () {
    'use strict';

    function startPlugin() {
        // Plugin initialization
    }

    if (window.appready) {
        startPlugin();
    } else {
        Lampa.Listener.follow('app', function (event) {
            if (event.type === 'ready') {
                startPlugin();
            }
        });
    }

})();
```

具体实现应根据插件所使用的 Lampa API 和功能进行调整。

### 文件命名

插件文件必须以 `.js` 结尾。

推荐使用具有明确含义的文件名：

```text
plugin-name.js
torrentio.js
live-sports.js
subtitle.js
video-parser.js
```

不推荐使用：

```text
plugin
plugin.txt
plugin.json
plugin.md
```

### 安装

在 Lampa 中打开插件设置，并添加插件 JavaScript 文件对应的地址。

例如：

```text
https://example.com/lampa/plugin-name.js
```

然后根据 Lampa 的插件管理功能加载插件。

### 更新

插件更新后，只需要保持原来的 `.js` 地址不变，并更新插件文件内容即可。

建议在插件内部维护版本号，例如：

```javascript
version: '1.2.0'
```

### 目录结构

推荐的项目结构：

```text
.
├── README.md
├── plugins/
│   ├── plugin-name.js
│   ├── torrentio.js
│   ├── live-sports.js
│   └── subtitle.js
└── LICENSE
```

如果项目规模较小，也可以直接将 `.js` 插件文件放在根目录：

```text
.
├── README.md
├── torrentio.js
├── live-sports.js
└── subtitle.js
```

### 注意事项

本项目中的插件仅用于扩展 Lampa 功能。

第三方网站、API、视频源、字幕源等内容的可用性由对应服务提供方决定。

使用插件时，请遵守所在国家或地区的法律法规，以及相关网站和服务的使用条款。

---

<a id="english"></a>

## 🇬🇧 English

### About

This repository contains **JavaScript plugins for Lampa**.

The plugins are designed to extend Lampa with additional functionality, such as:

* Additional movie and TV sources
* Video parsers
* Live streaming sources
* Player extensions
* Subtitle-related features
* UI enhancements
* Other Lampa-compatible extensions

All plugins are distributed as JavaScript files and must use the `.js` extension.

### Plugin Requirements

Plugins should follow the Lampa plugin architecture and JavaScript conventions.

General requirements:

1. Plugin files must use the `.js` extension.
2. Plugins should be loadable through Lampa's plugin mechanism.
3. Avoid unnecessary global variables.
4. Use Lampa APIs and extension mechanisms whenever possible.
5. Do not modify unrelated Lampa core functionality.
6. Maintain compatibility with current Lampa versions whenever possible.
7. Clearly document third-party dependencies.
8. Plugin name, version and main functionality should be clearly defined.

### Recommended Structure

A basic plugin can follow this structure:

```javascript
(function () {
    'use strict';

    var plugin = {
        name: 'Plugin Name',
        version: '1.0.0'
    };

    // Plugin code

})();
```

If the plugin requires Lampa APIs, initialize it according to the Lampa plugin architecture.

### File Naming

Plugin files must end with `.js`.

Recommended:

```text
plugin-name.js
torrentio.js
live-sports.js
subtitle.js
video-parser.js
```

### Installation

Add the URL of the plugin JavaScript file through Lampa's plugin settings.

Example:

```text
https://example.com/lampa/plugin-name.js
```

Then load the plugin using Lampa's plugin management functionality.

### Project Structure

Recommended:

```text
.
├── README.md
├── plugins/
│   ├── plugin-name.js
│   ├── torrentio.js
│   ├── live-sports.js
│   └── subtitle.js
└── LICENSE
```

For smaller projects, plugin files can also be placed directly in the repository root.

### Disclaimer

The availability of third-party websites, APIs, video sources and subtitle sources depends on their respective providers.

Users are responsible for complying with applicable laws, regulations and service terms.

---

<a id="русский"></a>

## 🇷🇺 Русский

### О проекте

Этот репозиторий содержит **JavaScript-плагины для Lampa**.

Плагины предназначены для расширения возможностей Lampa, включая:

* дополнительные источники фильмов и сериалов;
* парсеры видео;
* источники прямых трансляций;
* расширения проигрывателя;
* функции, связанные с субтитрами;
* расширения интерфейса;
* другие функции, совместимые с Lampa.

Все плагины распространяются в виде JavaScript-файлов с расширением `.js`.

### Требования к плагинам

Плагины должны соответствовать архитектуре и правилам написания плагинов Lampa.

Основные требования:

1. Файл плагина должен иметь расширение `.js`.
2. Плагин должен загружаться через механизм плагинов Lampa.
3. Следует избегать ненужного загрязнения глобального пространства имён.
4. По возможности следует использовать API и механизмы расширения Lampa.
5. Не следует изменять части Lampa, которые не связаны с работой плагина.
6. Желательно поддерживать актуальные версии Lampa.
7. Использование сторонних зависимостей должно быть указано.
8. Название, версия и назначение плагина должны быть понятны из исходного кода.

### Рекомендуемая структура

Базовый плагин может иметь следующую структуру:

```javascript
(function () {
    'use strict';

    var plugin = {
        name: 'Plugin Name',
        version: '1.0.0'
    };

    // Код плагина

})();
```

При использовании API Lampa инициализация должна выполняться в соответствии с механизмом плагинов Lampa.

### Имена файлов

Файлы плагинов должны заканчиваться на `.js`.

Например:

```text
plugin-name.js
torrentio.js
live-sports.js
subtitle.js
video-parser.js
```

### Установка

Добавьте URL JavaScript-файла плагина в настройках плагинов Lampa.

Например:

```text
https://example.com/lampa/plugin-name.js
```

После этого загрузите плагин через менеджер плагинов Lampa.

### Структура проекта

Рекомендуемая структура:

```text
.
├── README.md
├── plugins/
│   ├── plugin-name.js
│   ├── torrentio.js
│   ├── live-sports.js
│   └── subtitle.js
└── LICENSE
```

Для небольших проектов файлы `.js` можно размещать непосредственно в корне репозитория.

### Отказ от ответственности

Работоспособность сторонних сайтов, API, видеоресурсов и источников субтитров зависит от соответствующих поставщиков.

Пользователь самостоятельно несёт ответственность за соблюдение применимого законодательства и условий использования соответствующих сервисов.

---

<a id="українська"></a>

## 🇺🇦 Українська

### Про проєкт

Цей репозиторій містить **JavaScript-плагіни для Lampa**.

Плагіни призначені для розширення можливостей Lampa, зокрема:

* додаткові джерела фільмів і серіалів;
* парсери відео;
* джерела прямих трансляцій;
* розширення програвача;
* функції, пов'язані із субтитрами;
* розширення інтерфейсу;
* інші функції, сумісні з Lampa.

Усі плагіни поширюються у вигляді JavaScript-файлів із розширенням `.js`.

### Вимоги до плагінів

Плагіни повинні відповідати архітектурі та правилам розробки плагінів Lampa.

Основні вимоги:

1. Файл плагіна повинен мати розширення `.js`.
2. Плагін повинен завантажуватися через механізм плагінів Lampa.
3. Не слід без потреби забруднювати глобальний простір імен.
4. За можливості необхідно використовувати API та механізми розширення Lampa.
5. Не слід змінювати функціональність Lampa, яка не пов'язана з роботою плагіна.
6. Бажано підтримувати актуальні версії Lampa.
7. Використання сторонніх залежностей повинно бути зазначене.
8. Назва, версія та призначення плагіна повинні бути зрозумілими.

### Рекомендована структура

Базовий плагін може мати таку структуру:

```javascript
(function () {
    'use strict';

    var plugin = {
        name: 'Plugin Name',
        version: '1.0.0'
    };

    // Код плагіна

})();
```

Якщо плагін використовує API Lampa, його ініціалізація повинна виконуватися відповідно до механізму плагінів Lampa.

### Назви файлів

Файли плагінів повинні закінчуватися на `.js`.

Наприклад:

```text
plugin-name.js
torrentio.js
live-sports.js
subtitle.js
video-parser.js
```

### Встановлення

Додайте URL JavaScript-файлу плагіна в налаштуваннях плагінів Lampa.

Наприклад:

```text
https://example.com/lampa/plugin-name.js
```

Після цього завантажте плагін через менеджер плагінів Lampa.

### Структура проєкту

Рекомендована структура:

```text
.
├── README.md
├── plugins/
│   ├── plugin-name.js
│   ├── torrentio.js
│   ├── live-sports.js
│   └── subtitle.js
└── LICENSE
```

Для невеликих проєктів `.js`-файли можна розміщувати безпосередньо в корені репозиторію.

### Відмова від відповідальності

Працездатність сторонніх вебсайтів, API, відеоресурсів та джерел субтитрів залежить від відповідних постачальників.

Користувач самостійно відповідає за дотримання чинного законодавства та умов використання відповідних сервісів.

---

## License

Please check the license included in this repository before using, modifying or redistributing the plugins.
