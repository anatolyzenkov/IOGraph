from __future__ import annotations

from dataclasses import dataclass
from math import atan2, pi, sqrt
from time import monotonic
import sys
from typing import Any

from PyQt6.QtCore import QPointF, QRect, QRectF, QTimer, Qt
from PyQt6.QtGui import QColor, QColorSpace, QCursor, QGuiApplication, QPainter, QPaintEvent, QPen, QPixmap
from PyQt6.QtWidgets import QWidget


@dataclass
class FloatPoint:
    x: float
    y: float

    def set_from(self, other: "FloatPoint") -> None:
        self.x = other.x
        self.y = other.y


class TrackCanvas(QWidget):
    # Java parity: Drawer constants
    STROKE_WEIGHT = 0.45
    RADIUS_THRESHOLD = 20.0
    DELAY_DISTANCE_QUAD = 400.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setMouseTracking(True)

        self._desktop_rect = QRect(0, 0, 1, 1)
        self._scale: float = 1.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0
        self._pixel_scale: float = 1.0

        # Java-like two-layer drawing model: full-size + preview-size
        self._preview_pixmap: QPixmap | None = None

        self._prev_p = FloatPoint(0.0, 0.0)
        self._new_p = FloatPoint(0.0, 0.0)
        self._stop_p = FloatPoint(0.0, 0.0)
        self._radius: float = 0.0

        self._raw_samples: list[tuple[float | None, float | None, int]] = []
        self._accumulated_ms: int = 0
        self._run_started_mono: float | None = None
        self._has_written_first_row = False

        self._ignore_mouse_stops: bool = False
        self._colorful_scheme: bool = False
        self._use_desktop_background: bool = False
        self._use_multiple_monitors: bool = True
        self._desktop_background_source: QPixmap | None = None
        self._tracking: bool = False
        self._last_elapsed_ms: int = 0

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

    # Public API

    def start_tracking(self) -> None:
        if self._tracking:
            return
        self._tracking = True
        self._prepare_for_update()
        self._run_started_mono = monotonic()
        self._timer.start()

    def stop_tracking(self) -> None:
        if self._tracking and self._run_started_mono is not None:
            delta = int((monotonic() - self._run_started_mono) * 1000)
            self._accumulated_ms += max(0, delta)
        self._run_started_mono = None
        self._last_elapsed_ms = self._accumulated_ms
        self._tracking = False
        self._timer.stop()
        self.update()

    def toggle_tracking(self) -> None:
        if self._tracking:
            self.stop_tracking()
        else:
            self.start_tracking()

    def reset(self) -> None:
        self._ensure_buffers()
        if self._preview_pixmap is not None:
            self._preview_pixmap.fill(Qt.GlobalColor.transparent)
        self._raw_samples = []
        self._accumulated_ms = 0
        self._run_started_mono = None
        self._has_written_first_row = False
        self._last_elapsed_ms = 0
        self._radius = 0.0
        self.update()

    def export_csv_text(self) -> str:
        lines = ["x,y,time"]
        for x, y, t in self._raw_samples:
            if x is None or y is None:
                lines.append(f",,{t}")
            else:
                lines.append(f"{int(round(x))},{int(round(y))},{t}")
        return "\n".join(lines) + "\n"

    def export_raw_samples(self) -> list[dict[str, Any]]:
        return [{"x": x, "y": y, "t": t} for x, y, t in self._raw_samples]

    def load_raw_samples(self, rows: list[dict[str, Any]]) -> None:
        parsed: list[tuple[float | None, float | None, int]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            t_raw = row.get("t", 0)
            try:
                t = int(t_raw)
            except (TypeError, ValueError):
                t = 0
            x_raw = row.get("x")
            y_raw = row.get("y")
            if x_raw is None or y_raw is None:
                parsed.append((None, None, max(0, t)))
                continue
            try:
                x = float(x_raw)
                y = float(y_raw)
            except (TypeError, ValueError):
                parsed.append((None, None, max(0, t)))
                continue
            parsed.append((x, y, max(0, t)))
        parsed.sort(key=lambda s: s[2])
        self._raw_samples = parsed
        self._has_written_first_row = len(parsed) > 0
        self._accumulated_ms = parsed[-1][2] if parsed else 0
        self._last_elapsed_ms = self._accumulated_ms
        self._rebuild_from_raw_samples()

    def export_png(self, path: str) -> bool:
        self._ensure_buffers()
        w = max(1, int(round(self._desktop_rect.width() * self._pixel_scale)))
        h = max(1, int(round(self._desktop_rect.height() * self._pixel_scale)))
        out = QPixmap(w, h)
        bg = Qt.GlobalColor.black if self._colorful_scheme else Qt.GlobalColor.white
        out.fill(bg)

        p = QPainter(out)
        try:
            if self._use_desktop_background and self._desktop_background_source is not None:
                src = self._desktop_background_source
                source = QRectF(0.0, 0.0, float(src.width()), float(src.height()))
                target = QRectF(0.0, 0.0, float(w), float(h))
                p.drawPixmap(target, src, source)
        finally:
            p.end()
        self._render_raw_on_pixmap(
            out,
            map_point=self._map_global_to_full,
            stroke_scale=1.0 * self._pixel_scale,
        )

        # macOS export: tag PNG with Display P3 profile when available.
        if sys.platform == "darwin":
            image = out.toImage()
            try:
                image.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.DisplayP3))
            except Exception:
                # Keep export robust even if color space API varies by Qt build.
                pass
            return image.save(path, "PNG")
        return out.save(path, "PNG")

    def set_ignore_mouse_stops(self, value: bool) -> None:
        if self._ignore_mouse_stops == value:
            return
        self._ignore_mouse_stops = value
        self._rebuild_from_raw_samples()

    def set_colorful_scheme(self, value: bool) -> None:
        if self._colorful_scheme == value:
            return
        self._colorful_scheme = value
        self._rebuild_from_raw_samples()

    def is_colorful_scheme(self) -> bool:
        return self._colorful_scheme

    def set_use_desktop_background(self, value: bool) -> None:
        self._use_desktop_background = value
        if value and self._desktop_background_source is None:
            self.update_desktop_background()
        self.update()

    def set_use_multiple_monitors(self, value: bool) -> None:
        self._use_multiple_monitors = value
        self._refresh_desktop_geometry()
        self._update_projection()
        self._ensure_buffers()
        if self._use_desktop_background:
            self.update_desktop_background()
        self._rebuild_from_raw_samples()

    def is_use_multiple_monitors(self) -> bool:
        return self._use_multiple_monitors

    def update_desktop_background(self) -> bool:
        screens = QGuiApplication.screens()
        if not screens:
            return False

        self._refresh_desktop_geometry()
        base = QPixmap(self._desktop_rect.width(), self._desktop_rect.height())
        base.fill(Qt.GlobalColor.black)

        painter = QPainter(base)
        try:
            if self._use_multiple_monitors:
                for screen in screens:
                    s_rect = screen.geometry()
                    shot = screen.grabWindow(0)
                    if shot.isNull():
                        continue
                    painter.drawPixmap(
                        s_rect.x() - self._desktop_rect.x(),
                        s_rect.y() - self._desktop_rect.y(),
                        shot,
                    )
            else:
                screen = self._get_single_screen()
                if screen is None:
                    return False
                s_rect = screen.geometry()
                shot = screen.grabWindow(0)
                if shot.isNull():
                    return False
                painter.drawPixmap(
                    s_rect.x() - self._desktop_rect.x(),
                    s_rect.y() - self._desktop_rect.y(),
                    shot,
                )
        finally:
            painter.end()

        self._desktop_background_source = base
        self.update()
        return True

    def is_tracking(self) -> bool:
        return self._tracking

    def get_elapsed_ms(self) -> int:
        if self._tracking and self._run_started_mono is not None:
            delta = int((monotonic() - self._run_started_mono) * 1000)
            return self._accumulated_ms + max(0, delta)
        return self._last_elapsed_ms

    # Internal helpers

    def _ensure_buffers(self) -> None:
        self._refresh_desktop_geometry()
        self._update_projection()
        pixel_scale = self._get_pixel_scale()

        prev_w = max(1, int(round(self.width() * pixel_scale)))
        prev_h = max(1, int(round(self.height() * pixel_scale)))

        prev_need = (
            self._preview_pixmap is None
            or self._preview_pixmap.width() != prev_w
            or self._preview_pixmap.height() != prev_h
            or abs(self._pixel_scale - pixel_scale) > 0.01
        )
        if prev_need:
            old = self._preview_pixmap
            self._preview_pixmap = QPixmap(prev_w, prev_h)
            self._preview_pixmap.setDevicePixelRatio(pixel_scale)
            self._preview_pixmap.fill(Qt.GlobalColor.transparent)
            if old is not None:
                p = QPainter(self._preview_pixmap)
                try:
                    p.drawPixmap(0, 0, old)
                finally:
                    p.end()

        self._pixel_scale = pixel_scale

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._ensure_buffers()
        self._rebuild_from_raw_samples()

    def _prepare_for_update(self) -> None:
        self._ensure_buffers()
        self._radius = 0.0

        pos = QCursor.pos()
        self._new_p = FloatPoint(float(pos.x()), float(pos.y()))
        self._prev_p.set_from(self._new_p)
        self._stop_p.set_from(self._new_p)

    def _on_tick(self) -> None:
        if not self._tracking:
            return

        self._ensure_buffers()
        if self._preview_pixmap is None:
            return

        pos = QCursor.pos()
        self._new_p.x = float(pos.x())
        self._new_p.y = float(pos.y())

        dt_ms = self.get_elapsed_ms()
        self._last_elapsed_ms = dt_ms

        no_movement = self._prev_p.x == self._new_p.x and self._prev_p.y == self._new_p.y
        if not self._has_written_first_row:
            self._raw_samples.append((float(pos.x()), float(pos.y()), dt_ms))
            self._has_written_first_row = True
        elif no_movement:
            self._raw_samples.append((None, None, dt_ms))
        else:
            self._raw_samples.append((float(pos.x()), float(pos.y()), dt_ms))

        update_rect = QRect()

        if not no_movement:
            prev_preview = self._map_global_to_preview(self._prev_p)
            new_preview = self._map_global_to_preview(self._new_p)

            x1 = int(new_preview.x())
            y1 = int(new_preview.y())
            x2 = int(prev_preview.x())
            y2 = int(prev_preview.y())
            update_rect = QRect(min(x1, x2) - 2, min(y1, y2) - 2, abs(x1 - x2) + 4, abs(y1 - y2) + 4)

            c = self._get_draw_color()
            self._draw_line(self._preview_pixmap, prev_preview, new_preview, c, self.STROKE_WEIGHT * self._scale)

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
            if self._radius > self.RADIUS_THRESHOLD:
                max_radius = (self._desktop_rect.height() * 0.25) ** 2
                self._radius = min(self._radius, max_radius)
                c = self._get_draw_color()

                preview_rect = self._draw_stop_ellipse(
                    self._preview_pixmap,
                    self._map_global_to_preview(self._prev_p),
                    c,
                    self._scale,
                )
                update_rect = update_rect.united(preview_rect)

            self._stop_p.set_from(self._new_p)
            self._radius = 0.0

        self._prev_p.set_from(self._new_p)

        if not update_rect.isNull():
            self.update(update_rect)

    def _draw_line(self, pix: QPixmap, p0: QPointF, p1: QPointF, color: QColor, width: float) -> None:
        p = QPainter(pix)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(color)
            pen.setWidthF(max(0.0, width))
            p.setPen(pen)
            p.drawLine(p0, p1)
        finally:
            p.end()

    def _draw_stop_ellipse(
        self,
        pix: QPixmap,
        center: QPointF,
        color: QColor,
        scale: float,
        radius: float | None = None,
    ) -> QRect:
        r = self._radius if radius is None else radius
        halo_d = int(2.0 * r * scale)
        dot_d = int(2.0 * sqrt(r) * scale)
        n = 200.0 * max(0.0, 1.0 - 2.0 * sqrt(r) / self.RADIUS_THRESHOLD)
        ch = 0 if self._colorful_scheme else 255
        halo_color = QColor(ch, ch, ch, int(n))

        hx = int(center.x() - halo_d * 0.5)
        hy = int(center.y() - halo_d * 0.5)
        dx = int(center.x() - dot_d * 0.5)
        dy = int(center.y() - dot_d * 0.5)

        p = QPainter(pix)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(halo_color)
            p.drawEllipse(hx, hy, halo_d, halo_d)

            p.setPen(QPen(color, max(0.0, self.STROKE_WEIGHT * scale)))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(hx, hy, halo_d, halo_d)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawEllipse(dx, dy, dot_d, dot_d)
        finally:
            p.end()

        return QRect(hx - 2, hy - 2, halo_d + 4, halo_d + 4)

    def _clear_draw_buffers(self) -> None:
        self._ensure_buffers()
        if self._preview_pixmap is not None:
            self._preview_pixmap.fill(Qt.GlobalColor.transparent)

    def _rebuild_from_raw_samples(self) -> None:
        self._clear_draw_buffers()
        if self._preview_pixmap is None:
            return
        self._render_raw_on_pixmap(
            self._preview_pixmap,
            map_point=self._map_global_to_preview,
            stroke_scale=self._scale,
        )
        self.update()

    def _render_raw_on_pixmap(self, pix: QPixmap, map_point, stroke_scale: float) -> None:
        if not self._raw_samples:
            self._radius = 0.0
            self._has_written_first_row = False
            return

        first_x, first_y, _ = self._raw_samples[0]
        if first_x is None or first_y is None:
            return

        radius = 0.0
        prev = FloatPoint(first_x, first_y)
        stop = FloatPoint(first_x, first_y)

        for x, y, _ in self._raw_samples[1:]:
            if x is None or y is None:
                new_p = FloatPoint(prev.x, prev.y)
            else:
                new_p = FloatPoint(x, y)

            no_movement = prev.x == new_p.x and prev.y == new_p.y
            if not no_movement:
                c = self._get_draw_color_for(prev, new_p)
                p0 = map_point(prev)
                p1 = map_point(new_p)
                self._draw_line(pix, p0, p1, c, self.STROKE_WEIGHT * stroke_scale)

            if self._ignore_mouse_stops:
                prev = new_p
                continue

            dx = new_p.x - stop.x
            dy = new_p.y - stop.y
            d = dx * dx + dy * dy
            if d < self.DELAY_DISTANCE_QUAD:
                radius += 0.3
            else:
                if radius > self.RADIUS_THRESHOLD:
                    max_radius = (self._desktop_rect.height() * 0.25) ** 2
                    radius = min(radius, max_radius)
                    c = self._get_draw_color_for(prev, new_p)
                    self._draw_stop_ellipse(
                        pix,
                        map_point(prev),
                        c,
                        stroke_scale,
                        radius=radius,
                    )
                stop = FloatPoint(new_p.x, new_p.y)
                radius = 0.0

            prev = new_p

    # Painting

    def _get_draw_color_for(self, prev: FloatPoint, new: FloatPoint) -> QColor:
        if not self._colorful_scheme:
            return QColor("black")

        n = 1.0 + atan2(new.y - prev.y, new.x - prev.x) / pi
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

    def _get_draw_color(self) -> QColor:
        return self._get_draw_color_for(self._prev_p, self._new_p)

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        self._ensure_buffers()

        p = QPainter(self)
        try:
            bg = Qt.GlobalColor.black if self._colorful_scheme else Qt.GlobalColor.white
            p.fillRect(self.rect(), bg)

            if self._use_desktop_background and self._desktop_background_source is not None:
                src = self._desktop_background_source
                target = QRectF(
                    self._offset_x,
                    self._offset_y,
                    self._desktop_rect.width() * self._scale,
                    self._desktop_rect.height() * self._scale,
                )
                source = QRectF(0.0, 0.0, float(src.width()), float(src.height()))
                p.drawPixmap(target, src, source)

            if self._preview_pixmap is not None:
                p.drawPixmap(0, 0, self._preview_pixmap)
        finally:
            p.end()

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

        primary = QGuiApplication.primaryScreen() or screens[0]
        self._desktop_rect = primary.geometry()

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

    def _map_global_to_preview(self, p: FloatPoint) -> QPointF:
        x = (p.x - self._desktop_rect.x()) * self._scale + self._offset_x
        y = (p.y - self._desktop_rect.y()) * self._scale + self._offset_y
        return QPointF(x, y)

    def _map_global_to_full(self, p: FloatPoint) -> QPointF:
        x = (p.x - self._desktop_rect.x()) * self._pixel_scale
        y = (p.y - self._desktop_rect.y()) * self._pixel_scale
        return QPointF(x, y)

    def _get_pixel_scale(self) -> float:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return 1.0
        return 2.0 if screen.devicePixelRatio() >= 1.5 else 1.0

    def _get_single_screen(self):
        screens = QGuiApplication.screens()
        if not screens:
            return None
        return QGuiApplication.primaryScreen() or screens[0]
