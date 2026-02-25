from __future__ import annotations

from dataclasses import dataclass
from math import atan2, pi
from time import monotonic

from PyQt6.QtCore import QPointF, QRect, QRectF, QTimer, Qt
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPaintEvent, QPen, QPixmap
from PyQt6.QtWidgets import QWidget


@dataclass
class FloatPoint:
    x: float
    y: float

    def set_from(self, other: "FloatPoint") -> None:
        self.x = other.x
        self.y = other.y


class TrackCanvas(QWidget):
    """
    Simplified port of Java TrackManager/Drawer:
    - читает глобальную позицию курсора
    - рисует линии движения и круги в точках остановки
    - сохраняет данные во внутренний CSV-буфер (на будущее экспорт)
    """

    RADIUS_THRESHOLD = 20.0
    DELAY_DISTANCE_QUAD = 400.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setMouseTracking(True)

        self._pixmap: QPixmap | None = None
        self._desktop_rect = QRect(0, 0, 1, 1)
        self._scale: float = 1.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0

        self._prev_p = FloatPoint(0.0, 0.0)
        self._new_p = FloatPoint(0.0, 0.0)
        self._stop_p = FloatPoint(0.0, 0.0)
        self._radius: float = 0.0

        self._csv_lines: list[str] = ["x,y,time"]
        self._start_time: float | None = None

        self._ignore_mouse_stops: bool = False
        self._colorful_scheme: bool = False
        self._use_desktop_background: bool = False
        self._use_multiple_monitors: bool = True
        self._desktop_background_source: QPixmap | None = None
        self._tracking: bool = False
        self._last_elapsed_ms: int = 0

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._on_tick)

    # Public API

    def start_tracking(self) -> None:
        self._tracking = True
        self._prepare_for_update()
        if self._start_time is None:
            self._start_time = monotonic()
        self._timer.start()

    def stop_tracking(self) -> None:
        self._last_elapsed_ms = self.get_elapsed_ms()
        self._tracking = False
        self._timer.stop()
        self.update()

    def toggle_tracking(self) -> None:
        if self._tracking:
            self.stop_tracking()
        else:
            self.start_tracking()

    def reset(self) -> None:
        if self._pixmap is not None:
            self._pixmap.fill(Qt.GlobalColor.transparent)
        self._csv_lines = ["x,y,time"]
        self._start_time = None
        self._last_elapsed_ms = 0
        self._radius = 0.0
        self.update()

    def export_csv_text(self) -> str:
        return "\n".join(self._csv_lines) + "\n"

    def export_png(self, path: str) -> bool:
        self._ensure_pixmap()
        if self._pixmap is None:
            return False

        image = QPixmap(self.size())
        bg = Qt.GlobalColor.black if self._colorful_scheme else Qt.GlobalColor.white
        image.fill(bg)
        painter = QPainter(image)
        try:
            if self._use_desktop_background and self._desktop_background_source is not None:
                src = self._desktop_background_source
                target = QRectF(
                    self._offset_x,
                    self._offset_y,
                    self._desktop_rect.width() * self._scale,
                    self._desktop_rect.height() * self._scale,
                )
                source = QRectF(0.0, 0.0, float(src.width()), float(src.height()))
                painter.drawPixmap(target, src, source)
            painter.drawPixmap(0, 0, self._pixmap)
        finally:
            painter.end()
        return image.save(path, "PNG")

    def set_ignore_mouse_stops(self, value: bool) -> None:
        self._ignore_mouse_stops = value

    def set_colorful_scheme(self, value: bool) -> None:
        self._colorful_scheme = value
        self.update()

    def set_use_desktop_background(self, value: bool) -> None:
        self._use_desktop_background = value
        if value and self._desktop_background_source is None:
            self.update_desktop_background()
        self.update()

    def set_use_multiple_monitors(self, value: bool) -> None:
        self._use_multiple_monitors = value
        self._refresh_desktop_geometry()
        self._update_projection()
        if self._use_desktop_background:
            self.update_desktop_background()
        self.update()

    def update_desktop_background(self) -> bool:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return False

        self._refresh_desktop_geometry()
        shot = screen.grabWindow(
            0,
            self._desktop_rect.x(),
            self._desktop_rect.y(),
            self._desktop_rect.width(),
            self._desktop_rect.height(),
        )
        if shot.isNull():
            return False
        self._desktop_background_source = shot
        self._update_projection()
        self.update()
        return True

    def is_tracking(self) -> bool:
        return self._tracking

    def get_elapsed_ms(self) -> int:
        if self._start_time is None:
            return self._last_elapsed_ms
        if not self._tracking:
            return self._last_elapsed_ms
        return int((monotonic() - self._start_time) * 1000)

    # Internal helpers

    def _ensure_pixmap(self) -> None:
        if self._pixmap is None or self._pixmap.size() != self.size():
            self._pixmap = QPixmap(self.size())
            self._pixmap.fill(Qt.GlobalColor.transparent)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._ensure_pixmap()
        self._update_projection()

    def _prepare_for_update(self) -> None:
        self._ensure_pixmap()
        self._refresh_desktop_geometry()
        self._update_projection()
        self._radius = 0.0

        pos = QCursor.pos()
        self._new_p = FloatPoint(float(pos.x()), float(pos.y()))
        self._prev_p.set_from(self._new_p)
        self._stop_p.set_from(self._new_p)

    def _on_tick(self) -> None:
        if not self._tracking:
            return

        pos = QCursor.pos()
        self._new_p.x = float(pos.x())
        self._new_p.y = float(pos.y())

        dt_ms = self.get_elapsed_ms()
        self._last_elapsed_ms = dt_ms
        no_movement = (
            self._prev_p.x == self._new_p.x and self._prev_p.y == self._new_p.y
        )

        if no_movement:
            self._csv_lines.append(f",,{dt_ms}")
        else:
            self._csv_lines.append(f"{int(pos.x())},{int(pos.y())},{dt_ms}")

        update_rect = QRect()

        if not no_movement and self._pixmap is not None:
            new_canvas = self._map_global_to_canvas(self._new_p)
            prev_canvas = self._map_global_to_canvas(self._prev_p)
            x1 = int(new_canvas.x())
            y1 = int(new_canvas.y())
            x2 = int(prev_canvas.x())
            y2 = int(prev_canvas.y())

            update_rect = QRect(
                min(x1, x2) - 2,
                min(y1, y2) - 2,
                abs(x1 - x2) + 4,
                abs(y1 - y2) + 4,
            )

            p = QPainter(self._pixmap)
            try:
                p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                p.setPen(QPen(self._get_draw_color(), 1.5))
                p.drawLine(prev_canvas, new_canvas)
            finally:
                p.end()

        # Логика "стопов" с кругами (упрощённая)
        if self._ignore_mouse_stops:
            self._prev_p.set_from(self._new_p)
            if not update_rect.isNull():
                self.update(update_rect)
            return

        dx = self._new_p.x - self._stop_p.x
        dy = self._new_p.y - self._stop_p.y
        d = dx * dx + dy * dy

        if d < self.DELAY_DISTANCE_QUAD:
            self._radius += 0.3
        else:
            if self._radius > self.RADIUS_THRESHOLD and self._pixmap is not None:
                radius_px = int((self._radius ** 0.5 * 2.0) * self._scale)
                radius_px = max(1, radius_px)
                canvas_prev = self._map_global_to_canvas(self._prev_p)
                cx = int(canvas_prev.x())
                cy = int(canvas_prev.y())
                rect = QRect(
                    cx - radius_px,
                    cy - radius_px,
                    radius_px * 2,
                    radius_px * 2,
                )
                p = QPainter(self._pixmap)
                try:
                    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    c = self._get_draw_color()
                    p.setPen(QPen(c, 1.0))
                    p.setBrush(c)
                    p.drawEllipse(rect)
                finally:
                    p.end()
                update_rect = update_rect.united(rect)

            self._stop_p.set_from(self._new_p)
            self._radius = 0.0

        self._prev_p.set_from(self._new_p)

        if not update_rect.isNull():
            # redraw only affected region; Qt сам инвалидацию разрулит
            self.update(update_rect)

    # Painting
    def _get_draw_color(self) -> QColor:
        if not self._colorful_scheme:
            return QColor("black")

        n = (1.0 + atan2(self._new_p.y - self._prev_p.y, self._new_p.x - self._prev_p.x) / pi)
        n = (n + 0.25) % 1.0
        colors = (QColor(255, 255, 0), QColor(0, 255, 255), QColor(255, 0, 255))
        idx = int(len(colors) * n)
        c0 = colors[idx]
        c1 = colors[(idx + 1) % len(colors)]
        t = len(colors) * n - idx

        r = int(c0.red() + (c1.red() - c0.red()) * t)
        g = int(c0.green() + (c1.green() - c0.green()) * t)
        b = int(c0.blue() + (c1.blue() - c0.blue()) * t)
        return QColor(r, g, b)

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        self._ensure_pixmap()
        painter = QPainter(self)
        try:
            bg = Qt.GlobalColor.black if self._colorful_scheme else Qt.GlobalColor.white
            painter.fillRect(self.rect(), bg)
            if self._use_desktop_background and self._desktop_background_source is not None:
                src = self._desktop_background_source
                target = QRectF(
                    self._offset_x,
                    self._offset_y,
                    self._desktop_rect.width() * self._scale,
                    self._desktop_rect.height() * self._scale,
                )
                source = QRectF(0.0, 0.0, float(src.width()), float(src.height()))
                painter.drawPixmap(target, src, source)
            if self._pixmap is not None:
                painter.drawPixmap(0, 0, self._pixmap)
        finally:
            painter.end()

    def _refresh_desktop_geometry(self) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            self._desktop_rect = QRect(0, 0, max(1, self.width()), max(1, self.height()))
            return
        if self._use_multiple_monitors:
            union_rect = QRect(screens[0].geometry())
            for s in screens[1:]:
                union_rect = union_rect.united(s.geometry())
            self._desktop_rect = union_rect
            return
        self._desktop_rect = screens[0].geometry()

    def _update_projection(self) -> None:
        width = max(1, self.width())
        height = max(1, self.height())
        dw = max(1, self._desktop_rect.width())
        dh = max(1, self._desktop_rect.height())
        sx = width / dw
        sy = height / dh
        self._scale = min(sx, sy)
        self._offset_x = (width - dw * self._scale) * 0.5
        self._offset_y = (height - dh * self._scale) * 0.5

    def _map_global_to_canvas(self, p: FloatPoint) -> QPointF:
        x = (p.x - self._desktop_rect.x()) * self._scale + self._offset_x
        y = (p.y - self._desktop_rect.y()) * self._scale + self._offset_y
        return QPointF(x, y)
