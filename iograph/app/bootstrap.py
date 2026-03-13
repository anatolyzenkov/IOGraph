from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QLockFile, QStandardPaths, Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

_windows_single_instance_lock: QLockFile | None = None


def run_app(window_factory) -> int:
    if sys.platform.startswith("win"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    if sys.platform.startswith("win"):
        if not _acquire_windows_single_instance_lock():
            return 0
    window = window_factory()
    window.show()
    return app.exec()


def _acquire_windows_single_instance_lock() -> bool:
    global _windows_single_instance_lock
    lock_root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    if not lock_root:
        lock_root = str(Path.home() / ".iograph")
    lock_dir = Path(lock_root)
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(lock_dir / "iograph-single-instance.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.information(None, "IOGraph", "IOGraph is already running.")
        return False
    _windows_single_instance_lock = lock
    return True
