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

本项目中的插件会由 **Cordova** 在构建 Lampa 本地版本时自动打包，并作为 Lampa 的本地插件运行。

所有插件文件必须放置在项目的 `plugins/` 目录中。

### 插件目录

插件统一存放于：

```text
plugins/
```

例如：

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── torrentio.js
    ├── live-sports.js
    ├── subtitle.js
    └── video-parser.js
```

**`.js` 插件文件不能直接放在项目根目录。**

### 自动打包

Cordova 构建项目时，会自动读取 `plugins/` 目录中的所有 `.js` 文件，并将这些文件打包到 Lampa 本地版本中。

因此：

* `plugins/` 目录下的 `.js` 文件会自动被打包。
* 不需要单独注册每一个插件。
* 不需要手动添加插件 URL。
* 打包完成后，插件作为 Lampa 本地插件运行。
* `plugins/` 中的非 `.js` 文件不会作为插件加载。

### 插件要求

插件必须符合 Lampa 的插件加载方式和 JavaScript 编写规范。

基本要求：

1. 插件文件必须使用 `.js` 扩展名。
2. 所有插件必须放在 `plugins/` 目录中。
3. 插件应能够通过 Lampa 的插件机制正常加载。
4. 插件代码应尽量避免污染全局命名空间。
5. 插件应使用 Lampa 提供的 API 和扩展机制。
6. 不应修改与插件功能无关的 Lampa 核心代码。
7. 插件应尽可能兼容当前版本的 Lampa。
8. 插件中使用的第三方依赖应明确说明。
9. 插件名称、版本及主要功能应在代码中清晰定义。

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

插件文件必须以 `.js` 结尾，并且必须放置在 `plugins/` 目录中。

推荐：

```text
plugins/
├── torrentio.js
├── live-sports.js
├── subtitle.js
└── video-parser.js
```

不推荐：

```text
torrentio
torrentio.txt
torrentio.json
torrentio.md
```

也不要将插件直接放在项目根目录：

```text
./torrentio.js
./live-sports.js
```

### 安装

本项目用于 **Lampa Cordova 本地版本**。

无需通过 Lampa 在线插件地址逐个安装插件。

只需要将插件 `.js` 文件放入：

```text
plugins/
```

目录。

在 Cordova 构建 Lampa 时，`plugins/` 目录中的所有 `.js` 文件会自动被打包到本地版本。

因此，安装插件的过程实际上就是将对应的 `.js` 文件放入 `plugins/` 目录，然后重新构建 Lampa。

### 更新插件

更新插件时，不需要修改其他配置。

只需要将对应插件的新 `.js` 文件放入：

```text
plugins/
```

目录，并替换原来的插件文件。

例如原来：

```text
plugins/
└── torrentio.js
```

更新后仍然使用：

```text
plugins/
└── torrentio.js
```

直接用新的 `torrentio.js` 替换旧文件即可。

然后重新进行 Cordova 构建，新版本插件就会被自动打包到 Lampa 本地版本中。

### 添加新插件

如果需要添加新的 Lampa 插件，只需要在 `plugins/` 目录中增加新的 `.js` 文件。

例如：

```text
plugins/
├── torrentio.js
├── live-sports.js
├── subtitle.js
├── video-parser.js
└── new-plugin.js
```

重新构建后，新的 `new-plugin.js` 会自动被打包。

### 删除插件

如果需要删除插件，只需要从 `plugins/` 目录删除对应的 `.js` 文件。

例如删除：

```text
plugins/
└── torrentio.js
```

重新构建后，该插件将不会再被打包到 Lampa 本地版本。

### 项目结构

标准项目结构如下：

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── plugin-name.js
    ├── torrentio.js
    ├── live-sports.js
    └── subtitle.js
```

**项目根目录只用于存放项目文件，Lampa 插件 `.js` 文件统一存放在 `plugins/` 目录。**

### 注意事项

本项目中的插件用于扩展 Lampa 的功能。

插件所依赖的第三方网站、API、视频源、直播源、字幕源等内容，其可用性由对应服务提供方决定。

使用插件时，请遵守所在国家或地区的法律法规，以及相关网站和服务的使用条款。

---

<a id="english"></a>

## 🇬🇧 English

### About

This repository contains **JavaScript plugins for Lampa**.

The plugins are automatically packaged by **Cordova** when building the local Lampa version and are then loaded as local Lampa plugins.

All plugin files must be placed in the `plugins/` directory.

### Plugin Directory

All plugins must be stored in:

```text
plugins/
```

Example:

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── torrentio.js
    ├── live-sports.js
    ├── subtitle.js
    └── video-parser.js
```

**Plugin `.js` files must not be placed in the repository root.**

### Automatic Packaging

When the Cordova project is built, all `.js` files inside the `plugins/` directory are automatically included in the local Lampa build.

Therefore:

* All `.js` files inside `plugins/` are automatically packaged.
* No individual plugin registration is required.
* No plugin URL needs to be added manually.
* Plugins run as local Lampa plugins after packaging.
* Non-JavaScript files inside `plugins/` are not loaded as plugins.

### Plugin Requirements

Plugins should follow the Lampa plugin architecture and JavaScript conventions.

General requirements:

1. Plugin files must use the `.js` extension.
2. All plugins must be placed inside `plugins/`.
3. Plugins should load correctly through the Lampa plugin mechanism.
4. Avoid unnecessary global variables.
5. Use Lampa APIs and extension mechanisms whenever possible.
6. Do not modify unrelated Lampa core functionality.
7. Maintain compatibility with current Lampa versions whenever possible.
8. Clearly document third-party dependencies.
9. Plugin name, version and main functionality should be clearly defined.

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

### Installation

This repository is intended for the **local Lampa Cordova build**.

Plugins do not need to be installed individually through Lampa's online plugin URL system.

Simply place the plugin `.js` file inside:

```text
plugins/
```

When Cordova builds Lampa, all `.js` files in this directory are automatically packaged into the local Lampa version.

### Updating Plugins

To update a plugin, simply place the new `.js` file in the `plugins/` directory and replace the existing file.

For example:

```text
plugins/
└── torrentio.js
```

Replace the existing `torrentio.js` with the new version and rebuild the Cordova project.

The updated plugin will then be automatically included in the local Lampa build.

### Adding a New Plugin

To add a new plugin, simply add a new `.js` file to the `plugins/` directory:

```text
plugins/
├── torrentio.js
├── live-sports.js
├── subtitle.js
├── video-parser.js
└── new-plugin.js
```

The new plugin will be automatically packaged during the next build.

### Removing a Plugin

To remove a plugin, delete its `.js` file from the `plugins/` directory.

After rebuilding the project, the removed plugin will no longer be included.

### Project Structure

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── plugin-name.js
    ├── torrentio.js
    ├── live-sports.js
    └── subtitle.js
```

**The repository root is reserved for project files. All Lampa plugin `.js` files must be stored in `plugins/`.**

### Disclaimer

The availability of third-party websites, APIs, video sources, live streams and subtitle sources depends on their respective providers.

Users are responsible for complying with applicable laws, regulations and service terms.

---

<a id="русский"></a>

## 🇷🇺 Русский

### О проекте

Этот репозиторий содержит **JavaScript-плагины для Lampa**.

При сборке локальной версии Lampa с помощью **Cordova** все плагины автоматически включаются в сборку и работают как локальные плагины Lampa.

Все файлы плагинов должны находиться в каталоге `plugins/`.

### Каталог плагинов

Все плагины необходимо размещать в:

```text
plugins/
```

Например:

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── torrentio.js
    ├── live-sports.js
    ├── subtitle.js
    └── video-parser.js
```

**Файлы `.js` плагинов нельзя размещать непосредственно в корне репозитория.**

### Автоматическая сборка

При сборке проекта Cordova все файлы `.js`, находящиеся в каталоге `plugins/`, автоматически включаются в локальную версию Lampa.

Поэтому:

* все `.js` из `plugins/` автоматически добавляются в сборку;
* отдельная регистрация каждого плагина не требуется;
* вручную добавлять URL плагинов не нужно;
* после сборки плагины работают как локальные плагины Lampa;
* файлы других форматов не загружаются как плагины.

### Требования к плагинам

Плагины должны соответствовать архитектуре и правилам разработки плагинов Lampa.

Основные требования:

1. Файл плагина должен иметь расширение `.js`.
2. Все плагины должны находиться в каталоге `plugins/`.
3. Плагин должен корректно загружаться через механизм плагинов Lampa.
4. Следует избегать ненужного загрязнения глобального пространства имён.
5. По возможности необходимо использовать API Lampa.
6. Не следует изменять функции Lampa, не связанные с работой плагина.
7. Желательно поддерживать актуальные версии Lampa.
8. Сторонние зависимости должны быть указаны.
9. Название, версия и назначение плагина должны быть понятны.

### Установка

Этот репозиторий предназначен для **локальной версии Lampa на базе Cordova**.

Не требуется устанавливать плагины по отдельности через URL.

Поместите файл `.js` в:

```text
plugins/
```

При следующей сборке Cordova все `.js`-файлы из этого каталога автоматически попадут в локальную версию Lampa.

### Обновление

Для обновления плагина достаточно поместить новый `.js`-файл в каталог `plugins/` и заменить старый файл.

Например:

```text
plugins/
└── torrentio.js
```

Замените существующий `torrentio.js` новой версией и повторно выполните сборку Cordova.

Новая версия автоматически попадёт в локальную сборку Lampa.

### Добавление нового плагина

Чтобы добавить новый плагин, достаточно добавить новый `.js`-файл в каталог `plugins/`:

```text
plugins/
├── torrentio.js
├── live-sports.js
├── subtitle.js
├── video-parser.js
└── new-plugin.js
```

При следующей сборке новый плагин будет автоматически включён.

### Удаление плагина

Чтобы удалить плагин, удалите соответствующий `.js`-файл из каталога `plugins/`.

После повторной сборки этот плагин больше не будет включён в Lampa.

### Структура проекта

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── plugin-name.js
    ├── torrentio.js
    ├── live-sports.js
    └── subtitle.js
```

**Корень репозитория предназначен для файлов проекта. Все `.js`-файлы плагинов Lampa должны находиться в каталоге `plugins/`.**

### Отказ от ответственности

Работоспособность сторонних веб-сайтов, API, видеоресурсов, прямых трансляций и источников субтитров зависит от соответствующих поставщиков.

Пользователь самостоятельно отвечает за соблюдение применимого законодательства и условий использования соответствующих сервисов.

---

<a id="українська"></a>

## 🇺🇦 Українська

### Про проєкт

Цей репозиторій містить **JavaScript-плагіни для Lampa**.

Під час створення локальної версії Lampa за допомогою **Cordova** усі плагіни автоматично додаються до збірки та працюють як локальні плагіни Lampa.

Усі файли плагінів повинні знаходитися в каталозі `plugins/`.

### Каталог плагінів

Усі плагіни потрібно розміщувати в:

```text
plugins/
```

Наприклад:

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── torrentio.js
    ├── live-sports.js
    ├── subtitle.js
    └── video-parser.js
```

**Файли `.js` плагінів не можна розміщувати безпосередньо в корені репозиторію.**

### Автоматичне пакування

Під час збирання проєкту Cordova усі файли `.js` у каталозі `plugins/` автоматично додаються до локальної версії Lampa.

Тому:

* усі `.js` у `plugins/` автоматично пакуються;
* окрема реєстрація кожного плагіна не потрібна;
* не потрібно вручну додавати URL плагінів;
* після збирання плагіни працюють як локальні плагіни Lampa;
* файли інших форматів не завантажуються як плагіни.

### Вимоги до плагінів

Плагіни повинні відповідати архітектурі та правилам розробки плагінів Lampa.

Основні вимоги:

1. Файл плагіна повинен мати розширення `.js`.
2. Усі плагіни повинні знаходитися в каталозі `plugins/`.
3. Плагін повинен коректно завантажуватися через механізм плагінів Lampa.
4. Не слід без потреби забруднювати глобальний простір імен.
5. За можливості необхідно використовувати API Lampa.
6. Не слід змінювати функціональність Lampa, яка не пов'язана з роботою плагіна.
7. Бажано підтримувати актуальні версії Lampa.
8. Сторонні залежності повинні бути зазначені.
9. Назва, версія та призначення плагіна повинні бути зрозумілими.

### Встановлення

Цей репозиторій призначений для **локальної версії Lampa на базі Cordova**.

Немає необхідності встановлювати плагіни окремо через URL.

Помістіть файл `.js` у:

```text
plugins/
```

Під час наступної збірки Cordova усі `.js`-файли з цього каталогу автоматично потраплять до локальної версії Lampa.

### Оновлення

Щоб оновити плагін, достатньо помістити новий `.js`-файл у каталог `plugins/` та замінити старий файл.

Наприклад:

```text
plugins/
└── torrentio.js
```

Замініть існуючий `torrentio.js` новою версією та повторно виконайте збірку Cordova.

Нова версія автоматично потрапить до локальної збірки Lampa.

### Додавання нового плагіна

Щоб додати новий плагін, достатньо додати новий `.js`-файл до каталогу `plugins/`:

```text
plugins/
├── torrentio.js
├── live-sports.js
├── subtitle.js
├── video-parser.js
└── new-plugin.js
```

Під час наступної збірки новий плагін буде автоматично доданий.

### Видалення плагіна

Щоб видалити плагін, видаліть відповідний `.js`-файл із каталогу `plugins/`.

Після повторної збірки цей плагін більше не буде включений до Lampa.

### Структура проєкту

```text
.
├── README.md
├── LICENSE
└── plugins/
    ├── plugin-name.js
    ├── torrentio.js
    ├── live-sports.js
    └── subtitle.js
```

**Корінь репозиторію призначений для файлів проєкту. Усі `.js`-файли плагінів Lampa повинні знаходитися в каталозі `plugins/`.**

### Відмова від відповідальності

Працездатність сторонніх вебсайтів, API, відеоресурсів, прямих трансляцій та джерел субтитрів залежить від відповідних постачальників.

Користувач самостійно відповідає за дотримання чинного законодавства та умов використання відповідних сервісів.

---

## License

Please check the license included in this repository before using, modifying or redistributing the plugins.
