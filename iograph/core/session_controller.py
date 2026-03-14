from __future__ import annotations

from datetime import datetime
import re

from PyQt6.QtCore import QObject, pyqtSignal


class SessionController(QObject):
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    session_reset = pyqtSignal()
    session_restored = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
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

    def period_label(self, *, tr=lambda s: s, format_time=None, format_date=None) -> str:
        started = self._started_at
        if started is None:
            return tr("session.time_period")
        ended = self._ended_at or datetime.now()
        time_formatter = format_time or (lambda dt: f"{dt.hour:02d}:{dt.minute:02d}")
        date_formatter = format_date or (lambda dt: f"{dt.day:02d}.{dt.month:02d}")
        if (ended - started).total_seconds() <= 60:
            return tr("session.period.from_template").format(start=time_formatter(started))
        full_date_treatment = started.day != ended.day or started.month != ended.month
        start_label = time_formatter(started) if not full_date_treatment else f"{time_formatter(started)} {date_formatter(started)}"
        end_label = time_formatter(ended) if not full_date_treatment else f"{time_formatter(ended)} {date_formatter(ended)}"
        return tr("session.period.from_to_template").format(
            start=start_label,
            end=end_label,
        )

    def export_base_name(
        self,
        elapsed_ms: int,
        app_name: str = "IOGraphica",
        *,
        tr=lambda s: s,
        format_time=None,
        format_date=None,
    ) -> str:
        time_label = self.tracking_time_text(elapsed_ms, tr=tr)
        period = self.period_label(tr=tr, format_time=format_time, format_date=format_date)
        safe_app = self._sanitize_filename_component(app_name)
        safe_time = self._sanitize_filename_component(time_label)
        if not period:
            return f"{safe_app} - {safe_time}"
        safe_period = self._sanitize_filename_component(period)
        return f"{safe_app} - {safe_time} ({safe_period})"

    @classmethod
    def tracking_time_text(cls, ms: int, *, tr=lambda s: s, plural=None) -> str:
        total_seconds = max(0, int(ms / 1000.0))
        if total_seconds < 1:
            return tr("session.time.just_started")
        plural_fn = plural or (lambda key_base, value: tr(f"{key_base}.one") if value == 1 else tr(f"{key_base}.other"))
        if total_seconds < 60:
            return cls._pluralize(total_seconds, "session.time.second", plural=plural_fn)
        total_minutes = total_seconds // 60
        if total_minutes < 60:
            return cls._pluralize(total_minutes, "session.time.minute", plural=plural_fn)
        total_hours = total_minutes // 60
        if total_hours < 24:
            return cls._pluralize(total_hours, "session.time.hour", plural=plural_fn)
        total_days = total_hours // 24
        return cls._pluralize(total_days, "session.time.day", plural=plural_fn)

    @staticmethod
    def _pluralize(value: int, key_base: str, *, plural) -> str:
        return plural(key_base, value).format(value=value)

    @staticmethod
    def _sanitize_filename_component(text: str) -> str:
        # Keep locale text readable but remove filesystem-invalid chars.
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', "-", str(text))
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = cleaned.rstrip(". ")
        return cleaned or "session"
