from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon


def build_app_icon(resource_dir: Path, app_icon_files: tuple[str, ...]) -> QIcon:
    icon = QIcon()
    for name in app_icon_files:
        path = resource_dir / name
        if path.exists():
            icon.addFile(str(path))
        hi = resource_dir / f"{path.stem}@2x{path.suffix}"
        if hi.exists():
            icon.addFile(str(hi))
    return icon
