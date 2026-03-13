from __future__ import annotations

from pathlib import Path
import sys


class UpdateUiDecisions:
    @staticmethod
    def is_zip_update(path: Path | None) -> bool:
        return path is not None and path.suffix.lower() == ".zip"

    @classmethod
    def already_downloaded_prompt(cls, path: Path | None) -> str:
        if cls.is_zip_update(path):
            return "New version of IOGraph is already downloaded.\n\nOpen downloaded update package?"
        return "New version of IOGraph is already downloaded.\n\nClose and install now?"

    @classmethod
    def install_ready_prompt(cls, path: Path | None) -> str:
        is_zip = cls.is_zip_update(path)
        if is_zip and sys.platform == "darwin":
            return "New version of IOGraph is ready to install.\n\nClose and install now?"
        if is_zip:
            return "New version of IOGraph is downloaded.\n\nOpen downloaded update package?"
        return "New version of IOGraph is ready to install.\n\nClose and install now?"

    @classmethod
    def install_action_label(cls, path: Path | None) -> str:
        if cls.is_zip_update(path) and sys.platform == "darwin":
            return "Install Downloaded Update..."
        if cls.is_zip_update(path):
            return "Open Update Package"
        return "Update now"
