from __future__ import annotations

from collections.abc import Mapping

from PyQt6.QtCore import QSettings


class SettingsKeys:
    OPTION_IGNORE_MOUSE_STOPS = "options/ignore_mouse_stops"
    OPTION_COLORFUL_SCHEME = "options/colorful_scheme"
    OPTION_USE_DESKTOP_BACKGROUND = "options/use_desktop_background"
    OPTION_USE_MULTIPLE_MONITORS = "options/use_multiple_monitors"
    OPTION_AUTOMATIC_UPDATE = "options/automatic_update"
    OPTION_LAST_SAVE_DIR = "options/last_save_dir"
    OPTION_LANGUAGE = "options/language"

    UPDATE_LAST_DOWNLOADED_PATH = "updates/last_downloaded_path"
    UPDATE_LAST_DOWNLOADED_VERSION = "updates/last_downloaded_version"
    UPDATE_LAST_AUTO_DOWNLOADED_VERSION = "updates/last_auto_downloaded_version"
    UPDATE_LAST_PROMPTED_VERSION = "updates/last_prompted_version"
    UPDATE_INSTALL_IGNORE_COUNT = "updates/install_ignore_count"

    PROMPT_FIRST_IMAGE_SAVE_SHOWN = "donate_prompt/first_image_saved_shown"
    PROMPT_FIRST_RAW_SAVE_SHOWN = "donate_prompt/first_raw_saved_shown"


class AppSettings:
    """Thin typed wrapper around QSettings with backward-compatible methods."""

    def __init__(self, organization: str = "iographica", application: str = "IOGraphPython") -> None:
        self._settings = QSettings(organization, application)

    # Compatibility layer for existing call sites.
    def value(self, key: str, default=None, value_type=None):
        if value_type is None:
            return self._settings.value(key, default)
        return self._settings.value(key, default, value_type)

    def setValue(self, key: str, value) -> None:
        self._settings.setValue(key, value)

    def remove(self, key: str) -> None:
        self._settings.remove(key)

    def sync(self) -> None:
        self._settings.sync()

    # Typed helpers for new/refactored code.
    def get_bool(self, key: str, default: bool = False) -> bool:
        return bool(self._settings.value(key, default, bool))

    def get_int(self, key: str, default: int = 0) -> int:
        return int(self._settings.value(key, default, int))

    def get_str(self, key: str, default: str = "") -> str:
        return str(self._settings.value(key, default, str))

    def set(self, key: str, value, *, sync: bool = True) -> None:
        self._settings.setValue(key, value)
        if sync:
            self._settings.sync()

    def set_many(self, values: Mapping[str, object], *, sync: bool = True) -> None:
        for key, value in values.items():
            self._settings.setValue(key, value)
        if sync:
            self._settings.sync()

    def remove_many(self, keys: list[str], *, sync: bool = True) -> None:
        for key in keys:
            self._settings.remove(key)
        if sync:
            self._settings.sync()
