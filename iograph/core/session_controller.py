from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal


class SessionController(QObject):
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    session_reset = pyqtSignal()
    session_restored = pyqtSignal()

    def __init__(self, month_names: tuple[str, ...], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._month_names = month_names
        self._started_at: datetime | None = None
        self._ended_at: datetime | None = None

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def ended_at(self) -> datetime | None:
        return self._ended_at

    def started_at_iso(self) -> str | None:
        return self._started_at.isoformat() if self._started_at else None

    def ended_at_iso(self) -> str | None:
        return self._ended_at.isoformat() if self._ended_at else None

    def start_tracking(self) -> None:
        if self._started_at is None:
            self._started_at = datetime.now()
        self._ended_at = None
        self.tracking_started.emit()

    def stop_tracking(self) -> None:
        self._ended_at = datetime.now()
        self.tracking_stopped.emit()

    def reset(self) -> None:
        self._started_at = None
        self._ended_at = None
        self.session_reset.emit()

    def restore_from_iso(self, started_raw, ended_raw) -> None:
        self._started_at = None
        self._ended_at = None
        if isinstance(started_raw, str):
            try:
                self._started_at = datetime.fromisoformat(started_raw)
            except ValueError:
                self._started_at = None
        if isinstance(ended_raw, str):
            try:
                self._ended_at = datetime.fromisoformat(ended_raw)
            except ValueError:
                self._ended_at = None
        self.session_restored.emit()

    def ensure_started_for_elapsed(self, elapsed_ms: int) -> None:
        if self._started_at is None and elapsed_ms > 0:
            self._started_at = datetime.now()

    def period_label(self) -> str:
        started = self._started_at
        if started is None:
            return "Time Period"
        ended = self._ended_at or datetime.now()
        if (ended - started).total_seconds() <= 60:
            return f"From {self._date_pattern(started, False)}"
        full_date_treatment = started.day != ended.day or started.month != ended.month
        return f"From {self._date_pattern(started, full_date_treatment)} to {self._date_pattern(ended, full_date_treatment)}"

    def export_base_name(self, elapsed_ms: int, app_name: str = "IOGraphica") -> str:
        time_label = self.tracking_time_text(elapsed_ms)
        period = self.period_label()
        if not period:
            return f"{app_name} - {time_label}"
        period_for_file = period.replace(":", "-")
        period_for_file = period_for_file[0].lower() + period_for_file[1:]
        return f"{app_name} - {time_label} ({period_for_file})"

    @classmethod
    def tracking_time_text(cls, ms: int) -> str:
        if ms < 1000:
            return "Just started"
        seconds = ms / 1000.0
        minutes = ms / (60.0 * 1000.0)
        hours = ms / (60.0 * 60.0 * 1000.0)
        days = ms / (24.0 * 60.0 * 60.0 * 1000.0)
        if minutes < 1.0:
            n = int(seconds)
            return f"{n} second" if n == 1 else f"{n} seconds"
        if hours < 1.0:
            n = int(minutes)
            return f"{n} minute" if n == 1 else f"{n} minutes"
        if days < 1.0:
            n = cls._precision(hours)
            return f"{n} hour" if hours < 1.1 else f"{n} hours"
        n = cls._precision(days)
        return f"{n} day" if days < 1.1 else f"{n} days"

    def _date_pattern(self, dt: datetime, full_date: bool) -> str:
        base = f"{dt.hour}:{dt.minute:02d}"
        if not full_date:
            return base
        return f"{base} {self._month_names[dt.month - 1]} {self._ordinal(dt.day)}"

    @staticmethod
    def _ordinal(day: int) -> str:
        if day == 1:
            return "1st"
        if day == 2:
            return "2nd"
        if day == 3:
            return "3rd"
        return f"{day}th"

    @staticmethod
    def _precision(value: float) -> str:
        if value % 1.0 < 0.1:
            return str(int(value))
        return f"{value:.1f}"
