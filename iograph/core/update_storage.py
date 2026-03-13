from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys

from PyQt6.QtCore import QStandardPaths

from ..services.settings import AppSettings, SettingsKeys
from .update_service import UpdateService


class UpdateStorageManager:
    def __init__(self, settings: AppSettings, staging_ttl_seconds: int) -> None:
        self._settings = settings
        self._staging_ttl_seconds = int(staging_ttl_seconds)

    @staticmethod
    def normalize_version_tag(version: str) -> str:
        v = str(version).replace("\ufeff", "").strip()
        if v.lower().startswith("v"):
            return v[1:]
        return v

    def cleanup_downloaded_update_if_installed(self, app_version: str) -> None:
        self.cleanup_stale_update_temp_files()
        downloaded = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION, "", str)
        if not downloaded:
            return
        current = self.normalize_version_tag(app_version)
        target = self.normalize_version_tag(downloaded)
        current_key = UpdateService.version_key(current)
        target_key = UpdateService.version_key(target)
        if current_key is None or target_key is None or current_key < target_key:
            return
        path = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)
        if path:
            p = Path(path)
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH)
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION)
        self._settings.remove(SettingsKeys.UPDATE_LAST_AUTO_DOWNLOADED_VERSION)
        self._settings.remove(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT)

    def update_target_path(self, asset_name: str, latest_version: str, manual: bool) -> Path:
        if manual:
            downloads = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            target_dir = Path(downloads) if downloads else (Path.home() / "Downloads")
            target_dir.mkdir(parents=True, exist_ok=True)
            base = target_dir / asset_name
            if not base.exists():
                return base
            stem, suffix = base.stem, base.suffix
            return target_dir / f"{stem}-{latest_version}{suffix}"
        target_dir = self.updates_cache_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / self.auto_update_cache_name(asset_name, latest_version)

    def updates_cache_dir(self) -> Path:
        appdata = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        if not appdata:
            appdata = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if appdata:
            return Path(appdata) / "updates"
        return Path.home() / ".iograph" / "updates"

    @staticmethod
    def cleanup_partial_update_files(target_dir: Path, asset_name: str) -> None:
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return
        stem = Path(asset_name).stem
        for part in target_dir.glob(f"{stem}*.part"):
            try:
                if part.is_file():
                    part.unlink()
            except Exception:
                pass

    def clear_stale_download_metadata_for(self, latest_version: str) -> None:
        target_tag = f"v{latest_version}"
        stored_tag = str(self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION, "", str)).strip()
        if not stored_tag:
            return
        if self.normalize_version_tag(stored_tag) == self.normalize_version_tag(target_tag):
            return
        previous_path = str(self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)).strip()
        if previous_path:
            p = Path(previous_path)
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH)
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION)
        self._settings.remove(SettingsKeys.UPDATE_LAST_AUTO_DOWNLOADED_VERSION)
        self._settings.remove(SettingsKeys.UPDATE_LAST_PROMPTED_VERSION)
        self._settings.remove(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT)

    def cleanup_stale_update_temp_files(self) -> None:
        updates_dir = self.updates_cache_dir()
        if not updates_dir.exists():
            return
        now = datetime.now().timestamp()
        for part in updates_dir.glob("*.part"):
            try:
                if part.is_file():
                    part.unlink()
            except Exception:
                pass
        for staging in updates_dir.glob("iograph-update-*"):
            try:
                if not staging.is_dir():
                    continue
                age = now - staging.stat().st_mtime
                if age >= self._staging_ttl_seconds:
                    shutil.rmtree(staging, ignore_errors=True)
            except Exception:
                pass

    @staticmethod
    def auto_update_cache_name(asset_name: str, latest_version: str) -> str:
        suffix = Path(asset_name).suffix.lower()
        if not suffix:
            suffix = ".bin"
        safe_version = re.sub(r"[^0-9A-Za-z._-]", "-", str(latest_version).strip())
        safe_version = safe_version or "unknown"
        if sys.platform.startswith("win"):
            return f"IOGraph-windows-v{safe_version}{suffix}"
        if sys.platform == "darwin":
            return f"IOGraph-macos-v{safe_version}{suffix}"
        return f"IOGraph-linux-v{safe_version}{suffix}"

    def has_pending_downloaded_update(self) -> bool:
        path = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)
        return bool(path and Path(path).exists())

    def pending_downloaded_update_path(self) -> Path | None:
        path = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)
        if not path:
            return None
        p = Path(path)
        return p if p.exists() else None

    def is_latest_update_already_downloaded(self, latest_tag: str) -> tuple[bool, bool]:
        downloaded_tag = str(self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION, "", str)).strip()
        if not downloaded_tag:
            return (False, False)
        if self.normalize_version_tag(downloaded_tag) != self.normalize_version_tag(latest_tag):
            return (False, False)
        path = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)
        if path and Path(path).exists():
            return (True, False)
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH)
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION)
        return (False, True)

    def register_download_result(self, local_path: Path, latest_version: str, manual: bool) -> None:
        tagged_version = f"v{latest_version}"
        previous_path_raw = str(self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)).strip()
        previous_version = str(self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION, "", str)).strip()
        if previous_path_raw and previous_path_raw != str(local_path) and previous_version != tagged_version:
            old_path = Path(previous_path_raw)
            try:
                if old_path.exists():
                    old_path.unlink()
            except Exception:
                pass
        self._settings.setValue(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, str(local_path))
        self._settings.setValue(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION, tagged_version)
        self._settings.setValue(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT, 0)
        if not manual:
            self._settings.setValue(SettingsKeys.UPDATE_LAST_AUTO_DOWNLOADED_VERSION, tagged_version)
            self._settings.setValue(SettingsKeys.UPDATE_LAST_PROMPTED_VERSION, tagged_version)

    def reset_install_ignore_count(self) -> None:
        self._settings.setValue(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT, 0)

    def increment_install_ignore_count(self) -> int:
        ignored = int(self._settings.value(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT, 0, int)) + 1
        self._settings.setValue(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT, ignored)
        return ignored

    def clear_missing_download_file_state(self) -> None:
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH)
        self._settings.remove(SettingsKeys.UPDATE_LAST_DOWNLOADED_VERSION)
        self._settings.remove(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT)
