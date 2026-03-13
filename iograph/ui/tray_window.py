from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt


def show_window_on_top(window) -> None:
    # Robust foreground restore for tray/menu activation across macOS/Windows.
    state = window.windowState()
    state &= ~Qt.WindowState.WindowMinimized
    window.setWindowState(state)
    if not window.isVisible():
        window.showNormal()
    elif window.isMinimized():
        window.showNormal()
    window.raise_()
    window.activateWindow()
    QTimer.singleShot(0, window.raise_)
    QTimer.singleShot(0, window.activateWindow)


def tray_settings_label(is_settings_open: bool) -> str:
    return "Hide Settings" if is_settings_open else "Show Settings"
