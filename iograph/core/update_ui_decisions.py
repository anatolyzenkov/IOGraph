from __future__ import annotations

from pathlib import Path
import sys


class UpdateUiDecisions:
    @staticmethod
    def is_zip_update(path: Path | None) -> bool:
        return path is not None and path.suffix.lower() == ".zip"

    @classmethod
    def already_downloaded_prompt(cls, path: Path | None, *, tr=lambda s: s) -> str:
        if cls.is_zip_update(path):
            return tr("update.prompt.already_downloaded_open_package")
        return tr("update.prompt.already_downloaded_close_install")

    @classmethod
    def install_ready_prompt(cls, path: Path | None, *, tr=lambda s: s) -> str:
        is_zip = cls.is_zip_update(path)
        if is_zip and sys.platform == "darwin":
            return tr("update.prompt.ready_close_install")
        if is_zip:
            return tr("update.prompt.downloaded_open_package")
        return tr("update.prompt.ready_close_install")

    @classmethod
    def install_action_label(cls, path: Path | None, *, tr=lambda s: s) -> str:
        if cls.is_zip_update(path) and sys.platform == "darwin":
            return tr("update.install.action.install_downloaded_ellipsis")
        if cls.is_zip_update(path):
            return tr("update.install.action.open_package")
        return tr("update.install.action.update_now")
