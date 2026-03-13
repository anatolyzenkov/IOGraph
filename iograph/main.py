from pathlib import Path
import webbrowser
from math import cos, pi
import os
import plistlib
import subprocess
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from PyQt6.QtCore import QEvent, QObject, QSize, Qt, QThread, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QColor, QCursor, QDesktopServices, QGuiApplication, QIcon, QImage, QPainter
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
import sys

from .tracker import TrackCanvas
from .app.bootstrap import run_app
from .app.signals import AppSignals
from .core.update_controller import UpdateController
from .core.session_controller import SessionController
from .core.session_cache_restore import restore_session_caches
from .core.session_restore_decisions import SessionRestoreDecisions
from .core.session_storage import SessionStorage
from .core.export_controller import ExportController
from .core.tracking_controller import TrackingController
from .core.update_storage import UpdateStorageManager
from .core.update_ui_decisions import UpdateUiDecisions
from .core.update_workers import MacZipInstallWorker
from .services.settings import AppSettings, SettingsKeys
from .ui.icon_loader import build_app_icon
from .ui.desktop_snapshot_controller import DesktopSnapshotController
from .ui.layout_scaffold import build_bottom_scaffold
from .ui.menu_builder import build_main_menu
from .ui.panel_icon_logic import heart_icon_name, save_icon_name, setup_icon_name, update_desktop_icon_name
from .ui.panel_widgets import build_front_panel, build_secondary_panel
from .ui.settings_panel import build_settings_panel
from .ui.support_prompt import show_support_prompt
from .ui.toggle_button import build_toggle_button
from .ui.tray_menu import build_tray_menu
from .ui.tray_window import show_window_on_top, tray_settings_label
from .ui.update_actions import sync_install_update_actions
from .ui.update_status import apply_check_updates_status, check_updates_label

class PreviewRenderWorker(QObject):
    progress = pyqtSignal(int, object, float)  # request_id, QImage, pixel_scale
    finished = pyqtSignal(int, object, float)  # request_id, QImage, pixel_scale
    failed = pyqtSignal(str)

    def __init__(self, request_id: int, state: dict) -> None:
        super().__init__()
        self._request_id = request_id
        self._state = state

    @pyqtSlot()
    def run(self) -> None:
        try:
            image = TrackCanvas.render_preview_image_with_progress(
                self._state,
                lambda img: self.progress.emit(self._request_id, img, float(self._state["pixel_scale"])),
            )
            self.finished.emit(self._request_id, image, float(self._state["pixel_scale"]))
        except Exception as exc:
            self.failed.emit(str(exc))


class ExportRenderWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, state: dict, path: str) -> None:
        super().__init__()
        self._state = state
        self._path = path

    @pyqtSlot()
    def run(self) -> None:
        try:
            image = TrackCanvas.render_export_image_from_state(self._state)
            ok = TrackCanvas.save_image_with_profile(image, self._path)
            self.finished.emit(ok, self._path)
        except Exception:
            self.finished.emit(False, self._path)


class MainWindow(QMainWindow):
    MAIN_FRAME_WIDTH = 720
    PANEL_HEIGHT = 66
    _MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    _RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
    _APP_ICON_FILES = ("icon16.png", "icon32.png", "icon64.png", "icon128.png", "icon256.png", "icon512.png")
    _ABOUT_IOGRAPHICA_URL = "https://anatolyzenkov.com/iographica?utm_source=iograph&utm_medium=desktop&utm_campaign=about_iographica"
    _WEBSITE_URL = "https://anatolyzenkov.com/iographica?utm_source=iograph&utm_medium=desktop&utm_campaign=iograph_website"
    _GITHUB_URL = "https://github.com/anatolyzenkov/IOGraph"
    _DONATE_URL = "https://donate.stripe.com/7sY9AUcjj7W26nq7Rj67S02"
    _DONATE_UTM_SOURCE = "iograph"
    _DONATE_UTM_MEDIUM = "desktop_app"
    _DONATE_UTM_CAMPAIGN = "donate"
    _PROMPT_FIRST_IMAGE_SAVE_KEY = SettingsKeys.PROMPT_FIRST_IMAGE_SAVE_SHOWN
    _PROMPT_FIRST_RAW_SAVE_KEY = SettingsKeys.PROMPT_FIRST_RAW_SAVE_SHOWN
    _SESSION_STATE_FILE = "session_state.json"
    _SESSION_CHUNK_MS = 5 * 60 * 1000
    _VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
    _AUTO_UPDATE_INTERVAL_MS = 6 * 60 * 60 * 1000
    _UPDATE_BADGE_MAX_IGNORES = 3
    _UPDATE_STAGING_TTL_SECONDS = 24 * 60 * 60

    def __init__(self) -> None:
        super().__init__()
        self._settings = AppSettings()
        self._signals = AppSignals()
        self._update_storage = UpdateStorageManager(self._settings, self._UPDATE_STAGING_TTL_SECONDS)
        self._update_controller = UpdateController(self)
        self._update_controller.check_started.connect(lambda manual: self._signals.update_check_started.emit(manual))
        self._update_controller.check_finished.connect(self._on_update_check_finished)
        self._update_controller.download_started.connect(
            lambda latest_version, manual: self._signals.update_download_started.emit(latest_version, manual)
        )
        self._update_controller.download_finished.connect(self._on_update_download_finished)
        self._update_controller.state_changed.connect(lambda: self._set_update_check_busy(False))
        session = SessionController(self._MONTH_NAMES, self)
        self._tracking_controller = TrackingController(session, self)
        self._tracking_controller.session_tracking_started.connect(lambda: self._signals.session_tracking_started.emit())
        self._tracking_controller.session_tracking_stopped.connect(lambda: self._signals.session_tracking_stopped.emit())
        self._tracking_controller.session_reset.connect(lambda: self._signals.session_reset.emit())
        self._tracking_controller.session_restored.connect(lambda: self._signals.session_restored.emit())
        self._session_storage = SessionStorage(self._SESSION_STATE_FILE, self._SESSION_CHUNK_MS)
        self._suppress_option_handlers = False
        self._force_quit_requested = False
        self._last_system_dark_mode = False
        self._preview_render_thread: QThread | None = None
        self._preview_render_worker: PreviewRenderWorker | None = None
        self._preview_rerender_pending = False
        self._preview_request_seq = 0
        self._preview_active_request_id = 0
        self._preview_saved_toggle_visible = True
        self._preview_saved_fade_active = True
        self._export_thread: QThread | None = None
        self._export_worker: ExportRenderWorker | None = None
        self._mac_install_thread: QThread | None = None
        self._mac_install_worker: MacZipInstallWorker | None = None
        self._mac_install_progress: QProgressDialog | None = None
        self._mac_install_zip_path: Path | None = None
        self._app_version = self._resolve_app_version()
        self._setup_auto_hide_timer = QTimer(self)
        self._setup_auto_hide_timer.setSingleShot(True)
        self._setup_auto_hide_timer.setInterval(10000)
        self._setup_auto_hide_timer.timeout.connect(lambda: self._setup_btn.setChecked(False))
        self._auto_update_timer = QTimer(self)
        self._auto_update_timer.setInterval(self._AUTO_UPDATE_INTERVAL_MS)
        self._auto_update_timer.timeout.connect(lambda: self._check_for_updates(manual=False))
        self._panel_anim_timer = QTimer(self)
        self._panel_anim_timer.setInterval(20)
        self._panel_anim_timer.timeout.connect(self._on_panel_anim_tick)
        self._panel_anim_count = 0
        self._panel_anim_direction = 0
        self._panel_anim_max = 30
        self.setWindowTitle("IOGraph")
        self.setFixedWidth(self.MAIN_FRAME_WIDTH)
        self.setWindowIcon(self._app_icon())
        self._last_system_dark_mode = self._is_system_dark_mode()
        style_hints = QGuiApplication.styleHints()
        if hasattr(style_hints, "colorSchemeChanged"):
            style_hints.colorSchemeChanged.connect(lambda _scheme: self._on_system_color_scheme_changed())

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._canvas = TrackCanvas(self)
        self._desktop_snapshot_controller = DesktopSnapshotController(
            self,
            capture_desktop_background=self._canvas.update_desktop_background,
            on_status=self._status,
        )
        layout.addWidget(self._canvas, stretch=1)

        scaffold_refs = build_bottom_scaffold(
            self,
            container_layout=layout,
            panel_height=self.PANEL_HEIGHT,
            viewport_event_filter=self,
        )
        self._bottom_panel = scaffold_refs.bottom_panel
        bottom_layout = scaffold_refs.bottom_layout
        self._panels_viewport = scaffold_refs.panels_viewport
        self._front_panel = scaffold_refs.front_panel
        self._control_panel = scaffold_refs.control_panel

        toggle_refs = build_toggle_button(
            self._canvas,
            on_clicked=self._on_toggle_clicked,
            on_fade_tick=self._animate_toggle_opacity,
        )
        self._toggle_btn = toggle_refs.button
        self._canvas.installEventFilter(self)
        self._update_toggle_icon()
        self._toggle_hover = False
        self._toggle_opacity = 1.0
        self._toggle_opacity_effect = toggle_refs.opacity_effect
        self._toggle_fade_timer = toggle_refs.fade_timer

        front_refs = build_front_panel(
            self._front_panel,
            on_reset=self._reset_canvas,
            icon_loader=self._icon,
            is_windows=sys.platform.startswith("win"),
        )
        self._total_time_label = front_refs.total_time_label
        self._reset_btn = front_refs.reset_btn
        self._period_label = front_refs.period_label

        panel_refs = build_settings_panel(
            self._control_panel,
            on_refresh_desktop_snapshot=self._refresh_desktop_snapshot,
            on_update_desktop_pressed=self._on_update_desktop_pressed,
            on_update_desktop_released=self._on_update_desktop_released,
            icon_loader=self._icon,
        )
        self._ignore_stops_box = panel_refs.ignore_stops_box
        self._use_desktop_box = panel_refs.use_desktop_box
        self._update_desktop_btn = panel_refs.update_desktop_btn
        self._multi_monitor_box = panel_refs.multi_monitor_box
        self._colorful_box = panel_refs.colorful_box

        self._secondary_panel = QWidget(self._bottom_panel)
        secondary_refs = build_secondary_panel(
            self._secondary_panel,
            on_save_image=self._save_image,
            on_save_pressed=self._on_save_pressed,
            on_save_released=self._on_save_released,
            on_setup_pressed=self._on_setup_pressed,
            on_setup_released=self._on_setup_released,
            on_toggle_setup_panel=self._toggle_setup_panel,
            on_url_pressed=self._on_url_pressed,
            on_url_released=self._on_url_released,
            on_open_support=lambda: self._open_support_url("main_support_button"),
            icon_loader=self._icon,
            heart_icon_loader=self._heart_icon,
        )
        self._save_btn = secondary_refs.save_btn
        self._setup_btn = secondary_refs.setup_btn
        self._url_btn = secondary_refs.url_btn
        bottom_layout.addWidget(self._secondary_panel, stretch=0)

        self._resize_panels_for_viewport()
        self._update_panel_positions()

        self.setCentralWidget(central)
        self._setup_actions()
        self._bind_control_panel()
        self._load_settings()
        self._update_multi_monitor_controls_availability()
        self._cleanup_downloaded_update_if_installed()
        self._apply_window_geometry()
        self._load_session_state()
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(1000)
        self._ui_timer.timeout.connect(self._update_timer_label)
        self._ui_timer.start()
        app = QGuiApplication.instance()
        if app is not None:
            app.screenAdded.connect(lambda screen: self._on_screens_changed())
            app.screenRemoved.connect(lambda screen: self._on_screens_changed())
        self._setup_tray()
        self._update_install_update_actions()
        self._refresh_dpi_dependent_icons()
        self._position_toggle_button()
        self._set_tracking(True)
        self._sync_ui_state()
        if self._auto_update_action.isChecked():
            QTimer.singleShot(1200, lambda: self._check_for_updates(manual=False))
        self._status("Ready")

    def _setup_actions(self) -> None:
        refs = build_main_menu(
            self,
            on_save_image=self._save_image,
            on_save_csv=self._save_csv,
            on_reset=self._reset_canvas,
            on_quit=self._request_quit,
            on_toggle_tracking=lambda: self._set_tracking(not self._canvas.is_tracking()),
            on_ignore_stops_toggled=self._on_ignore_stops_toggled,
            on_colorful_toggled=self._on_colorful_toggled,
            on_use_desktop_toggled=self._on_use_desktop_toggled,
            on_multi_monitor_toggled=self._on_multi_monitor_toggled,
            on_refresh_desktop_snapshot=self._refresh_desktop_snapshot,
            on_about=self._show_about_dialog,
            on_check_updates=lambda: self._check_for_updates(manual=True),
            on_auto_update_toggled=self._on_auto_update_toggled,
            on_open_downloaded_update=self._open_downloaded_update,
            on_open_about_iographica=lambda: self._open_url(self._ABOUT_IOGRAPHICA_URL),
            on_open_website=lambda: self._open_url(self._WEBSITE_URL),
            on_open_source=lambda: self._open_url(self._GITHUB_URL),
            on_open_support=lambda: self._open_support_url("help_menu_support"),
        )
        self._save_image_action = refs.save_image_action
        self._save_csv_action = refs.save_csv_action
        self._reset_action = refs.reset_action
        self._tracking_toggle_action = refs.tracking_toggle_action
        self._tracking_reset_action = refs.tracking_reset_action
        self._ignore_stops_action = refs.ignore_stops_action
        self._colorful_action = refs.colorful_action
        self._use_desktop_action = refs.use_desktop_action
        self._multi_monitor_action = refs.multi_monitor_action
        self._refresh_desktop_action = refs.refresh_desktop_action
        self._check_updates_action = refs.check_updates_action
        self._auto_update_action = refs.auto_update_action
        self._install_downloaded_update_action = refs.install_downloaded_update_action

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(self._tray_state_icon(tracking=False))
        tray_exit_label = "Exit" if sys.platform.startswith("win") else "Quit"
        refs = build_tray_menu(
            self,
            tray_exit_label=tray_exit_label,
            on_open_downloaded_update=self._open_downloaded_update,
            on_toggle_tracking=lambda: self._set_tracking(not self._canvas.is_tracking()),
            on_reset=self._reset_canvas,
            on_save_image=self._save_image,
            on_save_csv=self._save_csv,
            on_toggle_settings=self._toggle_settings_from_tray,
            on_check_updates=lambda: self._check_for_updates(manual=True),
            on_auto_update_toggled=self._on_auto_update_toggled,
            on_open_about_iographica=lambda: self._open_url(self._ABOUT_IOGRAPHICA_URL),
            on_open_website=lambda: self._open_url(self._WEBSITE_URL),
            on_open_source=lambda: self._open_url(self._GITHUB_URL),
            on_open_support=lambda: self._open_support_url("tray_menu_support"),
            on_about=self._show_about_dialog,
            on_quit=self._request_quit,
        )
        self._tray_install_update_action = refs.install_update_action
        self._tray_update_sep_action = refs.update_separator_action
        self._tray_toggle_action = refs.toggle_action
        self._tray_reset_action = refs.reset_action
        self._tray_save_image_action = refs.save_image_action
        self._tray_save_csv_action = refs.save_csv_action
        self._tray_settings_action = refs.settings_action
        self._tray_check_updates_action = refs.check_updates_action
        self._tray_auto_update_action = refs.auto_update_action
        self._tray_icon.setContextMenu(refs.menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()
        self._set_auto_update_state(self._auto_update_action.isChecked())
        self._update_tray_state()

    def _bind_control_panel(self) -> None:
        self._ignore_stops_box.toggled.connect(self._ignore_stops_action.setChecked)
        self._ignore_stops_action.toggled.connect(self._ignore_stops_box.setChecked)
        self._use_desktop_box.toggled.connect(self._use_desktop_action.setChecked)
        self._use_desktop_action.toggled.connect(self._use_desktop_box.setChecked)
        self._multi_monitor_box.toggled.connect(self._multi_monitor_action.setChecked)
        self._multi_monitor_action.toggled.connect(self._multi_monitor_box.setChecked)
        self._colorful_box.toggled.connect(self._colorful_action.setChecked)
        self._colorful_action.toggled.connect(self._colorful_box.setChecked)

    def _on_toggle_clicked(self, checked: bool) -> None:
        self._set_tracking(checked)

    def _on_ignore_stops_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        self._persist_option(SettingsKeys.OPTION_IGNORE_MOUSE_STOPS, checked)
        self._canvas.set_ignore_mouse_stops(checked, rebuild=False)
        self._request_preview_rerender()
        self._sync_ui_state()

    def _reset_canvas(self) -> None:
        reset_request = self._tracking_controller.build_reset_request(self._canvas.get_elapsed_ms())
        user_confirmed = True
        if reset_request.requires_confirmation:
            answer = QMessageBox.question(
                self,
                "Reset confirmation",
                reset_request.message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            user_confirmed = answer == QMessageBox.StandardButton.Yes
        result = self._tracking_controller.apply_reset_decision_with_callbacks(
            user_confirmed=user_confirmed,
            is_tracking=self._canvas.is_tracking(),
            on_canvas_reset=self._canvas.reset,
            on_clear_session_state=self._clear_session_state,
        )
        if not result.reset_performed:
            return
        self._perform_reset_post_ui()

    def _perform_reset_post_ui(self) -> None:
        self._total_time_label.setText("Total Time")
        self._period_label.setText("Time Period")
        self._total_time_label.setVisible(False)
        self._period_label.setVisible(False)
        self._reset_btn.setVisible(False)
        self._sync_ui_state()
        self._status("Canvas reset")

    def _save_image(self) -> None:
        if self._export_thread is not None:
            self._status("Export is already running")
            return
        default_dir = self._default_save_dir()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save image",
            str(default_dir / f"{self._build_export_base_name()}.png"),
            "PNG image (*.png)",
        )
        if not path:
            return
        image_path = ExportController.ensure_image_path(path)
        self._remember_save_dir(image_path.parent)
        self._start_export_worker(str(image_path))

    def _save_csv(self) -> None:
        default_dir = self._default_save_dir()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Raw Data",
            str(default_dir / f"{self._build_export_base_name()}.csv"),
            "CSV file (*.csv)",
        )
        if not path:
            return
        csv_path = ExportController.ensure_csv_path(path)
        self._remember_save_dir(csv_path.parent)
        csv_path.write_text(self._canvas.export_csv_text(), encoding="utf-8")
        self._status("CSV saved")
        self._maybe_prompt_support_after_first_raw_save()
        self._sync_ui_state()

    def _start_export_worker(self, path: str) -> None:
        state = self._canvas.snapshot_export_render_state()
        thread, worker = ExportController.create_export_worker(
            self,
            snapshot_state=state,
            target_path=path,
            worker_cls=ExportRenderWorker,
            on_finished=self._on_export_finished,
            on_thread_closed=self._on_export_thread_closed,
        )
        self._export_thread = thread
        self._export_worker = worker
        self._status(ExportController.export_start_status())
        export_ui = ExportController.ui_state(export_in_progress=True)
        self._save_btn.setEnabled(export_ui.can_save_image)
        self._save_image_action.setEnabled(export_ui.can_save_image)
        tray_save = getattr(self, "_tray_save_image_action", None)
        if tray_save is not None:
            tray_save.setEnabled(export_ui.can_save_image)
        thread.start()

    def _on_export_finished(self, ok: bool, _path: str) -> None:
        self._status(ExportController.export_finished_status(ok))
        if ExportController.should_prompt_support_after_image_save(ok):
            self._maybe_prompt_support_after_first_image_save()
        self._sync_ui_state()

    def _maybe_prompt_support_after_first_image_save(self) -> None:
        self._maybe_prompt_support(
            key=self._PROMPT_FIRST_IMAGE_SAVE_KEY,
            title="First Graphic Saved",
            text="Done - your first IOGraph is saved.",
            informative_text="Thanks for using IOGraph. If you'd like to support the project, I'd really appreciate it.",
            source="first_image_saved_popup",
        )

    def _maybe_prompt_support_after_first_raw_save(self) -> None:
        self._maybe_prompt_support(
            key=self._PROMPT_FIRST_RAW_SAVE_KEY,
            title="RAW Data Saved",
            text="Your RAW data is saved.",
            informative_text="If IOGraph is helpful to you, you can support its continued development.",
            source="first_raw_saved_popup",
        )

    def _maybe_prompt_support(self, key: str, title: str, text: str, informative_text: str, source: str) -> None:
        if self._settings.value(key, False, bool):
            return
        self._persist_option(key, True)
        if show_support_prompt(self, title=title, text=text, informative_text=informative_text):
            self._open_support_url(source)

    def _on_export_thread_closed(self) -> None:
        self._export_thread = None
        self._export_worker = None

    def _default_save_dir(self) -> Path:
        saved = self._settings.get_str(SettingsKeys.OPTION_LAST_SAVE_DIR, "")
        if saved:
            candidate = Path(saved).expanduser()
            if candidate.exists() and candidate.is_dir():
                return candidate
        desktop = Path.home() / "Desktop"
        if desktop.exists() and desktop.is_dir():
            return desktop
        return Path.home()

    def _remember_save_dir(self, directory: Path) -> None:
        if directory.exists() and directory.is_dir():
            self._settings.set(SettingsKeys.OPTION_LAST_SAVE_DIR, str(directory), sync=True)

    def _persist_option(self, key: str, value) -> None:
        self._settings.setValue(key, value)
        self._settings.sync()

    def _on_use_desktop_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        self._persist_option(SettingsKeys.OPTION_USE_DESKTOP_BACKGROUND, checked)
        self._canvas.set_use_desktop_background(checked)
        self._refresh_desktop_action.setEnabled(checked)
        self._update_desktop_btn.setVisible(checked)
        self._update_desktop_btn.setEnabled(checked)
        self._update_update_desktop_icon()
        if checked:
            self._refresh_desktop_snapshot()
        else:
            self._status("Desktop background disabled")

    def _request_preview_rerender(self) -> None:
        if self._preview_render_thread is not None:
            self._preview_rerender_pending = True
            return
        self._canvas.set_suspend_preview_updates(True)
        self._preview_saved_toggle_visible = self._toggle_btn.isVisible()
        self._preview_saved_fade_active = self._toggle_fade_timer.isActive()
        self._toggle_fade_timer.stop()
        self._toggle_btn.setVisible(False)
        self._preview_request_seq += 1
        state = self._canvas.snapshot_preview_render_state()
        request_id = self._preview_request_seq
        self._preview_active_request_id = request_id
        thread, worker = ExportController.create_preview_worker(
            self,
            request_id=request_id,
            snapshot_state=state,
            worker_cls=PreviewRenderWorker,
            on_progress=self._on_preview_rerender_progress,
            on_finished=self._on_preview_rerender_ready,
            on_failed=self._on_preview_rerender_failed,
            on_thread_closed=self._on_preview_thread_closed,
        )
        self._preview_render_thread = thread
        self._preview_render_worker = worker
        self._status(ExportController.preview_rendering_status())
        thread.start()

    def _on_preview_rerender_progress(self, request_id: int, image: QImage, pixel_scale: float) -> None:
        if request_id != self._preview_active_request_id:
            return
        self._canvas.apply_preview_image(image, pixel_scale)
        self._status(ExportController.preview_rendering_status())

    def _on_preview_rerender_ready(self, request_id: int, image: QImage, pixel_scale: float) -> None:
        if request_id != self._preview_active_request_id:
            return
        if not self._canvas.apply_preview_image(image, pixel_scale):
            self._canvas.rebuild_from_raw_samples()
        self._status(ExportController.preview_rendered_status())
        self._sync_ui_state()

    def _on_preview_rerender_failed(self, _error: str) -> None:
        self._canvas.rebuild_from_raw_samples()
        self._sync_ui_state()

    def _on_preview_thread_closed(self) -> None:
        self._preview_render_thread = None
        self._preview_render_worker = None
        self._preview_active_request_id = 0
        self._canvas.set_suspend_preview_updates(False)
        if self._preview_saved_fade_active:
            self._toggle_fade_timer.start()
        self._toggle_btn.setVisible(self._preview_saved_toggle_visible)
        self._animate_toggle_opacity()
        if self._preview_rerender_pending:
            self._preview_rerender_pending = False
            self._request_preview_rerender()

    def _refresh_desktop_snapshot(self) -> None:
        self._desktop_snapshot_controller.refresh()

    def _on_multi_monitor_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        if checked == self._canvas.is_use_multiple_monitors():
            return
        self._persist_option(SettingsKeys.OPTION_USE_MULTIPLE_MONITORS, checked)
        self._canvas.set_suspend_preview_updates(True)
        self._canvas.set_use_multiple_monitors(checked, rebuild=False)
        if self._use_desktop_action.isChecked():
            self._refresh_desktop_snapshot()
        self._apply_window_geometry()
        self._request_preview_rerender()
        self._sync_ui_state()

    def _on_screens_changed(self) -> None:
        self._update_multi_monitor_controls_availability()
        self._apply_window_geometry()

    def _update_multi_monitor_controls_availability(self) -> None:
        has_multiple = len(QGuiApplication.screens()) > 1
        self._multi_monitor_action.setEnabled(has_multiple)
        self._multi_monitor_box.setEnabled(has_multiple)

    def _load_settings(self) -> None:
        ignore_stops = self._settings.get_bool(SettingsKeys.OPTION_IGNORE_MOUSE_STOPS, False)
        colorful = self._settings.get_bool(SettingsKeys.OPTION_COLORFUL_SCHEME, False)
        use_desktop = self._settings.get_bool(SettingsKeys.OPTION_USE_DESKTOP_BACKGROUND, False)
        use_multi_monitor = self._settings.get_bool(SettingsKeys.OPTION_USE_MULTIPLE_MONITORS, True)
        auto_update = self._settings.get_bool(SettingsKeys.OPTION_AUTOMATIC_UPDATE, True)

        # Apply to runtime first (source of truth), then mirror in UI without signal side-effects.
        self._canvas.set_ignore_mouse_stops(ignore_stops, rebuild=False)
        self._canvas.set_colorful_scheme(colorful, rebuild=False)
        self._canvas.set_use_multiple_monitors(use_multi_monitor, rebuild=False)
        self._canvas.set_use_desktop_background(use_desktop)

        self._set_checked_silent(self._ignore_stops_action, ignore_stops)
        self._set_checked_silent(self._ignore_stops_box, ignore_stops)
        self._set_checked_silent(self._colorful_action, colorful)
        self._set_checked_silent(self._colorful_box, colorful)
        self._set_checked_silent(self._multi_monitor_action, use_multi_monitor)
        self._set_checked_silent(self._multi_monitor_box, use_multi_monitor)
        self._set_checked_silent(self._use_desktop_action, use_desktop)
        self._set_checked_silent(self._use_desktop_box, use_desktop)

        self._refresh_desktop_action.setEnabled(use_desktop)
        self._update_desktop_btn.setVisible(use_desktop)
        self._update_desktop_btn.setEnabled(use_desktop)
        self._update_update_desktop_icon()
        self._set_auto_update_state(auto_update)
        self._sync_ui_state()

    def _save_settings(self) -> None:
        self._settings.set_many(
            {
                SettingsKeys.OPTION_IGNORE_MOUSE_STOPS: self._ignore_stops_action.isChecked(),
                SettingsKeys.OPTION_COLORFUL_SCHEME: self._colorful_action.isChecked(),
                SettingsKeys.OPTION_USE_MULTIPLE_MONITORS: self._multi_monitor_action.isChecked(),
                SettingsKeys.OPTION_USE_DESKTOP_BACKGROUND: self._use_desktop_action.isChecked(),
                SettingsKeys.OPTION_AUTOMATIC_UPDATE: self._auto_update_action.isChecked(),
            },
            sync=True,
        )

    def _save_session_state(self) -> None:
        signature = self._canvas.render_cache_signature()
        preview_saved = self._canvas.export_preview_cache(str(self._session_storage.preview_cache_path()))
        desktop_saved = self._canvas.export_desktop_background_cache(str(self._session_storage.desktop_cache_path()))
        raw_storage = self._session_storage.write_raw_chunks(self._canvas.export_raw_samples())
        session_times = self._tracking_controller.session_timestamps_payload()
        state = {
            "version": 1,
            "session_started_at": session_times["session_started_at"],
            "session_ended_at": session_times["session_ended_at"],
            "raw_storage": raw_storage,
            "render_signature": signature,
            "preview_cache_saved": preview_saved,
            "desktop_cache_saved": desktop_saved,
        }
        self._session_storage.save_state(state)

    def _load_session_state(self) -> None:
        payload = self._session_storage.load_state()
        if payload is None:
            if self._use_desktop_action.isChecked():
                self._refresh_desktop_snapshot()
            return

        raw_samples = self._session_storage.read_raw_samples(payload)
        signature = payload.get("render_signature")
        use_cache = signature == self._canvas.render_cache_signature()
        use_desktop_bg = self._use_desktop_action.isChecked()
        if raw_samples:
            self._canvas.load_raw_samples(raw_samples, rebuild=False)
        cache_restore = restore_session_caches(
            payload=payload,
            use_cache=use_cache,
            use_desktop_background=use_desktop_bg,
            preview_cache_path=self._session_storage.preview_cache_path(),
            desktop_cache_path=self._session_storage.desktop_cache_path(),
            load_preview_cache=self._canvas.load_preview_cache,
            load_desktop_cache=self._canvas.load_desktop_background_cache,
        )
        if SessionRestoreDecisions.needs_preview_rerender(cache_restore.loaded_preview_cache):
            self._request_preview_rerender()
        if SessionRestoreDecisions.needs_desktop_refresh(use_desktop_bg, cache_restore.loaded_desktop_cache):
            self._refresh_desktop_snapshot()

        started_raw = payload.get("session_started_at")
        ended_raw = payload.get("session_ended_at")
        self._tracking_controller.restore_session_from_payload(started_raw, ended_raw, self._canvas.get_elapsed_ms())

        if self._canvas.get_elapsed_ms() > 0:
            self._update_timer_label()

    def _clear_session_state(self) -> None:
        self._session_storage.clear_state_files()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if getattr(self, "_tray_icon", None) is not None and not self._force_quit_requested:
            self.hide()
            event.ignore()
            return
        if not self._confirm_exit():
            self._force_quit_requested = False
            event.ignore()
            return
        self._save_session_state()
        self._save_settings()
        super().closeEvent(event)

    def _update_timer_label(self) -> None:
        self._refresh_icons_if_system_theme_changed()
        elapsed_ms = self._canvas.get_elapsed_ms()
        tracking = self._canvas.is_tracking()
        if not self._tracking_controller.should_show_timer_labels(elapsed_ms, tracking):
            return
        self._total_time_label.setText(self._tracking_controller.tracking_time_text(elapsed_ms))
        self._period_label.setText(self._tracking_controller.period_label())
        self._total_time_label.setVisible(True)
        self._period_label.setVisible(True)
        self._reset_btn.setVisible(self._tracking_controller.ui_state(elapsed_ms, tracking).reset_button_visible)
        self._sync_ui_state()

    def _build_export_base_name(self) -> str:
        return self._tracking_controller.export_base_name(self._canvas.get_elapsed_ms(), app_name="IOGraphica")

    def _set_tracking(self, enabled: bool) -> None:
        transition = self._tracking_controller.set_tracking_with_callbacks(
            enabled,
            on_canvas_start=self._canvas.start_tracking,
            on_canvas_stop=self._canvas.stop_tracking,
        )
        self._toggle_btn.setChecked(transition.enabled)
        self._sync_ui_state()
        self._status(transition.status_message)

    def _toggle_setup_panel(self, checked: bool) -> None:
        self._panel_anim_direction = 1 if checked else -1
        self._panel_anim_timer.start()
        self._setup_btn.setIcon(self._icon(setup_icon_name(checked=checked, pressed=False)))
        self._update_tray_state()

    def _apply_window_geometry(self) -> None:
        screen_width, screen_height = self._get_screen_bounds(self._multi_monitor_action.isChecked())
        scale = self.MAIN_FRAME_WIDTH / max(1, screen_width)
        preview_height = max(100, int(screen_height * scale))
        self._canvas.setFixedSize(self.MAIN_FRAME_WIDTH, preview_height)
        self._bottom_panel.setFixedWidth(self.MAIN_FRAME_WIDTH)
        self.adjustSize()
        menu_h = self.menuBar().sizeHint().height() if self.menuBar() is not None else 0
        total_h = menu_h + preview_height + self._bottom_panel.height()
        self.setFixedSize(self.MAIN_FRAME_WIDTH, total_h)
        self._refresh_dpi_dependent_icons()
        self._position_toggle_button()

    @staticmethod
    def _get_screen_bounds(use_multiple_monitors: bool) -> tuple[int, int]:
        screens = QGuiApplication.screens()
        if not screens:
            return (1920, 1080)
        if use_multiple_monitors and len(screens) > 1:
            union = screens[0].geometry()
            for s in screens[1:]:
                union = union.united(s.geometry())
            return (max(1, union.width()), max(1, union.height()))
        primary = QGuiApplication.primaryScreen() or screens[0]
        g = primary.geometry()
        return (max(1, g.width()), max(1, g.height()))

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        canvas = getattr(self, "_canvas", None)
        panels_viewport = getattr(self, "_panels_viewport", None)
        if obj is canvas:
            event_type = event.type()
            if event_type == QEvent.Type.Resize:
                self._position_toggle_button()
            elif event_type in (QEvent.Type.MouseMove, QEvent.Type.Enter, QEvent.Type.Leave):
                self._update_toggle_hover_state()
        elif obj is panels_viewport and event.type() == QEvent.Type.Resize:
            self._resize_panels_for_viewport()
            self._update_panel_positions()
        return super().eventFilter(obj, event)

    def _position_toggle_button(self) -> None:
        x = (self._canvas.width() - self._toggle_btn.width()) // 2
        y = (self._canvas.height() - self._toggle_btn.height()) // 2
        self._toggle_btn.move(max(0, x), max(0, y))
        self._toggle_btn.raise_()

    def _update_toggle_icon(self) -> None:
        self._toggle_btn.setIcon(self._icon("PauseBtn.png" if self._toggle_btn.isChecked() else "RecordBtn.png"))

    def _animate_toggle_opacity(self) -> None:
        self._update_toggle_hover_state()
        target = 1.0 if self._toggle_hover or not self._canvas.is_tracking() else 0.0
        if abs(self._toggle_opacity - target) < 0.02:
            self._toggle_opacity = target
        elif self._toggle_opacity < target:
            self._toggle_opacity = min(1.0, self._toggle_opacity + 0.12)
        else:
            self._toggle_opacity = max(0.0, self._toggle_opacity - 0.12)
        self._toggle_opacity_effect.setOpacity(self._toggle_opacity)

    def _update_toggle_hover_state(self) -> None:
        pos = self._canvas.mapFromGlobal(QCursor.pos())
        cx = self._toggle_btn.x() + self._toggle_btn.width() // 2
        cy = self._toggle_btn.y() + self._toggle_btn.height() // 2
        dx = cx - pos.x()
        dy = cy - pos.y()
        self._toggle_hover = dx * dx + dy * dy < 40 * 40

    def _update_save_icon(self) -> None:
        self._save_btn.setIcon(
            self._icon(save_icon_name(enabled=self._save_btn.isEnabled(), pressed=self._save_btn.isDown()))
        )

    def _on_save_pressed(self) -> None:
        self._save_btn.setIcon(self._icon(save_icon_name(enabled=self._save_btn.isEnabled(), pressed=True)))

    def _on_save_released(self) -> None:
        self._update_save_icon()

    def _on_setup_pressed(self) -> None:
        self._setup_btn.setIcon(
            self._icon(setup_icon_name(checked=self._setup_btn.isChecked(), pressed=True))
        )

    def _on_setup_released(self) -> None:
        self._setup_btn.setIcon(
            self._icon(setup_icon_name(checked=self._setup_btn.isChecked(), pressed=False))
        )

    def _on_update_desktop_pressed(self) -> None:
        self._update_desktop_btn.setIcon(
            self._icon(update_desktop_icon_name(enabled=self._update_desktop_btn.isEnabled(), pressed=True))
        )

    def _on_update_desktop_released(self) -> None:
        self._update_update_desktop_icon()

    def _update_update_desktop_icon(self) -> None:
        self._update_desktop_btn.setIcon(
            self._icon(
                update_desktop_icon_name(
                    enabled=self._update_desktop_btn.isEnabled(),
                    pressed=self._update_desktop_btn.isDown(),
                )
            )
        )

    def _on_url_pressed(self) -> None:
        self._url_btn.setIcon(self._heart_icon(heart_icon_name(pressed=True)))

    def _on_url_released(self) -> None:
        self._update_url_icon()

    def _update_url_icon(self) -> None:
        self._url_btn.setIcon(self._heart_icon(heart_icon_name(pressed=self._url_btn.isDown())))

    def _heart_icon(self, name: str) -> QIcon:
        # Donation icon should stay visually stable across system palette changes.
        return QIcon(str(self._resource_file_for_dpi(name)))

    def _icon(self, name: str) -> QIcon:
        themed_name = self._themed_icon_name(name)
        return QIcon(str(self._resource_file_for_dpi(themed_name)))

    def _themed_icon_name(self, name: str) -> str:
        if not self._is_system_dark_mode():
            return name
        base = self._RESOURCE_DIR / name
        themed = base.with_name(f"{base.stem}_dark{base.suffix}")
        return themed.name if themed.exists() else name

    def _is_system_dark_mode(self) -> bool:
        style_hints = QGuiApplication.styleHints()
        if not hasattr(style_hints, "colorScheme"):
            return False
        return style_hints.colorScheme() == Qt.ColorScheme.Dark

    def _on_system_color_scheme_changed(self) -> None:
        self._last_system_dark_mode = self._is_system_dark_mode()
        self._refresh_dpi_dependent_icons()

    def _refresh_icons_if_system_theme_changed(self) -> None:
        dark_mode = self._is_system_dark_mode()
        if dark_mode == self._last_system_dark_mode:
            return
        self._last_system_dark_mode = dark_mode
        self._refresh_dpi_dependent_icons()

    def _tray_icon_name(self, tracking: bool) -> str:
        if sys.platform.startswith("win"):
            return "icon32.png"
        if sys.platform == "darwin":
            name = "MacOSTrayIconPause.png" if tracking else "MacOSTrayIconRecord.png"
            if (self._RESOURCE_DIR / name).exists():
                return name
        return "MenuBarIconPause.png" if tracking else "MenuBarIconRecord.png"

    def _tray_state_icon(self, tracking: bool) -> QIcon:
        icon = QIcon(str(self._resource_file_for_dpi(self._tray_icon_name(tracking))))
        if sys.platform == "darwin":
            icon.setIsMask(True)
            return icon
        if sys.platform.startswith("win"):
            return icon
        if self._should_show_update_badge():
            size = icon.actualSize(QSize(22, 22))
            pm = icon.pixmap(size)
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            d = max(5, min(pm.width(), pm.height()) // 3)
            x = pm.width() - d - 1
            y = 1
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 59, 48))
            p.drawEllipse(x, y, d, d)
            p.end()
            return QIcon(pm)
        return icon

    def _should_show_update_badge(self) -> bool:
        if sys.platform == "darwin":
            return False
        if not self._has_pending_downloaded_update():
            return False
        ignores = int(self._settings.value(SettingsKeys.UPDATE_INSTALL_IGNORE_COUNT, 0, int))
        return ignores < self._UPDATE_BADGE_MAX_IGNORES

    def _app_icon(self) -> QIcon:
        return build_app_icon(self._RESOURCE_DIR, self._APP_ICON_FILES)

    def _resource_file_for_dpi(self, name: str) -> Path:
        base = self._RESOURCE_DIR / name
        if not self._is_high_dpi_screen():
            return base
        hi = self._RESOURCE_DIR / f"{base.stem}@2x{base.suffix}"
        return hi if hi.exists() else base

    def _is_high_dpi_screen(self) -> bool:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return False
        return screen.devicePixelRatio() >= 1.5

    def _refresh_dpi_dependent_icons(self) -> None:
        self._update_toggle_icon()
        self._update_save_icon()
        self._on_setup_released()
        self._on_update_desktop_released()
        self._update_url_icon()
        if self._reset_btn.isDown():
            self._reset_btn.setIcon(self._icon("ResetPressedBtn.png"))
        else:
            self._reset_btn.setIcon(self._icon("ResetBtn.png"))
        if getattr(self, "_tray_icon", None) is not None:
            self._update_tray_state()

    def _on_colorful_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        if checked == self._canvas.is_colorful_scheme():
            return
        self._persist_option(SettingsKeys.OPTION_COLORFUL_SCHEME, checked)
        self._canvas.set_colorful_scheme(checked, rebuild=False)
        self._request_preview_rerender()
        self._refresh_dpi_dependent_icons()
        self._sync_ui_state()

    def _confirm_exit(self) -> bool:
        # Session is persisted on close, no destructive-exit warning is needed.
        return True

    def _set_option_checked(self, action: QAction, checkbox: QCheckBox, value: bool) -> None:
        self._suppress_option_handlers = True
        try:
            action.setChecked(value)
            checkbox.setChecked(value)
        finally:
            self._suppress_option_handlers = False

    def _restore_option_from_runtime(self, action: QAction, checkbox: QCheckBox, value: bool) -> None:
        self._set_checked_silent(action, value)
        self._set_checked_silent(checkbox, value)

    def _defer_restore_option_from_runtime(self, action: QAction, checkbox: QCheckBox, value: bool) -> None:
        QTimer.singleShot(0, lambda: self._restore_option_from_runtime(action, checkbox, value))

    @staticmethod
    def _set_checked_silent(widget, value: bool) -> None:
        prev = widget.blockSignals(True)
        try:
            widget.setChecked(value)
        finally:
            widget.blockSignals(prev)

    def _request_quit(self) -> None:
        self._force_quit_requested = True
        if sys.platform.startswith("win") and not self.isVisible():
            if not self._confirm_exit():
                self._force_quit_requested = False
                return
            self._save_session_state()
            self._save_settings()
            tray = getattr(self, "_tray_icon", None)
            if tray is not None:
                tray.hide()
            app = QApplication.instance()
            if app is not None:
                app.quit()
            return
        self.close()

    def _on_panel_anim_tick(self) -> None:
        self._panel_anim_count += self._panel_anim_direction
        self._panel_anim_count = max(0, min(self._panel_anim_max, self._panel_anim_count))
        if self._panel_anim_direction == 1 and self._panel_anim_count == self._panel_anim_max:
            self._panel_anim_timer.stop()
        elif self._panel_anim_direction == -1 and self._panel_anim_count == 0:
            self._panel_anim_timer.stop()
        self._update_panel_positions()

    def _update_panel_positions(self) -> None:
        n = self._smooth(self._panel_anim_count / self._panel_anim_max, 1.0)
        y_front = -int(self.PANEL_HEIGHT * n)
        y_control = int(self.PANEL_HEIGHT * (1.0 - n))
        self._front_panel.move(0, y_front)
        self._control_panel.move(0, y_control)

    def _resize_panels_for_viewport(self) -> None:
        w = max(1, self._panels_viewport.width())
        h = self.PANEL_HEIGHT
        self._front_panel.setGeometry(0, self._front_panel.y(), w, h)
        self._control_panel.setGeometry(0, self._control_panel.y(), w, h)

    @staticmethod
    def _smooth(n: float, f: float) -> float:
        f = max(0.6, f)
        if n < 0.5:
            return ((1.0 - cos(pi * n)) ** f) * 0.5
        return 0.5 + (1.0 - (1.0 - cos(pi * (1.0 - n))) ** f) * 0.5

    def _open_url(self, url: str) -> None:
        webbrowser.open(self._append_utm_term(url))

    def _open_support_url(self, source: str) -> None:
        self._open_url(self._build_donate_url(source))

    def _build_donate_url(self, source: str) -> str:
        parts = urlsplit(self._DONATE_URL)
        params = dict(parse_qsl(parts.query, keep_blank_values=True))
        params["utm_source"] = self._DONATE_UTM_SOURCE
        params["utm_medium"] = self._DONATE_UTM_MEDIUM
        params["utm_campaign"] = self._DONATE_UTM_CAMPAIGN
        params["utm_content"] = source
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))

    def _append_utm_term(self, url: str) -> str:
        try:
            parts = urlsplit(url)
            params = dict(parse_qsl(parts.query, keep_blank_values=True))
            if "utm_source" not in params:
                return url
            params["utm_term"] = self._app_version
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))
        except Exception:
            return url

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About IOGraph",
            f"IOGraph {self._app_version}\nTurn your routine work into contemporary art",
        )

    def _resolve_app_version(self) -> str:
        env_version = str(os.environ.get("IOGRAPH_VERSION", "")).replace("\ufeff", "").strip()
        if env_version:
            return env_version
        if getattr(sys, "frozen", False):
            try:
                exe_path = Path(sys.executable).resolve()
                plist_path = exe_path.parent.parent / "Info.plist"
                if plist_path.exists():
                    payload = plistlib.loads(plist_path.read_bytes())
                    plist_version = str(payload.get("CFBundleShortVersionString", "")).strip()
                    if plist_version:
                        return plist_version
            except Exception:
                pass
            try:
                version_candidates = []
                meipass = getattr(sys, "_MEIPASS", "")
                if meipass:
                    version_candidates.append(Path(meipass) / "VERSION")
                version_candidates.append(Path(sys.executable).resolve().parent / "VERSION")
                for version_path in version_candidates:
                    if version_path.exists():
                        file_version = version_path.read_text(encoding="utf-8").replace("\ufeff", "").strip()
                        if file_version:
                            return file_version
            except Exception:
                pass
        try:
            if self._VERSION_FILE.exists():
                file_version = self._VERSION_FILE.read_text(encoding="utf-8").replace("\ufeff", "").strip()
                if file_version:
                    return file_version
        except Exception:
            pass
        return "dev"

    @staticmethod
    def _normalize_version_tag(version: str) -> str:
        return UpdateStorageManager.normalize_version_tag(version)

    def _cleanup_downloaded_update_if_installed(self) -> None:
        self._update_storage.cleanup_downloaded_update_if_installed(self._app_version)

    def _check_for_updates(self, manual: bool) -> None:
        if self._update_controller.is_downloading():
            if manual:
                QMessageBox.information(
                    self,
                    "Check for Updates",
                    "Update download is in progress.\nPlease wait until it finishes.",
                )
            return
        if self._update_controller.is_checking():
            if manual:
                QMessageBox.information(
                    self,
                    "Check for Updates",
                    "Update check is already running.\nPlease wait a few seconds and try again.",
                )
            return
        if not self._update_controller.start_check(self._app_version, manual):
            return
        self._set_update_check_busy(True)
        self._status("Checking for updates...")
        return

    def _on_update_check_finished(self, manual: bool, result: dict) -> None:
        self._signals.update_check_finished.emit(manual, result)
        ok = bool(result.get("ok", False))
        if not ok:
            if manual:
                QMessageBox.warning(self, "Check for Updates", f"Unable to check for updates:\n{result.get('error', '')}")
            return
        has_update = bool(result.get("has_update", False))
        latest_tag = str(result.get("latest_tag", ""))
        latest_version = str(result.get("latest_version", ""))
        release_url = str(result.get("url", ""))
        asset_url = str(result.get("asset_url", ""))
        asset_name = str(result.get("asset_name", ""))
        if not has_update:
            if manual:
                QMessageBox.information(self, "Check for Updates", f"You are up to date ({self._app_version}).")
            self._status("No updates found")
            return
        if not manual:
            last_downloaded = self._settings.value(SettingsKeys.UPDATE_LAST_AUTO_DOWNLOADED_VERSION, "", str)
            if last_downloaded == latest_tag:
                saved_path = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)
                if saved_path and Path(saved_path).exists():
                    return
                self._settings.remove(SettingsKeys.UPDATE_LAST_AUTO_DOWNLOADED_VERSION)
        if self._is_latest_update_already_downloaded(latest_tag):
            if manual:
                downloaded_path = self._pending_downloaded_update_path()
                message = UpdateUiDecisions.already_downloaded_prompt(downloaded_path)
                answer = QMessageBox.question(
                    self,
                    "Update Ready",
                    message,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self._open_downloaded_update()
            return
        if self._update_controller.is_downloading():
            return
        if manual:
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            answer = QMessageBox.question(
                self,
                "Update Available",
                f"IOGraph {latest_version} is available.\n\nDownload now?",
                buttons,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if not asset_url or not asset_name:
            if manual and release_url:
                self._open_url(release_url)
            return
        self._start_update_download(latest_version, asset_url, asset_name, manual)
        self._status("Update available")

    def _start_update_download(self, latest_version: str, asset_url: str, asset_name: str, manual: bool) -> None:
        if self._update_controller.is_downloading():
            return
        target = self._update_storage.update_target_path(asset_name, latest_version, manual)
        self._update_storage.cleanup_partial_update_files(target.parent, asset_name)
        self._update_storage.clear_stale_download_metadata_for(latest_version)
        if not self._update_controller.start_download(latest_version, asset_url, str(target), manual):
            return
        self._set_update_check_busy(True)
        self._status("Downloading update...")
        return

    def _update_target_path(self, asset_name: str, latest_version: str, manual: bool) -> Path:
        return self._update_storage.update_target_path(asset_name, latest_version, manual)

    def _updates_cache_dir(self) -> Path:
        return self._update_storage.updates_cache_dir()

    @staticmethod
    def _cleanup_partial_update_files(target_dir: Path, asset_name: str) -> None:
        UpdateStorageManager.cleanup_partial_update_files(target_dir, asset_name)

    def _clear_stale_download_metadata_for(self, latest_version: str) -> None:
        self._update_storage.clear_stale_download_metadata_for(latest_version)

    def _cleanup_stale_update_temp_files(self) -> None:
        self._update_storage.cleanup_stale_update_temp_files()

    @staticmethod
    def _auto_update_cache_name(asset_name: str, latest_version: str) -> str:
        return UpdateStorageManager.auto_update_cache_name(asset_name, latest_version)

    def _on_update_download_finished(self, ok: bool, path: str, error: str, latest_version: str, manual: bool) -> None:
        self._signals.update_download_finished.emit(ok, path, error, manual)
        if not ok:
            if manual:
                QMessageBox.warning(self, "Update Download", f"Failed to download IOGraph {latest_version}:\n{error}")
            else:
                self._status("Background update download failed")
            return
        local = Path(path)
        self._update_storage.register_download_result(local, latest_version, manual)
        self._update_install_update_actions()
        prompt_message = UpdateUiDecisions.install_ready_prompt(local)
        prompt = QMessageBox.question(
            self,
            "Update Ready",
            prompt_message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if prompt == QMessageBox.StandardButton.Yes:
            self._update_storage.reset_install_ignore_count()
            self._open_update_artifact(local)
            self._status("Update downloaded")
            return
        self._update_storage.increment_install_ignore_count()
        self._update_tray_state()
        self._status("Update downloaded")

    def _set_update_check_busy(self, busy: bool) -> None:
        label = check_updates_label(
            is_downloading=self._update_controller.is_downloading(),
            is_checking=self._update_controller.is_checking(),
        )
        apply_check_updates_status(
            label=label,
            menu_action=getattr(self, "_check_updates_action", None),
            tray_action=getattr(self, "_tray_check_updates_action", None),
        )
        self._update_install_update_actions()

    def _update_install_update_actions(self) -> None:
        has_file = self._has_pending_downloaded_update()
        downloaded = self._pending_downloaded_update_path()
        sync_install_update_actions(
            has_downloaded_update=has_file,
            downloaded_path=downloaded,
            menu_action=getattr(self, "_install_downloaded_update_action", None),
            tray_action=getattr(self, "_tray_install_update_action", None),
            tray_separator_action=getattr(self, "_tray_update_sep_action", None),
        )
        self._update_tray_state()

    def _has_pending_downloaded_update(self) -> bool:
        return self._update_storage.has_pending_downloaded_update()

    def _pending_downloaded_update_path(self) -> Path | None:
        return self._update_storage.pending_downloaded_update_path()

    @staticmethod
    def _is_zip_update(path: Path | None) -> bool:
        return UpdateUiDecisions.is_zip_update(path)

    def _is_latest_update_already_downloaded(self, latest_tag: str) -> bool:
        has_downloaded, stale_cleaned = self._update_storage.is_latest_update_already_downloaded(latest_tag)
        if stale_cleaned:
            self._update_install_update_actions()
        return has_downloaded

    def _open_downloaded_update(self) -> None:
        path = self._settings.value(SettingsKeys.UPDATE_LAST_DOWNLOADED_PATH, "", str)
        if not path:
            QMessageBox.information(self, "Install Downloaded Update", "No downloaded update was found.")
            return
        local = Path(path)
        if not local.exists():
            self._update_storage.clear_missing_download_file_state()
            self._update_install_update_actions()
            QMessageBox.information(self, "Install Downloaded Update", "Downloaded update file no longer exists.")
            return
        self._update_storage.reset_install_ignore_count()
        self._open_update_artifact(local)

    def _open_update_artifact(self, path: Path) -> None:
        if self._is_zip_update(path) and sys.platform.startswith("win"):
            try:
                subprocess.Popen(["explorer.exe", "/select,", str(path)])
            except Exception:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
            return
        if self._is_zip_update(path) and sys.platform == "darwin":
            self._start_macos_zip_install(path)
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        if path.suffix.lower() == ".dmg":
            QTimer.singleShot(650, self._request_quit)

    def _start_macos_zip_install(self, zip_path: Path) -> None:
        if self._mac_install_thread is not None:
            QMessageBox.information(self, "Install Downloaded Update", "Update installation is already in progress.")
            return
        if not getattr(sys, "frozen", False):
            QMessageBox.warning(self, "Install Downloaded Update", "Automatic install is available only in bundled app.")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(zip_path)))
            return
        current_team = ""
        current_app = self._current_macos_app_bundle_path()
        if current_app is not None:
            current_team = MacZipInstallWorker._codesign_team_identifier(current_app)
        progress = QProgressDialog("Preparing update installation...", "", 0, 0, self)
        progress.setWindowTitle("Installing Update")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setValue(0)
        progress.show()
        self._mac_install_progress = progress
        self._mac_install_zip_path = zip_path
        thread = QThread(self)
        worker = MacZipInstallWorker(str(zip_path), "/Applications/IOGraph.app", current_team, os.getpid())
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_macos_zip_install_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_macos_zip_install_thread_closed)
        self._mac_install_thread = thread
        self._mac_install_worker = worker
        thread.start()

    def _on_macos_zip_install_finished(self, ok: bool, error: str) -> None:
        progress = self._mac_install_progress
        if progress is not None:
            progress.hide()
            progress.deleteLater()
            self._mac_install_progress = None
        zip_path = self._mac_install_zip_path
        if ok:
            self._request_quit()
            return
        QMessageBox.warning(
            self,
            "Install Downloaded Update",
            (
                "Automatic install failed. Opening downloaded package for manual installation."
                if not error
                else f"Automatic install failed: {error}\n\nOpening downloaded package for manual installation."
            ),
        )
        if zip_path is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(zip_path)))

    def _on_macos_zip_install_thread_closed(self) -> None:
        self._mac_install_thread = None
        self._mac_install_worker = None
        self._mac_install_zip_path = None

    @staticmethod
    def _current_macos_app_bundle_path() -> Path | None:
        if sys.platform != "darwin":
            return None
        if not getattr(sys, "frozen", False):
            return None
        try:
            exe = Path(sys.executable).resolve()
        except Exception:
            return None
        for parent in exe.parents:
            if parent.suffix.lower() == ".app":
                return parent
        return None

    def _status(self, _message: str) -> None:
        # Java version has no Qt status bar; keep this as no-op to avoid affecting layout height.
        return

    def _on_auto_update_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        self._set_auto_update_state(checked)
        self._persist_option(SettingsKeys.OPTION_AUTOMATIC_UPDATE, checked)

    def _set_auto_update_state(self, checked: bool) -> None:
        self._suppress_option_handlers = True
        try:
            self._auto_update_action.setChecked(checked)
            tray_auto = getattr(self, "_tray_auto_update_action", None)
            if tray_auto is not None:
                tray_auto.setChecked(checked)
        finally:
            self._suppress_option_handlers = False
        if checked:
            self._auto_update_timer.start()
        else:
            self._auto_update_timer.stop()

    def event(self, event) -> bool:  # type: ignore[override]
        event_type = event.type()
        theme_change = getattr(QEvent.Type, "ThemeChange", None)
        if event_type == QEvent.Type.WindowDeactivate and self._setup_btn.isChecked():
            self._setup_auto_hide_timer.start()
        elif event_type == QEvent.Type.WindowActivate:
            self._setup_auto_hide_timer.stop()
        elif event_type in tuple(
            t
            for t in (QEvent.Type.ApplicationPaletteChange, QEvent.Type.PaletteChange, theme_change)
            if t is not None
        ):
            self._refresh_icons_if_system_theme_changed()
        return super().event(event)

    def _toggle_settings_from_tray(self) -> None:
        self._setup_btn.setChecked(not self._setup_btn.isChecked())
        self._show_on_top()
        self._update_tray_state()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_on_top()

    def _show_on_top(self) -> None:
        show_window_on_top(self)

    def _update_tray_state(self) -> None:
        tray = getattr(self, "_tray_icon", None)
        if tray is None or not hasattr(self, "_tray_toggle_action"):
            return
        elapsed = self._canvas.get_elapsed_ms()
        tracking = self._canvas.is_tracking()
        ui_state = self._tracking_controller.ui_state(elapsed, tracking)
        self._tray_toggle_action.setText(ui_state.toggle_label)
        self._tray_save_image_action.setEnabled(ui_state.can_save)
        self._tray_save_csv_action.setEnabled(ui_state.can_save)
        self._tray_reset_action.setEnabled(ui_state.can_reset)
        self._tray_settings_action.setText(tray_settings_label(self._setup_btn.isChecked()))
        tray.setIcon(self._tray_state_icon(tracking))

    def _sync_ui_state(self) -> None:
        elapsed = self._canvas.get_elapsed_ms()
        tracking = self._canvas.is_tracking()
        ui_state = self._tracking_controller.ui_state(elapsed, tracking)

        self._toggle_btn.setChecked(tracking)
        self._update_toggle_icon()

        self._save_btn.setEnabled(ui_state.can_save)
        self._update_save_icon()

        self._reset_action.setEnabled(ui_state.can_reset)
        self._tracking_reset_action.setEnabled(ui_state.can_reset)
        self._save_image_action.setEnabled(ui_state.can_save)
        self._save_csv_action.setEnabled(ui_state.can_save)

        self._tracking_toggle_action.setText(ui_state.toggle_label)

        # Safety net: if async preview rerender already finished, ensure central toggle is visible.
        if self._preview_render_thread is None and not self._toggle_btn.isVisible():
            self._toggle_btn.setVisible(True)

        self._update_tray_state()


def main() -> None:
    sys.exit(run_app(MainWindow))


if __name__ == "__main__":
    main()
