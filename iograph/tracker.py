from __future__ import annotations

from dataclasses import dataclass
from math import atan2, pi, sqrt
from time import monotonic
import sys
from typing import Any, Callable

from PyQt6.QtCore import QPointF, QRect, QRectF, QTimer, Qt
from PyQt6.QtGui import QColor, QColorSpace, QCursor, QGuiApplication, QImage, QPainter, QPaintEvent, QPen, QPixmap
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
    IDLE_RADIUS_STEP = 0.3

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
        self._suspend_preview_updates: bool = False

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

    @staticmethod
    def _is_windows() -> bool:
        return sys.platform.startswith("win")

    def _set_quality_hints(self, painter: QPainter) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if self._is_windows():
            # Mixed-DPI Windows setups benefit from the strongest painter quality flags.
            hq_aa = getattr(QPainter.RenderHint, "HighQualityAntialiasing", None)
            if hq_aa is not None:
                painter.setRenderHint(hq_aa, True)

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

    def load_raw_samples(self, rows: list[dict[str, Any]], rebuild: bool = True) -> None:
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
        self._raw_samples = self._compact_idle_samples(parsed)
        self._has_written_first_row = len(parsed) > 0
        self._accumulated_ms = parsed[-1][2] if parsed else 0
        self._last_elapsed_ms = self._accumulated_ms
        if rebuild:
            self._rebuild_from_raw_samples()

    @staticmethod
    def _compact_idle_samples(samples: list[tuple[float | None, float | None, int]]) -> list[tuple[float | None, float | None, int]]:
        compact: list[tuple[float | None, float | None, int]] = []
        for x, y, t in samples:
            if compact and x is None and y is None and compact[-1][0] is None and compact[-1][1] is None:
                compact[-1] = (None, None, max(compact[-1][2], t))
                continue
            compact.append((x, y, t))
        return compact

    def _idle_ticks_for_delta(self, dt_ms: int) -> float:
        interval_ms = max(1, self._timer.interval())
        return max(1.0, dt_ms / float(interval_ms))

    def rebuild_from_raw_samples(self) -> None:
        self._rebuild_from_raw_samples()

    def export_preview_cache(self, path: str) -> bool:
        self._ensure_buffers()
        if self._preview_pixmap is None:
            return False
        return self._preview_pixmap.save(path, "PNG")

    def load_preview_cache(self, path: str) -> bool:
        self._ensure_buffers()
        if self._preview_pixmap is None:
            return False
        cache = QPixmap(path)
        if cache.isNull():
            return False
        if cache.size() != self._preview_pixmap.size():
            return False
        self._preview_pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(self._preview_pixmap)
        try:
            p.drawPixmap(0, 0, cache)
        finally:
            p.end()
        self.update()
        return True

    def export_desktop_background_cache(self, path: str) -> bool:
        if self._desktop_background_source is None:
            return False
        return self._desktop_background_source.save(path, "PNG")

    def load_desktop_background_cache(self, path: str) -> bool:
        cache = QPixmap(path)
        if cache.isNull():
            return False
        if sys.platform.startswith("win"):
            scale = max(1.0, self._get_pixel_scale())
            expected_w = max(1, int(round(self._desktop_rect.width() * scale)))
            expected_h = max(1, int(round(self._desktop_rect.height() * scale)))
            logical_w = int(round(cache.deviceIndependentSize().width()))
            logical_h = int(round(cache.deviceIndependentSize().height()))
            if cache.width() == expected_w and cache.height() == expected_h:
                cache.setDevicePixelRatio(scale)
            elif logical_w != self._desktop_rect.width() or logical_h != self._desktop_rect.height():
                return False
        else:
            if cache.width() != self._desktop_rect.width() or cache.height() != self._desktop_rect.height():
                return False
        self._desktop_background_source = cache
        self.update()
        return True

    def render_cache_signature(self) -> dict[str, Any]:
        self._ensure_buffers()
        self._refresh_desktop_geometry()
        screens = QGuiApplication.screens()
        primary = QGuiApplication.primaryScreen()
        primary_name = primary.name() if primary is not None else ""
        return {
            "use_multiple_monitors": self._use_multiple_monitors,
            "desktop_rect": (
                self._desktop_rect.x(),
                self._desktop_rect.y(),
                self._desktop_rect.width(),
                self._desktop_rect.height(),
            ),
            "canvas_size": (self.width(), self.height()),
            "pixel_scale": round(self._pixel_scale, 2),
            "primary_name": primary_name,
            "screens": sorted(
                (
                    s.name(),
                    s.geometry().x(),
                    s.geometry().y(),
                    s.geometry().width(),
                    s.geometry().height(),
                )
                for s in screens
            ),
        }

    def export_png(self, path: str) -> bool:
        state = self.snapshot_export_render_state()
        image = self.render_export_image_from_state(state)
        return self.save_image_with_profile(image, path)

    def snapshot_preview_render_state(self) -> dict[str, Any]:
        self._ensure_buffers()
        bg = self._desktop_background_source.toImage() if self._use_desktop_background and self._desktop_background_source else None
        return {
            "raw_samples": list(self._raw_samples),
            "ignore_mouse_stops": self._ignore_mouse_stops,
            "colorful_scheme": self._colorful_scheme,
            "desktop_rect": (
                self._desktop_rect.x(),
                self._desktop_rect.y(),
                self._desktop_rect.width(),
                self._desktop_rect.height(),
            ),
            "logical_size": (max(1, self.width()), max(1, self.height())),
            "pixel_scale": self._pixel_scale,
            "timer_interval_ms": self._timer.interval(),
            "desktop_background": bg,
        }

    def snapshot_export_render_state(self) -> dict[str, Any]:
        self._ensure_buffers()
        bg = self._desktop_background_source.toImage() if self._use_desktop_background and self._desktop_background_source else None
        return {
            "raw_samples": list(self._raw_samples),
            "ignore_mouse_stops": self._ignore_mouse_stops,
            "colorful_scheme": self._colorful_scheme,
            "desktop_rect": (
                self._desktop_rect.x(),
                self._desktop_rect.y(),
                self._desktop_rect.width(),
                self._desktop_rect.height(),
            ),
            "logical_size": (max(1, self._desktop_rect.width()), max(1, self._desktop_rect.height())),
            "pixel_scale": self._pixel_scale,
            "timer_interval_ms": self._timer.interval(),
            "desktop_background": bg,
        }

    @staticmethod
    def _draw_color_for(prev: tuple[float, float], new: tuple[float, float], colorful_scheme: bool) -> QColor:
        if not colorful_scheme:
            return QColor("black")
        n = 1.0 + atan2(new[1] - prev[1], new[0] - prev[0]) / pi
        n = (n + 0.25) % 1.0
        colors = (QColor(255, 255, 0), QColor(0, 255, 255), QColor(255, 0, 255))
        idx = int(len(colors) * n)
        c0 = colors[idx]
        c1 = colors[(idx + 1) % len(colors)]
        t = len(colors) * n - idx
        return QColor(
            int(c0.red() + (c1.red() - c0.red()) * t),
            int(c0.green() + (c1.green() - c0.green()) * t),
            int(c0.blue() + (c1.blue() - c0.blue()) * t),
        )

    @classmethod
    def _render_raw_on_image(
        cls,
        image: QImage,
        raw_samples: list[tuple[float | None, float | None, int]],
        colorful_scheme: bool,
        ignore_mouse_stops: bool,
        desktop_rect: tuple[int, int, int, int],
        logical_size: tuple[int, int],
        pixel_scale: float,
        timer_interval_ms: int,
        progress_cb: Callable[[QImage], None] | None = None,
        progress_interval_ms: int = 80,
    ) -> None:
        if len(raw_samples) < 2:
            if progress_cb is not None:
                progress_cb(image.copy())
            return

        dx0, dy0, dw, dh = desktop_rect
        lw, lh = logical_size
        scale = min(max(1, lw) / max(1, dw), max(1, lh) / max(1, dh))
        offx = (lw - dw * scale) * 0.5
        offy = (lh - dh * scale) * 0.5
        s = max(0.0001, pixel_scale)

        def map_preview(pt: tuple[float, float]) -> tuple[float, float]:
            x = ((pt[0] - dx0) * scale + offx) * s
            y = ((pt[1] - dy0) * scale + offy) * s
            return x, y

        p = QPainter(image)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            radius = 0.0
            first = raw_samples[0]
            if first[0] is None or first[1] is None:
                return
            if progress_cb is not None:
                progress_cb(image.copy())
            prev = (float(first[0]), float(first[1]))
            stop = prev
            prev_t = first[2]
            next_emit = monotonic() + max(0.02, progress_interval_ms / 1000.0)

            for i, (x, y, t) in enumerate(raw_samples[1:], start=1):
                dt = max(0, int(t) - int(prev_t))
                prev_t = int(t)
                if x is None or y is None:
                    new = prev
                else:
                    new = (float(x), float(y))

                if prev != new:
                    color = cls._draw_color_for(prev, new, colorful_scheme)
                    pen = QPen(color)
                    pen.setWidthF(max(0.0, cls.STROKE_WEIGHT * scale * s))
                    p.setPen(pen)
                    x0, y0 = map_preview(prev)
                    x1, y1 = map_preview(new)
                    p.drawLine(QPointF(x0, y0), QPointF(x1, y1))

                if ignore_mouse_stops:
                    prev = new
                    if progress_cb is not None and (monotonic() >= next_emit or i == len(raw_samples) - 1):
                        progress_cb(image.copy())
                        next_emit = monotonic() + max(0.02, progress_interval_ms / 1000.0)
                    continue

                dxx = new[0] - stop[0]
                dyy = new[1] - stop[1]
                d = dxx * dxx + dyy * dyy
                if d < cls.DELAY_DISTANCE_QUAD:
                    if x is None or y is None:
                        ticks = max(1.0, dt / float(max(1, timer_interval_ms)))
                        radius += cls.IDLE_RADIUS_STEP * ticks
                    else:
                        radius += cls.IDLE_RADIUS_STEP
                else:
                    if radius > cls.RADIUS_THRESHOLD:
                        radius = min(radius, (dh * 0.25) ** 2)
                        color = cls._draw_color_for(prev, new, colorful_scheme)
                        halo_d = int(2.0 * radius * scale * s)
                        dot_d = int(2.0 * sqrt(radius) * scale * s)
                        n = 200.0 * max(0.0, 1.0 - 2.0 * sqrt(radius) / cls.RADIUS_THRESHOLD)
                        ch = 0 if colorful_scheme else 255
                        halo = QColor(ch, ch, ch, int(n))
                        cx, cy = map_preview(prev)
                        hx = int(cx - halo_d * 0.5)
                        hy = int(cy - halo_d * 0.5)
                        tx = int(cx - dot_d * 0.5)
                        ty = int(cy - dot_d * 0.5)
                        p.setPen(Qt.PenStyle.NoPen)
                        p.setBrush(halo)
                        p.drawEllipse(hx, hy, halo_d, halo_d)
                        p.setPen(QPen(color, max(0.0, cls.STROKE_WEIGHT * scale * s)))
                        p.setBrush(Qt.BrushStyle.NoBrush)
                        p.drawEllipse(hx, hy, halo_d, halo_d)
                        p.setPen(Qt.PenStyle.NoPen)
                        p.setBrush(color)
                        p.drawEllipse(tx, ty, dot_d, dot_d)
                    stop = new
                    radius = 0.0
                prev = new
                if progress_cb is not None and (monotonic() >= next_emit or i == len(raw_samples) - 1):
                    progress_cb(image.copy())
                    next_emit = monotonic() + max(0.02, progress_interval_ms / 1000.0)
        finally:
            p.end()

    @classmethod
    def render_preview_image_from_state(cls, state: dict[str, Any]) -> QImage:
        lw, lh = state["logical_size"]
        s = float(state["pixel_scale"])
        image = QImage(max(1, int(round(lw * s))), max(1, int(round(lh * s))), QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        cls._render_raw_on_image(
            image=image,
            raw_samples=state["raw_samples"],
            colorful_scheme=state["colorful_scheme"],
            ignore_mouse_stops=state["ignore_mouse_stops"],
            desktop_rect=tuple(state["desktop_rect"]),
            logical_size=tuple(state["logical_size"]),
            pixel_scale=float(state["pixel_scale"]),
            timer_interval_ms=int(state["timer_interval_ms"]),
        )
        return image

    @classmethod
    def render_preview_image_with_progress(
        cls,
        state: dict[str, Any],
        progress_cb: Callable[[QImage], None],
    ) -> QImage:
        lw, lh = state["logical_size"]
        s = float(state["pixel_scale"])
        image = QImage(max(1, int(round(lw * s))), max(1, int(round(lh * s))), QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        cls._render_raw_on_image(
            image=image,
            raw_samples=state["raw_samples"],
            colorful_scheme=state["colorful_scheme"],
            ignore_mouse_stops=state["ignore_mouse_stops"],
            desktop_rect=tuple(state["desktop_rect"]),
            logical_size=tuple(state["logical_size"]),
            pixel_scale=float(state["pixel_scale"]),
            timer_interval_ms=int(state["timer_interval_ms"]),
            progress_cb=progress_cb,
        )
        return image

    @classmethod
    def render_export_image_from_state(cls, state: dict[str, Any]) -> QImage:
        lw, lh = state["logical_size"]
        s = float(state["pixel_scale"])
        image = QImage(max(1, int(round(lw * s))), max(1, int(round(lh * s))), QImage.Format.Format_ARGB32_Premultiplied)
        bg = Qt.GlobalColor.black if state["colorful_scheme"] else Qt.GlobalColor.white
        image.fill(bg)
        bg_img = state.get("desktop_background")
        if isinstance(bg_img, QImage):
            p = QPainter(image)
            try:
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                if sys.platform.startswith("win") and (bg_img.width() != image.width() or bg_img.height() != image.height()):
                    # Windows mixed-DPI export path: avoid jagged desktop background when upscale is required.
                    scaled = bg_img.scaled(image.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    p.drawImage(0, 0, scaled)
                else:
                    p.drawImage(
                        QRectF(0.0, 0.0, float(image.width()), float(image.height())),
                        bg_img,
                        QRectF(0.0, 0.0, float(bg_img.width()), float(bg_img.height())),
                    )
            finally:
                p.end()
        cls._render_raw_on_image(
            image=image,
            raw_samples=state["raw_samples"],
            colorful_scheme=state["colorful_scheme"],
            ignore_mouse_stops=state["ignore_mouse_stops"],
            desktop_rect=tuple(state["desktop_rect"]),
            logical_size=tuple(state["logical_size"]),
            pixel_scale=float(state["pixel_scale"]),
            timer_interval_ms=int(state["timer_interval_ms"]),
        )
        return image

    @staticmethod
    def save_image_with_profile(image: QImage, path: str) -> bool:
        if sys.platform == "darwin":
            try:
                image.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.DisplayP3))
            except Exception:
                pass
        return image.save(path, "PNG")

    def apply_preview_image(self, image: QImage, pixel_scale: float) -> bool:
        self._ensure_buffers()
        if self._preview_pixmap is None:
            return False
        expected_w = max(1, int(round(self.width() * pixel_scale)))
        expected_h = max(1, int(round(self.height() * pixel_scale)))
        if image.width() != expected_w or image.height() != expected_h:
            return False
        pix = QPixmap.fromImage(image)
        pix.setDevicePixelRatio(pixel_scale)
        self._preview_pixmap = pix
        self.update()
        return True

    def set_ignore_mouse_stops(self, value: bool, rebuild: bool = True) -> None:
        if self._ignore_mouse_stops == value:
            return
        self._ignore_mouse_stops = value
        if rebuild:
            self._rebuild_from_raw_samples()

    def set_colorful_scheme(self, value: bool, rebuild: bool = True) -> None:
        if self._colorful_scheme == value:
            return
        self._colorful_scheme = value
        if rebuild:
            self._rebuild_from_raw_samples()

    def is_colorful_scheme(self) -> bool:
        return self._colorful_scheme

    def set_use_desktop_background(self, value: bool) -> None:
        self._use_desktop_background = value
        if value and self._desktop_background_source is None:
            self.update_desktop_background()
        self.update()

    def set_use_multiple_monitors(self, value: bool, rebuild: bool = True) -> None:
        self._use_multiple_monitors = value
        self._refresh_desktop_geometry()
        self._update_projection()
        self._ensure_buffers()
        if self._use_desktop_background:
            self.update_desktop_background()
        if rebuild:
            self._rebuild_from_raw_samples()

    def is_use_multiple_monitors(self) -> bool:
        return self._use_multiple_monitors

    def update_desktop_background(self) -> bool:
        screens = QGuiApplication.screens()
        if not screens:
            return False

        self._refresh_desktop_geometry()
        capture_scale = self._get_pixel_scale() if sys.platform.startswith("win") else 1.0
        base_w = max(1, int(round(self._desktop_rect.width() * capture_scale)))
        base_h = max(1, int(round(self._desktop_rect.height() * capture_scale)))
        base = QPixmap(base_w, base_h)
        if sys.platform.startswith("win"):
            base.setDevicePixelRatio(capture_scale)
        base.fill(Qt.GlobalColor.black)

        painter = QPainter(base)
        try:
            self._set_quality_hints(painter)
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

    def set_suspend_preview_updates(self, value: bool) -> None:
        self._suspend_preview_updates = value

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
        if self._suspend_preview_updates:
            return
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
            if self._raw_samples and self._raw_samples[-1][0] is None and self._raw_samples[-1][1] is None:
                self._raw_samples[-1] = (None, None, dt_ms)
            else:
                self._raw_samples.append((None, None, dt_ms))
        else:
            self._raw_samples.append((float(pos.x()), float(pos.y()), dt_ms))

        update_rect = QRect()

        if not no_movement and not self._suspend_preview_updates:
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
            if not self._suspend_preview_updates and not update_rect.isNull():
                self.update(update_rect)
            return

        dx = self._new_p.x - self._stop_p.x
        dy = self._new_p.y - self._stop_p.y
        d = dx * dx + dy * dy

        if d < self.DELAY_DISTANCE_QUAD:
            self._radius += self.IDLE_RADIUS_STEP
        else:
            if self._radius > self.RADIUS_THRESHOLD:
                max_radius = (self._desktop_rect.height() * 0.25) ** 2
                self._radius = min(self._radius, max_radius)
                c = self._get_draw_color()

                if not self._suspend_preview_updates:
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

        if not self._suspend_preview_updates and not update_rect.isNull():
            self.update(update_rect)

    def _draw_line(self, pix: QPixmap, p0: QPointF, p1: QPointF, color: QColor, width: float) -> None:
        p = QPainter(pix)
        try:
            self._set_quality_hints(p)
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
            self._set_quality_hints(p)
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

        prev_t = self._raw_samples[0][2]
        for x, y, t in self._raw_samples[1:]:
            dt = max(0, t - prev_t)
            prev_t = t
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
                if x is None or y is None:
                    radius += self.IDLE_RADIUS_STEP * self._idle_ticks_for_delta(dt)
                else:
                    radius += self.IDLE_RADIUS_STEP
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
            self._set_quality_hints(p)
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
        dpr = max(1.0, float(screen.devicePixelRatio()))
        if self._is_windows():
            # Keep fractional DPR on Windows to avoid aliasing on mixed-DPI monitors.
            return round(dpr, 2)
        return 2.0 if dpr >= 1.5 else 1.0

    def _get_single_screen(self):
        screens = QGuiApplication.screens()
        if not screens:
            return None
        return QGuiApplication.primaryScreen() or screens[0]
