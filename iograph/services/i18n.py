from __future__ import annotations

from .settings import AppSettings, SettingsKeys


class I18nService:
    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = ("en", "ru")

    _RU_TRANSLATIONS = {
        "Check for Updates": "Проверить обновления",
        "Checking for Updates...": "Проверка обновлений...",
        "Downloading Update...": "Загрузка обновления...",
        "Install Downloaded Update": "Установить загруженное обновление",
        "Hide Settings": "Скрыть настройки",
        "Show Settings": "Показать настройки",
    }

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._language = self._normalize_language(
            self._settings.get_str(SettingsKeys.OPTION_LANGUAGE, self.DEFAULT_LANGUAGE)
        )

    @classmethod
    def _normalize_language(cls, code: str) -> str:
        normalized = (code or "").strip().lower()
        if normalized in cls.SUPPORTED_LANGUAGES:
            return normalized
        return cls.DEFAULT_LANGUAGE

    def current_language(self) -> str:
        return self._language

    def set_language(self, code: str) -> str:
        self._language = self._normalize_language(code)
        self._settings.set(SettingsKeys.OPTION_LANGUAGE, self._language, sync=True)
        return self._language

    def tr(self, source_text: str) -> str:
        if self._language == "ru":
            return self._RU_TRANSLATIONS.get(source_text, source_text)
        return source_text
