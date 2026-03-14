from __future__ import annotations

from PyQt6.QtCore import QLocale

from .settings import AppSettings, SettingsKeys


class I18nService:
    AUTO_MODE = "auto"
    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = (
        "en",
        "de",
        "fr",
        "es",
        "ru",
        "uk",
        "tr",
        "ar",
        "zh-Hans",
        "zh-Hant",
    )

    LANGUAGE_LABELS = {
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "es": "Español",
        "ru": "Русский",
        "uk": "Українська",
        "tr": "Türkçe",
        "ar": "العربية",
        "zh-Hans": "简体中文",
        "zh-Hant": "繁體中文",
    }

    _TRANSLATIONS = {
        "de": {
            "Language": "Sprache",
            "Auto (System)": "Automatisch (System)",
            "Hide Settings": "Einstellungen ausblenden",
            "Show Settings": "Einstellungen anzeigen",
            "Check for Updates": "Nach Updates suchen",
            "Checking for Updates...": "Suche nach Updates...",
            "Downloading Update...": "Update wird heruntergeladen...",
        },
        "fr": {
            "Language": "Langue",
            "Auto (System)": "Automatique (Système)",
            "Hide Settings": "Masquer les réglages",
            "Show Settings": "Afficher les réglages",
            "Check for Updates": "Vérifier les mises à jour",
            "Checking for Updates...": "Vérification des mises à jour...",
            "Downloading Update...": "Téléchargement de la mise à jour...",
        },
        "es": {
            "Language": "Idioma",
            "Auto (System)": "Automático (Sistema)",
            "Hide Settings": "Ocultar ajustes",
            "Show Settings": "Mostrar ajustes",
            "Check for Updates": "Buscar actualizaciones",
            "Checking for Updates...": "Buscando actualizaciones...",
            "Downloading Update...": "Descargando actualización...",
        },
        "ru": {
            "Language": "Язык",
            "Auto (System)": "Авто (системный)",
            "Hide Settings": "Скрыть настройки",
            "Show Settings": "Показать настройки",
            "Check for Updates": "Проверить обновления",
            "Checking for Updates...": "Проверка обновлений...",
            "Downloading Update...": "Загрузка обновления...",
        },
        "uk": {
            "Language": "Мова",
            "Auto (System)": "Авто (системна)",
            "Hide Settings": "Сховати налаштування",
            "Show Settings": "Показати налаштування",
            "Check for Updates": "Перевірити оновлення",
            "Checking for Updates...": "Перевірка оновлень...",
            "Downloading Update...": "Завантаження оновлення...",
        },
        "tr": {
            "Language": "Dil",
            "Auto (System)": "Otomatik (Sistem)",
            "Hide Settings": "Ayarları Gizle",
            "Show Settings": "Ayarları Göster",
            "Check for Updates": "Güncellemeleri Denetle",
            "Checking for Updates...": "Güncellemeler denetleniyor...",
            "Downloading Update...": "Güncelleme indiriliyor...",
        },
        "ar": {
            "Language": "اللغة",
            "Auto (System)": "تلقائي (النظام)",
            "Hide Settings": "إخفاء الإعدادات",
            "Show Settings": "إظهار الإعدادات",
            "Check for Updates": "التحقق من التحديثات",
            "Checking for Updates...": "جارٍ التحقق من التحديثات...",
            "Downloading Update...": "جارٍ تنزيل التحديث...",
        },
        "zh-Hans": {
            "Language": "语言",
            "Auto (System)": "自动（系统）",
            "Hide Settings": "隐藏设置",
            "Show Settings": "显示设置",
            "Check for Updates": "检查更新",
            "Checking for Updates...": "正在检查更新...",
            "Downloading Update...": "正在下载更新...",
        },
        "zh-Hant": {
            "Language": "語言",
            "Auto (System)": "自動（系統）",
            "Hide Settings": "隱藏設定",
            "Show Settings": "顯示設定",
            "Check for Updates": "檢查更新",
            "Checking for Updates...": "正在檢查更新...",
            "Downloading Update...": "正在下載更新...",
        },
    }

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._mode = self._normalize_mode(
            self._settings.get_str(SettingsKeys.OPTION_LANGUAGE, self.AUTO_MODE)
        )

    @classmethod
    def _normalize_mode(cls, mode: str) -> str:
        normalized = (mode or "").strip()
        if normalized == cls.AUTO_MODE:
            return normalized
        if normalized in cls.SUPPORTED_LANGUAGES:
            return normalized
        lower = normalized.lower()
        if lower in cls.SUPPORTED_LANGUAGES:
            return lower
        return cls.AUTO_MODE

    def current_mode(self) -> str:
        return self._mode

    def set_language_mode(self, mode: str) -> str:
        self._mode = self._normalize_mode(mode)
        self._settings.set(SettingsKeys.OPTION_LANGUAGE, self._mode, sync=True)
        return self._mode

    def effective_language(self) -> str:
        if self._mode != self.AUTO_MODE:
            return self._mode
        return self._resolve_system_language()

    def language_menu_options(self) -> list[tuple[str, str]]:
        options = [(self.AUTO_MODE, self.tr("Auto (System)"))]
        for code in self.SUPPORTED_LANGUAGES:
            options.append((code, self.LANGUAGE_LABELS.get(code, code)))
        return options

    @classmethod
    def _resolve_system_language(cls) -> str:
        locale = QLocale.system()
        bcp47 = (locale.bcp47Name() or "").strip()
        if bcp47.lower().startswith("zh-hant"):
            return "zh-Hant"
        if bcp47.lower().startswith("zh-hans"):
            return "zh-Hans"
        name = (locale.name() or "").strip().lower().replace("-", "_")
        if name.startswith("zh_tw") or name.startswith("zh_hk") or name.startswith("zh_mo"):
            return "zh-Hant"
        if name.startswith("zh_"):
            return "zh-Hans"
        base = (bcp47.split("-", 1)[0] or name.split("_", 1)[0]).lower()
        if base in cls.SUPPORTED_LANGUAGES:
            return base
        return cls.DEFAULT_LANGUAGE

    def tr(self, source_text: str) -> str:
        lang = self.effective_language()
        return self._TRANSLATIONS.get(lang, {}).get(source_text, source_text)
