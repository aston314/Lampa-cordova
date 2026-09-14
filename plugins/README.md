
# Lampa Plugins Directory Guide 🔌📦

[English](#english) | [简体中文](#简体中文) | [Русский](#русский) | [Українська](#українська)

---

## 简体中文

本目录用于管理 **Lampa Android TV 客户端** 的自定义插件库，支持 **本地离线插件（`.js`）** 与 **远程预装插件配置（`plugins.json`）** 两大体系。

### 📁 目录结构示例
```text
plugins/
├── plugins.json          # 远程插件预装配置表
├── my_plugin.js          # 本地离线插件 1
├── custom_source.js      # 本地离线插件 2
└── README.md             # 本说明文件
```

---

### 一、本地离线插件（`.js` 文件）
* **使用方式**：直接将第三方的 Lampa 插件（如在线源、评分插件等）以 **`.js`** 结尾的文件放入本目录。
* **自动生效机制**：
  1. GitHub Actions 打包时，会自动将所有 `.js` 文件固化编译进 APK 安装包内部；
  2. 脚本会自动在核心代码中完成注册加载；
  3. **优势**：开机即用、100% 离线秒开、免翻墙、彻底无视官方黑名单屏蔽。
* **规则注意**：
  * 文件名必须以 `.js` 结尾（建议使用纯英文/拼音，如 `online.js`）；
  * 隐藏文件（如 `.gitkeep`、`.DS_Store`）会自动被忽略，不会产生任何干扰。

---

### 二、远程在线插件配置（`plugins.json`）
* **使用方式**：在本目录下创建或编辑 **`plugins.json`**，用于配置开机时自动写入 Lampa 的在线网络插件（免去在电视上手动输入 URL）。
* **配置格式模板**：
```json
[
  {
    "name": "TMDB Proxy",
    "url": "http://cub.red/plugin/tmdb-proxy",
    "author": "CUB",
    "status": 1
  },
  {
    "name": "备用插件（暂不启用）",
    "url": "http://example.com/other-plugin.js",
    "author": "Example",
    "status": 0
  }
]
```
* **参数说明**：
  * **`status: 1`**：启用。打包时会自动读取并注入到客户端；
  * **`status: 0`**：停用。构建时自动跳过，仅作为配置冗余留存，方便随时开启。

---

## English

This directory manages custom plugins for the **Lampa Android TV client**, supporting both **local offline plugins (`.js`)** and **pre-installed remote plugin configurations (`plugins.json`)**.

### 📁 Directory Layout
```text
plugins/
├── plugins.json          # Remote plugin configuration list
├── my_plugin.js          # Local offline plugin 1
├── custom_source.js      # Local offline plugin 2
└── README.md             # This documentation
```

---

### 1. Local Offline Plugins (`.js` files)
* **Usage**: Place any valid third-party Lampa plugin file ending with **`.js`** directly into this folder.
* **Automation Mechanism**:
  1. GitHub Actions automatically bundles all `.js` files into the APK asset bundle during build;
  2. The build script automatically injects their registration into Lampa's plugin loader;
  3. **Advantages**: Zero-configuration on TV, 100% offline, zero network latency, completely immune to domain blacklists.
* **Rules**:
  * Files must end with `.js` (alphanumeric filenames recommended, e.g., `online.js`);
  * Hidden files (e.g., `.gitkeep`, `.DS_Store`) and non-JS files are safely ignored.

---

### 2. Pre-installed Remote Plugins (`plugins.json`)
* **Usage**: Create or edit **`plugins.json`** in this folder to specify remote plugin URLs that should be pre-installed into Lampa on startup (no manual URL typing on TV).
* **Configuration Format**:
```json
[
  {
    "name": "TMDB Proxy",
    "url": "http://cub.red/plugin/tmdb-proxy",
    "author": "CUB",
    "status": 1
  },
  {
    "name": "Backup Plugin (Disabled)",
    "url": "http://example.com/other-plugin.js",
    "author": "Example",
    "status": 0
  }
]
```
* **Parameters**:
  * **`status: 1`**: Enabled. Automatically injected into the app on startup;
  * **`status: 0`**: Disabled. Kept as redundant config without being loaded into the app.

---

## Русский

Эта папка предназначена для управления пользовательскими плагинами **клиента Lampa Android TV**. Поддерживаются как **локальные оффлайн-плагины (`.js`)**, так и **предустановленные удаленные плагины (`plugins.json`)**.

### 📁 Структура каталога
```text
plugins/
├── plugins.json          # Конфигурация удаленных плагинов
├── my_plugin.js          # Локальный оффлайн-плагин 1
├── custom_source.js      # Локальный оффлайн-плагин 2
└── README.md             # Данная инструкция
```

---

### 1. Локальные оффлайн-плагины (файлы `.js`)
* **Использование**: Поместите любой файл плагина с расширением **`.js`** прямо в эту папку.
* **Автоматическая сборка**:
  1. GitHub Actions автоматически компилирует и вшивает все `.js` файлы внутрь APK;
  2. Скрипт сборки автоматически регистрирует плагины в загрузчике Lampa;
  3. **Преимущества**: Готовность сразу после установки, 100% оффлайн, мгновенный запуск, полный обход любых черных списков.
* **Правила**:
  * Имя файла должно заканчиваться на `.js` (рекомендуются латинские символы, например `online.js`);
  * Скрытые файлы (`.gitkeep`, `.DS_Store`) автоматически игнорируются.

---

### 2. Предустановленные онлайн-плагины (`plugins.json`)
* **Использование**: Создайте или отредактируйте файл **`plugins.json`** в этой папке для автоматической установки плагинов по URL при первом запуске (без необходимости ввода длинных ссылок с пульта).
* **Шаблон конфигурации**:
```json
[
  {
    "name": "TMDB Proxy",
    "url": "http://cub.red/plugin/tmdb-proxy",
    "author": "CUB",
    "status": 1
  },
  {
    "name": "Резервный плагин (отключен)",
    "url": "http://example.com/other-plugin.js",
    "author": "Example",
    "status": 0
  }
]
```
* **Параметры**:
  * **`status: 1`**: Включен. Автоматически вшивается и активируется в приложении;
  * **`status: 0`**: Отключен. Остается в конфигурации как резерв, не загружаясь в приложение.

---

## Українська

Цей каталог призначений для керування користувацькими плагінами **клієнта Lampa Android TV**. Підтримуються як **локальні офлайн-плагіни (`.js`)**, так і **попередньо встановлені віддалені плагіни (`plugins.json`)**.

### 📁 Структура каталогу
```text
plugins/
├── plugins.json          # Конфігурація віддалених плагінів
├── my_plugin.js          # Локальний офлайн-плагін 1
├── custom_source.js      # Локальний офлайн-плагін 2
└── README.md             # Ця інструкція
```

---

### 1. Локальні офлайн-плагіни (файли `.js`)
* **Використання**: Помістіть будь-який файл плагіна з розширенням **`.js`** безпосередньо в цю папку.
* **Механізм автоматизації**:
  1. GitHub Actions автоматично вшиває всі файли `.js` всередину APK-пакета під час збірки;
  2. Скрипт автоматично додає їх до списку реєстрації плагінів Lampa;
  3. **Переваги**: Працює одразу після встановлення, 100% офлайн, миттєве завантаження, повний імунітет до блокувань у чорних списках.
* **Правила**:
  * Файл обов'язково повинен мати розширення `.js` (рекомендується латиниця, наприклад `online.js`);
  * Приховані файли (`.gitkeep`, `.DS_Store`) автоматично ігноруються.

---

### 2. Попередньо встановлені онлайн-плагіни (`plugins.json`)
* **Використання**: Створіть або відредагуйте файл **`plugins.json`** у цій папці для автоматичного завантаження мережевих плагінів за URL під час запуску (без потреби вводити довгі адреси пультом телевізора).
* **Формат конфігурації**:
```json
[
  {
    "name": "TMDB Proxy",
    "url": "http://cub.red/plugin/tmdb-proxy",
    "author": "CUB",
    "status": 1
  },
  {
    "name": "Резервний плагін (вимкнено)",
    "url": "http://example.com/other-plugin.js",
    "author": "Example",
    "status": 0
  }
]
```
* **Параметри**:
  * **`status: 1`**: Увімкнено. Автоматично зчитується та впроваджується в застосунок;
  * **`status: 0`**: Вимкнено. Зберігається як надлишкова конфігурація без завантаження в застосунок.
```
