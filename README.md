# Lampa APK Auto-Builder

[English](#english) | [简体中文](#简体中文) | [Русский](#русский) | [Українська](#українська)

<!-- LATEST_BUILD_INFO_START -->
### 🚀 Latest Automated Build
- **App Version**: `v3.3.3.57`
- **Build Date**: `2026-09-14 16:55 (UTC+8)`
- **Upstream Source**: [0f50f0c](https://github.com/yumata/lampa/commit/0f50f0c4cb3f602ecaff84925dca07f96bbd38a8)
- **Direct Download**: [📦 lampa-v3.3.3.57.apk](https://github.com/aston314/Lampa-cordova/releases/download/v3.3.3.57/lampa-v3.3.3.57.apk)
<!-- LATEST_BUILD_INFO_END -->

<!-- RELATED_RELEASES_START -->
### 🌐 Related Lampa Community Builds

#### 📦 [lampa-app/LAMPA](https://github.com/lampa-app/LAMPA)
- **App Version**: `v1.13.1` (v1.13.1)
- **Release Date**: `2026-09-13 22:43 (UTC+8)`
- **Release Notes**: [View Details](https://github.com/lampa-app/LAMPA/releases/tag/v1.13.1)
- **Direct Download**: [📦 app-lite-release.apk](https://github.com/lampa-app/LAMPA/releases/download/v1.13.1/app-lite-release.apk)
<!-- RELATED_RELEASES_END -->

---

## 简体中文

基于 GitHub Actions 的全自动化 **[Lampa](https://github.com/yumata/lampa)** Android APK 同步构建流水线。

### 🌟 核心特性
- **自动监测上游更新**：每天定时检测 `yumata/lampa` 的代码提交；若无变动则自动跳过，节省构建资源。
- **自动化代码补丁**：自动注入 `cordova.js`、启动图自适应隐藏监听以及自定义方法替换。
- **集成核心原生插件**：支持外部播放器调用（Intent）、本地文件系统、HTTP 引擎、状态栏沉浸等。
- **深度兼容优化**：针对电视盒子与移动设备，锁定 Android SDK API Level 29（Android 10）与 Java 11。
- **自动递增版本号**：内部版本号 `versionCode` 随构建自动自增，设备端可**直接覆盖旧版无缝升级**。
- **已签名 Release 产物**：自动生成正规签名的 APK 安装包，支持在 [Releases](../../releases) 页面直接下载。

---

## English

An automated GitHub Actions pipeline for synchronizing, patching, and building **[Lampa](https://github.com/yumata/lampa)** into a native signed Android APK.

### 🌟 Key Features
- **Upstream Sync & Monitoring**: Checks `yumata/lampa` daily for changes and skips execution if no new commits exist.
- **Automated Patching**: Injects `cordova.js`, adaptive splash screen dismissal logic, and custom method replacements.
- **Native Plugin Integration**: Pre-configured with external player invocation (Intent), local file storage, HTTP requests, and status bar controls.
- **Optimized Compatibility**: Built targeting Android SDK API Level 29 (Android 10) on Java 11 for broad compatibility across TV boxes and mobile devices.
- **Automatic Version Incrementing**: Increases `versionCode` on every build to enable seamless in-place updates.
- **Signed Releases**: Delivers production-ready, signed APK binaries available directly on the [Releases](../../releases) page.

---

## Русский

Полностью автоматизированный конвейер GitHub Actions для синхронизации, адаптации и сборки приложения **[Lampa](https://github.com/yumata/lampa)** в подписанный Android APK.

### 🌟 Основные возможности
- **Отслеживание апстрима**: Ежедневный мониторинг изменений в `yumata/lampa` с автопропуском сборки при отсутствии обновлений.
- **Автоматические патчи**: Внедрение `cordova.js`, скрипта автоматического скрытия заставки и модификация исходных методов.
- **Нативные плагины**: Поддержка внешних видеоплееров (Intent), работы с файлами, HTTP-запросов и полноэкранного режима.
- **Совместимость с медиаприставками**: Сборка под Android SDK API Level 29 (Java 11) для стабильной работы на Android TV и ТВ-боксах.
- **Автоматический инкремент версий**: `versionCode` увеличивается при каждой сборке, что позволяет **устанавливать обновления поверх без удаления**.
- **Подписанные релизы**: Сборка полноценного подписанного APK с возможностью прямой загрузки из раздела [Releases](../../releases).

---

## Українська

Повністю автоматизований робочий процес GitHub Actions для синхронізації, патчингу та збірки **[Lampa](https://github.com/yumata/lampa)** у підписаний Android APK.

### 🌟 Особливості
- **Автоматичний моніторинг**: Щоденна перевірка репозиторію `yumata/lampa`; збірка пропускається, якщо нових комітів немає.
- **Впровадження патчів**: Автоматичне додавання `cordova.js`, обробника закриття заставки та заміна необхідних методів.
- **Нативні можливості**: Підтримка виклику зовнішніх відеоплеєрів (Intent), файлової системи, мережевих HTTP-запитів та повноекранного інтерфейсу.
- **Оптимізація для ТБ**: Складання під Android SDK API Level 29 (Java 11) для стабільної роботи на Smart TV та приставках.
- **Автоматичне зростання версій**: `versionCode` збільшується автоматично, забезпечуючи **безпроблемне оновлення поверх встановленої версії**.
- **Підписані релізи**: Готові до встановлення підписані `.apk` файли доступні для завантаження на сторінці [Releases](../../releases).
