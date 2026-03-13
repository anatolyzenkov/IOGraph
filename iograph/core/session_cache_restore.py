from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .session_restore_decisions import SessionRestoreDecisions


@dataclass(frozen=True)
class SessionCacheRestoreResult:
    loaded_preview_cache: bool
    loaded_desktop_cache: bool


def restore_session_caches(
    *,
    payload: dict,
    use_cache: bool,
    use_desktop_background: bool,
    preview_cache_path: Path,
    desktop_cache_path: Path,
    load_preview_cache,
    load_desktop_cache,
) -> SessionCacheRestoreResult:
    loaded_preview_cache = False
    loaded_desktop_cache = False

    if SessionRestoreDecisions.should_try_preview_cache(payload, use_cache):
        loaded_preview_cache = load_preview_cache(str(preview_cache_path))
    elif payload.get("preview_cache_saved", False):
        # Signature can drift across restarts while cached image remains perfectly reusable by size.
        loaded_preview_cache = load_preview_cache(str(preview_cache_path))

    if SessionRestoreDecisions.should_try_desktop_cache(payload, use_cache, use_desktop_background):
        loaded_desktop_cache = load_desktop_cache(str(desktop_cache_path))
    elif use_desktop_background and payload.get("desktop_cache_saved", False):
        # Prefer already saved snapshot when geometry still matches; recapture only as fallback.
        loaded_desktop_cache = load_desktop_cache(str(desktop_cache_path))

    return SessionCacheRestoreResult(
        loaded_preview_cache=loaded_preview_cache,
        loaded_desktop_cache=loaded_desktop_cache,
    )
