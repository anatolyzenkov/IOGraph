from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QPoint, QTimer
from PyQt6.QtWidgets import QApplication


@dataclass
class _SnapshotRestoreState:
    visible: bool = False
    minimized: bool = False
    position: QPoint | None = None


class DesktopSnapshotController:
    def __init__(
        self,
        window,
        *,
        capture_desktop_background,
        on_status,
        tr=lambda s: s,
        hide_delay_ms: int = 40,
        final_delay_ms: int = 160,
    ) -> None:
        self._window = window
        self._capture_desktop_background = capture_desktop_background
        self._on_status = on_status
        self._tr = tr
        self._hide_delay_ms = int(hide_delay_ms)
        self._final_delay_ms = int(final_delay_ms)
        self._restore = _SnapshotRestoreState()

    def refresh(self) -> None:
        # Two-phase hide/capture: handles startup case when window becomes visible after scheduling.
        self._restore.visible = self._window.isVisible()
        self._restore.minimized = self._window.isMinimized()
        self._restore.position = self._window.frameGeometry().topLeft()
        if self._restore.visible:
            self._window.hide()
            QApplication.processEvents()
        QTimer.singleShot(self._hide_delay_ms, self._capture_hidden)

    def _capture_hidden(self) -> None:
        if self._window.isVisible():
            # Startup path: window may become visible after initial scheduling.
            self._restore.visible = True
            self._restore.minimized = self._window.isMinimized()
            self._restore.position = self._window.frameGeometry().topLeft()
            self._window.hide()
            QApplication.processEvents()
            QTimer.singleShot(self._final_delay_ms, self._capture_final)
            return
        QTimer.singleShot(self._final_delay_ms, self._capture_final)

    def _capture_final(self) -> None:
        ok = self._capture_desktop_background()
        if self._restore.visible:
            if self._restore.minimized:
                self._window.showMinimized()
            else:
                self._window.showNormal()
                if self._restore.position is not None:
                    self._window.move(self._restore.position)
                self._window.raise_()
                self._window.activateWindow()
        self._restore.position = None
        self._on_status(
            self._tr("desktop.snapshot.updated") if ok else self._tr("desktop.snapshot.failed")
        )
