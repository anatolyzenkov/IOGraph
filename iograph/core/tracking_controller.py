from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

from .session_controller import SessionController


@dataclass(frozen=True)
class TrackingTransition:
    enabled: bool
    status_message: str


class TrackingController(QObject):
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    tracking_reset = pyqtSignal()

    def __init__(self, session: SessionController, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._session = session

    def set_tracking(self, enabled: bool) -> TrackingTransition:
        if enabled:
            self._session.start_tracking()
            self.tracking_started.emit()
            return TrackingTransition(enabled=True, status_message="Tracking started")
        self._session.stop_tracking()
        self.tracking_stopped.emit()
        return TrackingTransition(enabled=False, status_message="Tracking stopped")

    def apply_reset(self, was_tracking: bool) -> None:
        if was_tracking:
            self._session.start_tracking()
        else:
            self._session.reset()
        self.tracking_reset.emit()
