from __future__ import annotations


class SessionRestoreDecisions:
    @staticmethod
    def should_try_preview_cache(payload: dict, use_cache: bool) -> bool:
        return bool(use_cache and payload.get("preview_cache_saved", False))

    @staticmethod
    def should_try_desktop_cache(payload: dict, use_cache: bool, use_desktop_background: bool) -> bool:
        return bool(use_cache and use_desktop_background and payload.get("desktop_cache_saved", False))

    @staticmethod
    def needs_preview_rerender(loaded_preview_cache: bool) -> bool:
        return not loaded_preview_cache

    @staticmethod
    def needs_desktop_refresh(use_desktop_background: bool, loaded_desktop_cache: bool) -> bool:
        return bool(use_desktop_background and not loaded_desktop_cache)
