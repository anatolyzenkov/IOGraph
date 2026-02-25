from pathlib import Path
from datetime import datetime
import webbrowser
from math import cos, pi

from PyQt6.QtCore import QEvent, QSettings, QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QCursor, QFont, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
import sys

from .tracker import TrackCanvas


class MainWindow(QMainWindow):
    MAIN_FRAME_WIDTH = 465
    PANEL_HEIGHT = 66
    _MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    _RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
    _APP_ICON_FILES = ("icon16.png", "icon32.png", "icon64.png", "icon128.png", "icon256.png", "icon512.png")
    _GITHUB_URL = "https://github.com/anatolyzenkov/iograph"
    _FACEBOOK_URL = "https://www.facebook.com/pages/IOGraphica/317794951637"
    _WEBSITE_URL = "https://iographica.com/"

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("iographica", "IOGraphPython")
        self._session_started_at: datetime | None = None
        self._session_ended_at: datetime | None = None
        self._suppress_option_handlers = False
        self._force_quit_requested = False
        self._pending_snapshot_restore_visible = False
        self._pending_snapshot_restore_minimized = False
        self._setup_auto_hide_timer = QTimer(self)
        self._setup_auto_hide_timer.setSingleShot(True)
        self._setup_auto_hide_timer.setInterval(10000)
        self._setup_auto_hide_timer.timeout.connect(lambda: self._setup_btn.setChecked(False))
        self._panel_anim_timer = QTimer(self)
        self._panel_anim_timer.setInterval(20)
        self._panel_anim_timer.timeout.connect(self._on_panel_anim_tick)
        self._panel_anim_count = 0
        self._panel_anim_direction = 0
        self._panel_anim_max = 30
        self.setWindowTitle("IOGraph (Python)")
        self.setFixedWidth(self.MAIN_FRAME_WIDTH)
        self.setWindowIcon(self._app_icon())

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._canvas = TrackCanvas(self)
        layout.addWidget(self._canvas, stretch=1)

        self._bottom_panel = QWidget(self)
        self._bottom_panel.setFixedHeight(self.PANEL_HEIGHT)
        bottom_layout = QHBoxLayout(self._bottom_panel)
        bottom_layout.setContentsMargins(6, 0, 6, 0)
        bottom_layout.setSpacing(0)
        layout.addWidget(self._bottom_panel, stretch=0)

        self._panels_viewport = QWidget(self._bottom_panel)
        self._panels_viewport.setContentsMargins(0, 0, 0, 0)
        self._panels_viewport.setFixedHeight(self.PANEL_HEIGHT)
        self._panels_viewport.installEventFilter(self)
        bottom_layout.addWidget(self._panels_viewport, stretch=1)

        self._front_panel = QWidget(self._panels_viewport)
        self._control_panel = QWidget(self._panels_viewport)

        self._toggle_btn = QPushButton(self._canvas)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setFixedSize(88, 88)
        self._toggle_btn.setIconSize(QSize(88, 88))
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self._toggle_btn.clicked.connect(self._on_toggle_clicked)
        self._canvas.installEventFilter(self)
        self._update_toggle_icon()
        self._toggle_hover = False
        self._toggle_opacity = 1.0
        self._toggle_opacity_effect = QGraphicsOpacityEffect(self._toggle_btn)
        self._toggle_opacity_effect.setOpacity(self._toggle_opacity)
        self._toggle_btn.setGraphicsEffect(self._toggle_opacity_effect)
        self._toggle_fade_timer = QTimer(self)
        self._toggle_fade_timer.setInterval(33)
        self._toggle_fade_timer.timeout.connect(self._animate_toggle_opacity)
        self._toggle_fade_timer.start()

        front_layout = QVBoxLayout(self._front_panel)
        front_layout.setContentsMargins(28, 5, 0, 5)
        front_layout.setSpacing(0)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(5)
        front_layout.addLayout(top_row)

        self._total_time_label = QLabel("Total Time", self._front_panel)
        self._total_time_label.setFont(QFont(self._total_time_label.font().family(), 30))
        self._total_time_label.setFixedHeight(36)
        self._total_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._total_time_label.setVisible(False)
        top_row.addStretch(1)
        top_row.addWidget(self._total_time_label, stretch=0)

        self._reset_btn = QPushButton(self._front_panel)
        self._reset_btn.clicked.connect(self._reset_canvas)
        self._reset_btn.setVisible(False)
        self._reset_btn.setFixedSize(19, 28)
        self._reset_btn.setIconSize(QSize(19, 19))
        self._reset_btn.setFlat(True)
        self._reset_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding-top: 8px; }")
        self._reset_btn.setIcon(self._icon("ResetBtn.png"))
        self._reset_btn.pressed.connect(lambda: self._reset_btn.setIcon(self._icon("ResetPressedBtn.png")))
        self._reset_btn.released.connect(lambda: self._reset_btn.setIcon(self._icon("ResetBtn.png")))
        top_row.addWidget(self._reset_btn, stretch=0)
        top_row.setAlignment(self._reset_btn, Qt.AlignmentFlag.AlignVCenter)
        top_row.addStretch(1)

        self._period_label = QLabel("Time Period", self._front_panel)
        self._period_label.setFont(QFont(self._period_label.font().family(), 12))
        self._period_label.setFixedHeight(18)
        self._period_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self._period_label.setVisible(False)
        front_layout.addWidget(self._period_label, stretch=0)
        front_layout.setAlignment(self._period_label, Qt.AlignmentFlag.AlignTop)

        control_layout = QGridLayout(self._control_panel)
        control_layout.setContentsMargins(10, 0, 0, 0)
        control_layout.setHorizontalSpacing(16)
        control_layout.setVerticalSpacing(2)

        self._ignore_stops_box = QCheckBox("Ignore Mouse Stops", self._control_panel)
        control_layout.setAlignment(self._ignore_stops_box, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        control_layout.addWidget(self._ignore_stops_box, 0, 0)
        desktop_row = QWidget(self._control_panel)
        desktop_row_layout = QHBoxLayout(desktop_row)
        desktop_row_layout.setContentsMargins(0, 0, 0, 0)
        desktop_row_layout.setSpacing(6)
        self._use_desktop_box = QCheckBox("Use Desktop", desktop_row)
        desktop_row_layout.addWidget(self._use_desktop_box, 0)
        self._update_desktop_btn = QPushButton(desktop_row)
        self._update_desktop_btn.clicked.connect(self._refresh_desktop_snapshot)
        self._update_desktop_btn.setFixedSize(19, 19)
        self._update_desktop_btn.setIconSize(QSize(18, 18))
        self._update_desktop_btn.setFlat(True)
        self._update_desktop_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self._update_desktop_btn.setIcon(self._icon("UpdateDesktopDisabledBtn.png"))
        self._update_desktop_btn.pressed.connect(self._on_update_desktop_pressed)
        self._update_desktop_btn.released.connect(self._on_update_desktop_released)
        self._update_desktop_btn.setVisible(False)
        desktop_row_layout.addWidget(self._update_desktop_btn, 0)
        desktop_row_layout.addStretch(1)
        control_layout.setAlignment(desktop_row, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        control_layout.addWidget(desktop_row, 0, 1)
        self._multi_monitor_box = QCheckBox("Use Multiple Monitors", self._control_panel)
        control_layout.setAlignment(self._multi_monitor_box, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        control_layout.addWidget(self._multi_monitor_box, 1, 0)
        colorful_row = QWidget(self._control_panel)
        colorful_row_layout = QHBoxLayout(colorful_row)
        colorful_row_layout.setContentsMargins(0, 0, 0, 0)
        colorful_row_layout.setSpacing(0)
        self._colorful_box = QCheckBox("Use Colourful Scheme", colorful_row)
        colorful_row_layout.addWidget(self._colorful_box, 0)
        colorful_row_layout.addStretch(1)
        control_layout.setAlignment(colorful_row, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        control_layout.addWidget(colorful_row, 1, 1)

        self._secondary_panel = QWidget(self._bottom_panel)
        secondary_layout = QVBoxLayout(self._secondary_panel)
        secondary_layout.setContentsMargins(0, 5, 0, 10)
        secondary_layout.setSpacing(4)
        self._save_btn = QPushButton(self._secondary_panel)
        self._save_btn.clicked.connect(self._save_image)
        self._save_btn.setEnabled(False)
        self._save_btn.setFixedSize(19, 18)
        self._save_btn.setIconSize(QSize(15, 15))
        self._save_btn.setFlat(True)
        self._save_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self._save_btn.setIcon(self._icon("SaveDisabledBtn.png"))
        self._save_btn.pressed.connect(self._on_save_pressed)
        self._save_btn.released.connect(self._on_save_released)
        secondary_layout.addWidget(self._save_btn)
        self._setup_btn = QPushButton(self._secondary_panel)
        self._setup_btn.setCheckable(True)
        self._setup_btn.setFixedSize(19, 18)
        self._setup_btn.setIconSize(QSize(15, 15))
        self._setup_btn.setFlat(True)
        self._setup_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self._setup_btn.setIcon(self._icon("SetupBtn.png"))
        self._setup_btn.pressed.connect(self._on_setup_pressed)
        self._setup_btn.released.connect(self._on_setup_released)
        self._setup_btn.toggled.connect(self._toggle_setup_panel)
        secondary_layout.addWidget(self._setup_btn)
        self._url_btn = QPushButton(self._secondary_panel)
        self._url_btn.setFixedSize(19, 18)
        self._url_btn.setIconSize(QSize(15, 15))
        self._url_btn.setFlat(True)
        self._url_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self._url_btn.setIcon(self._icon("URLBtn.png"))
        self._url_btn.pressed.connect(lambda: self._url_btn.setIcon(self._icon("URLPressedBtn.png")))
        self._url_btn.released.connect(lambda: self._url_btn.setIcon(self._icon("URLBtn.png")))
        self._url_btn.clicked.connect(lambda: webbrowser.open("https://iographica.com/"))
        secondary_layout.addWidget(self._url_btn)
        bottom_layout.addWidget(self._secondary_panel, stretch=0)

        self._resize_panels_for_viewport()
        self._update_panel_positions()

        self.setCentralWidget(central)
        self._setup_actions()
        self._bind_control_panel()
        self._load_settings()
        self._apply_window_geometry()
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(1000)
        self._ui_timer.timeout.connect(self._update_timer_label)
        self._ui_timer.start()
        app = QGuiApplication.instance()
        if app is not None:
            app.screenAdded.connect(lambda screen: self._apply_window_geometry())
            app.screenRemoved.connect(lambda screen: self._apply_window_geometry())
        self._setup_tray()
        self._refresh_dpi_dependent_icons()
        self._position_toggle_button()
        self._sync_ui_state()
        self._status("Ready")

    def _setup_actions(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        tracking_menu = self.menuBar().addMenu("&Tracking")
        options_menu = self.menuBar().addMenu("&Options")
        help_menu = self.menuBar().addMenu("&Help")

        self._save_image_action = QAction("Save &Image...", self)
        self._save_image_action.setShortcut("Ctrl+S")
        self._save_image_action.triggered.connect(self._save_image)
        file_menu.addAction(self._save_image_action)

        self._save_csv_action = QAction("Save &CSV...", self)
        self._save_csv_action.setShortcut("Ctrl+Shift+S")
        self._save_csv_action.triggered.connect(self._save_csv)
        file_menu.addAction(self._save_csv_action)

        self._reset_action = QAction("&Reset", self)
        self._reset_action.setShortcut("Ctrl+R")
        self._reset_action.triggered.connect(self._reset_canvas)
        file_menu.addAction(self._reset_action)

        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._request_quit)
        file_menu.addAction(exit_action)

        self._tracking_toggle_action = QAction("Start", self)
        self._tracking_toggle_action.setShortcut("Ctrl+R")
        self._tracking_toggle_action.triggered.connect(lambda: self._set_tracking(not self._canvas.is_tracking()))
        tracking_menu.addAction(self._tracking_toggle_action)
        self._tracking_reset_action = QAction("Reset", self)
        self._tracking_reset_action.setShortcut("Ctrl+N")
        self._tracking_reset_action.triggered.connect(self._reset_canvas)
        tracking_menu.addAction(self._tracking_reset_action)

        self._ignore_stops_action = QAction("Ignore Mouse Stops", self)
        self._ignore_stops_action.setCheckable(True)
        self._ignore_stops_action.toggled.connect(self._canvas.set_ignore_mouse_stops)
        options_menu.addAction(self._ignore_stops_action)

        self._colorful_action = QAction("Colourful Scheme", self)
        self._colorful_action.setCheckable(True)
        self._colorful_action.toggled.connect(self._on_colorful_toggled)
        options_menu.addAction(self._colorful_action)

        self._use_desktop_action = QAction("Use Desktop Background", self)
        self._use_desktop_action.setCheckable(True)
        self._use_desktop_action.toggled.connect(self._on_use_desktop_toggled)
        options_menu.addAction(self._use_desktop_action)

        self._multi_monitor_action = QAction("Use Multiple Monitors", self)
        self._multi_monitor_action.setCheckable(True)
        self._multi_monitor_action.setChecked(True)
        self._multi_monitor_action.toggled.connect(self._on_multi_monitor_toggled)
        options_menu.addAction(self._multi_monitor_action)

        self._refresh_desktop_action = QAction("Update Desktop Snapshot", self)
        self._refresh_desktop_action.triggered.connect(self._refresh_desktop_snapshot)
        self._refresh_desktop_action.setEnabled(False)
        options_menu.addAction(self._refresh_desktop_action)

        about_action = QAction("About IOGraph", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        help_menu.addSeparator()

        source_action = QAction("Get Source Code from GitHub...", self)
        source_action.triggered.connect(lambda: self._open_url(self._GITHUB_URL))
        help_menu.addAction(source_action)

        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self._check_for_updates_placeholder)
        help_menu.addAction(check_updates_action)
        self._check_updates_action = check_updates_action

        self._auto_update_action = QAction("Check for Updates Automatically", self)
        self._auto_update_action.setCheckable(True)
        self._auto_update_action.toggled.connect(self._on_auto_update_toggled)
        help_menu.addAction(self._auto_update_action)

        help_menu.addSeparator()
        facebook_action = QAction("Join Our Facebook Community...", self)
        facebook_action.triggered.connect(lambda: self._open_url(self._FACEBOOK_URL))
        help_menu.addAction(facebook_action)
        website_action = QAction("Visit IOGraphica's Website...", self)
        website_action.triggered.connect(lambda: self._open_url(self._WEBSITE_URL))
        help_menu.addAction(website_action)

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(self._icon("MenuBarIconRecord.png"))
        tray_menu = QMenu(self)
        self._tray_toggle_action = tray_menu.addAction("Start")
        self._tray_toggle_action.triggered.connect(lambda: self._set_tracking(not self._canvas.is_tracking()))
        self._tray_reset_action = tray_menu.addAction("Reset")
        self._tray_reset_action.triggered.connect(self._reset_canvas)
        self._tray_reset_action.setEnabled(False)
        tray_menu.addSeparator()
        self._tray_save_image_action = tray_menu.addAction("Save...")
        self._tray_save_image_action.triggered.connect(self._save_image)
        self._tray_save_image_action.setEnabled(False)
        tray_menu.addSeparator()
        self._tray_settings_action = tray_menu.addAction("Show Settings")
        self._tray_settings_action.triggered.connect(self._toggle_settings_from_tray)
        more_menu = tray_menu.addMenu("More")
        self._tray_save_csv_action = more_menu.addAction("Save Raw Data...")
        self._tray_save_csv_action.triggered.connect(self._save_csv)
        self._tray_save_csv_action.setEnabled(False)
        more_menu.addSeparator()
        self._tray_check_updates_action = more_menu.addAction("Check for Updates")
        self._tray_check_updates_action.triggered.connect(self._check_for_updates_placeholder)
        self._tray_auto_update_action = more_menu.addAction("Check for Updates Automatically")
        self._tray_auto_update_action.setCheckable(True)
        self._tray_auto_update_action.toggled.connect(self._on_auto_update_toggled)
        more_menu.addSeparator()
        more_menu.addAction("Get Source Code from GitHub", lambda: self._open_url(self._GITHUB_URL))
        more_menu.addAction("Join Our Facebook Community", lambda: self._open_url(self._FACEBOOK_URL))
        more_menu.addAction("Visit IOGraphica's Website", lambda: self._open_url(self._WEBSITE_URL))
        more_menu.addSeparator()
        more_menu.addAction("About IOGraph", self._show_about_dialog)
        tray_menu.addSeparator()
        tray_menu.addAction("Quit", self._request_quit)
        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()
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

    def _reset_canvas(self) -> None:
        if self._canvas.get_elapsed_ms() > 0:
            if not self._confirm_reset():
                return
        self._perform_reset()

    def _perform_reset(self) -> None:
        is_tracking = self._canvas.is_tracking()
        self._canvas.reset()
        if is_tracking:
            self._session_started_at = datetime.now()
            self._session_ended_at = None
        else:
            self._session_started_at = None
            self._session_ended_at = None
        self._total_time_label.setText("Total Time")
        self._period_label.setText("Time Period")
        self._total_time_label.setVisible(False)
        self._period_label.setVisible(False)
        self._reset_btn.setVisible(False)
        self._sync_ui_state()
        self._status("Canvas reset")

    def _save_image(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save image",
            f"{self._build_export_base_name()}.png",
            "PNG image (*.png)",
        )
        if not path:
            return
        image_path = Path(path)
        if image_path.suffix.lower() != ".png":
            image_path = image_path.with_suffix(".png")
        ok = self._canvas.export_png(str(image_path))
        self._status("Image saved" if ok else "Failed to save image")
        self._sync_ui_state()

    def _save_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            f"{self._build_export_base_name()}.csv",
            "CSV file (*.csv)",
        )
        if not path:
            return
        csv_path = Path(path)
        if csv_path.suffix.lower() != ".csv":
            csv_path = csv_path.with_suffix(".csv")
        csv_path.write_text(self._canvas.export_csv_text(), encoding="utf-8")
        self._status("CSV saved")
        self._sync_ui_state()

    def _on_use_desktop_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        self._canvas.set_use_desktop_background(checked)
        self._refresh_desktop_action.setEnabled(checked)
        self._update_desktop_btn.setVisible(checked)
        self._update_desktop_btn.setEnabled(checked)
        self._update_update_desktop_icon()
        if checked:
            self._refresh_desktop_snapshot()
        else:
            self._status("Desktop background disabled")

    def _refresh_desktop_snapshot(self) -> None:
        # Two-phase hide/capture: handles startup case when window becomes visible after scheduling.
        self._pending_snapshot_restore_visible = self.isVisible()
        self._pending_snapshot_restore_minimized = self.isMinimized()
        if self._pending_snapshot_restore_visible:
            self.hide()
            QApplication.processEvents()
        QTimer.singleShot(40, self._capture_desktop_snapshot_hidden)

    def _capture_desktop_snapshot_hidden(self) -> None:
        if self.isVisible():
            # Startup path: window may become visible after initial scheduling.
            self._pending_snapshot_restore_visible = True
            self._pending_snapshot_restore_minimized = self.isMinimized()
            self.hide()
            QApplication.processEvents()
            QTimer.singleShot(160, self._capture_desktop_snapshot_final)
            return
        QTimer.singleShot(160, self._capture_desktop_snapshot_final)

    def _capture_desktop_snapshot_final(self) -> None:
        ok = self._canvas.update_desktop_background()
        if self._pending_snapshot_restore_visible:
            if self._pending_snapshot_restore_minimized:
                self.showMinimized()
            else:
                self.showNormal()
                self.raise_()
                self.activateWindow()
        self._status("Desktop snapshot updated" if ok else "Failed to capture desktop snapshot")

    def _on_multi_monitor_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        if checked == self._canvas.is_use_multiple_monitors():
            return
        if self._canvas.get_elapsed_ms() > 0:
            ok = self._confirm_reset_for_switch(
                "Switch Confirmation",
                "We need to reset tracking when switching between single/multiple monitors.\nDo you want to start from scratch?",
            )
            if not ok:
                self._set_option_checked(self._multi_monitor_action, self._multi_monitor_box, not checked)
                return
        self._canvas.set_use_multiple_monitors(checked)
        if self._use_desktop_action.isChecked():
            self._refresh_desktop_snapshot()
        self._perform_reset()
        self._apply_window_geometry()

    def _load_settings(self) -> None:
        ignore_stops = self._settings.value("options/ignore_mouse_stops", False, bool)
        colorful = self._settings.value("options/colorful_scheme", False, bool)
        use_desktop = self._settings.value("options/use_desktop_background", False, bool)
        use_multi_monitor = self._settings.value("options/use_multiple_monitors", True, bool)
        auto_update = self._settings.value("options/automatic_update", False, bool)

        # Apply to runtime first (source of truth), then mirror in UI without signal side-effects.
        self._canvas.set_ignore_mouse_stops(ignore_stops)
        self._canvas.set_colorful_scheme(colorful)
        self._canvas.set_use_multiple_monitors(use_multi_monitor)
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
        if use_desktop:
            self._refresh_desktop_snapshot()
        self._set_auto_update_state(auto_update)
        self._sync_ui_state()

    def _save_settings(self) -> None:
        self._settings.setValue("options/ignore_mouse_stops", self._ignore_stops_action.isChecked())
        self._settings.setValue("options/colorful_scheme", self._colorful_action.isChecked())
        self._settings.setValue("options/use_multiple_monitors", self._multi_monitor_action.isChecked())
        self._settings.setValue("options/use_desktop_background", self._use_desktop_action.isChecked())
        self._settings.setValue("options/automatic_update", self._auto_update_action.isChecked())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if getattr(self, "_tray_icon", None) is not None and not self._force_quit_requested:
            self.hide()
            event.ignore()
            return
        if not self._confirm_exit():
            self._force_quit_requested = False
            event.ignore()
            return
        self._save_settings()
        super().closeEvent(event)

    def _update_timer_label(self) -> None:
        elapsed_ms = self._canvas.get_elapsed_ms()
        if elapsed_ms <= 0 and not self._canvas.is_tracking():
            return
        self._total_time_label.setText(self._build_tracking_time_text(elapsed_ms))
        self._period_label.setText(self._build_period_label())
        self._total_time_label.setVisible(True)
        self._period_label.setVisible(True)
        self._reset_btn.setVisible(elapsed_ms > 2000)
        self._sync_ui_state()

    def _build_export_base_name(self) -> str:
        time_label = self._build_tracking_time_text(self._canvas.get_elapsed_ms())
        period = self._build_period_label()
        if not period:
            return f"IOGraphica - {time_label}"
        period_for_file = period.replace(":", "-")
        period_for_file = period_for_file[0].lower() + period_for_file[1:]
        return f"IOGraphica - {time_label} ({period_for_file})"

    def _set_tracking(self, enabled: bool) -> None:
        if enabled:
            if self._session_started_at is None:
                self._session_started_at = datetime.now()
            self._session_ended_at = None
            self._canvas.start_tracking()
            self._toggle_btn.setChecked(True)
            self._sync_ui_state()
            self._status("Tracking started")
            return
        self._canvas.stop_tracking()
        self._session_ended_at = datetime.now()
        self._toggle_btn.setChecked(False)
        self._sync_ui_state()
        self._status("Tracking stopped")

    def _toggle_setup_panel(self, checked: bool) -> None:
        self._panel_anim_direction = 1 if checked else -1
        self._panel_anim_timer.start()
        self._setup_btn.setIcon(self._icon("SetupBtnC.png" if checked else "SetupBtn.png"))
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

    def _build_period_label(self) -> str:
        started = self._session_started_at
        if started is None:
            return "Time Period"
        ended = self._session_ended_at or datetime.now()
        if (ended - started).total_seconds() <= 60:
            return f"From {self._date_pattern(started, False)}"
        full_date_treatment = started.day != ended.day or started.month != ended.month
        return f"From {self._date_pattern(started, full_date_treatment)} to {self._date_pattern(ended, full_date_treatment)}"

    def _build_tracking_time_text(self, ms: int) -> str:
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
            n = self._precision(hours)
            return f"{n} hour" if hours < 1.1 else f"{n} hours"
        n = self._precision(days)
        return f"{n} day" if days < 1.1 else f"{n} days"

    def _date_pattern(self, dt: datetime, full_date: bool) -> str:
        base = f"{dt.hour}:{dt.minute:02d}"
        if not full_date:
            return base
        return f"{base} {self._MONTH_NAMES[dt.month - 1]} {self._ordinal(dt.day)}"

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

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        if obj is self._canvas:
            event_type = event.type()
            if event_type == QEvent.Type.Resize:
                self._position_toggle_button()
            elif event_type in (QEvent.Type.MouseMove, QEvent.Type.Enter, QEvent.Type.Leave):
                self._update_toggle_hover_state()
        elif obj is self._panels_viewport and event.type() == QEvent.Type.Resize:
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
        if not self._save_btn.isEnabled():
            self._save_btn.setIcon(self._icon("SaveDisabledBtn.png"))
            return
        self._save_btn.setIcon(self._icon("SaveBtn.png"))

    def _on_save_pressed(self) -> None:
        if self._save_btn.isEnabled():
            self._save_btn.setIcon(self._icon("SavePressedBtn.png"))

    def _on_save_released(self) -> None:
        self._update_save_icon()

    def _on_setup_pressed(self) -> None:
        self._setup_btn.setIcon(self._icon("SetupPressedBtnC.png" if self._setup_btn.isChecked() else "SetupPressedBtn.png"))

    def _on_setup_released(self) -> None:
        self._setup_btn.setIcon(self._icon("SetupBtnC.png" if self._setup_btn.isChecked() else "SetupBtn.png"))

    def _on_update_desktop_pressed(self) -> None:
        if self._update_desktop_btn.isEnabled():
            self._update_desktop_btn.setIcon(self._icon("UpdateDesktopPressedBtn.png"))

    def _on_update_desktop_released(self) -> None:
        self._update_update_desktop_icon()

    def _update_update_desktop_icon(self) -> None:
        if not self._update_desktop_btn.isEnabled():
            self._update_desktop_btn.setIcon(self._icon("UpdateDesktopDisabledBtn.png"))
            return
        self._update_desktop_btn.setIcon(self._icon("UpdateDesktopBtn.png"))

    def _icon(self, name: str) -> QIcon:
        return QIcon(str(self._resource_file_for_dpi(name)))

    def _app_icon(self) -> QIcon:
        icon = QIcon()
        for name in self._APP_ICON_FILES:
            path = self._RESOURCE_DIR / name
            if path.exists():
                icon.addFile(str(path))
            hi = self._RESOURCE_DIR / f"{path.stem}@2x{path.suffix}"
            if hi.exists():
                icon.addFile(str(hi))
        return icon

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
        if self._canvas.get_elapsed_ms() > 0:
            ok = self._confirm_reset_for_switch(
                "Color Scheme Switch Confirmation",
                "We need to reset tracking when switching color schemes.\nDo you want to start from scratch?",
            )
            if not ok:
                self._set_option_checked(self._colorful_action, self._colorful_box, not checked)
                return
        self._canvas.set_colorful_scheme(checked)
        self._perform_reset()

    def _confirm_reset_for_switch(self, title: str, message: str) -> bool:
        elapsed = self._canvas.get_elapsed_ms()
        if elapsed > 30 * 60 * 1000:
            message += f"\nAre you sure? After {self._build_tracking_time_text(elapsed)} of tracking?"
        answer = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _confirm_reset(self) -> bool:
        elapsed = self._canvas.get_elapsed_ms()
        message = "Do you really wanna start from scratch?"
        if elapsed > 30 * 60 * 1000:
            message += f"\nAre you sure? After {self._build_tracking_time_text(elapsed)} of tracking?"
        answer = QMessageBox.question(
            self,
            "Reset confirmation",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _confirm_exit(self) -> bool:
        elapsed = self._canvas.get_elapsed_ms()
        if elapsed < 60 * 1000:
            return True

        title = "Wait! Wait! Wait!"
        message = "Do you really wanna exit and lose all your data?"
        if elapsed > 30 * 60 * 1000:
            message += f"\nAre you sure? After {self._build_tracking_time_text(elapsed)} of laborious tracking?"

        answer = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _set_option_checked(self, action: QAction, checkbox: QCheckBox, value: bool) -> None:
        self._suppress_option_handlers = True
        try:
            action.setChecked(value)
            checkbox.setChecked(value)
        finally:
            self._suppress_option_handlers = False

    @staticmethod
    def _set_checked_silent(widget, value: bool) -> None:
        prev = widget.blockSignals(True)
        try:
            widget.setChecked(value)
        finally:
            widget.blockSignals(prev)

    def _request_quit(self) -> None:
        self._force_quit_requested = True
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
        webbrowser.open(url)

    def _show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About IOGraph",
            "IOGraph (Python port)\nPorted from the original Java version.",
        )

    def _check_for_updates_placeholder(self) -> None:
        self._status("Check for updates is not implemented yet")

    def _status(self, _message: str) -> None:
        # Java version has no Qt status bar; keep this as no-op to avoid affecting layout height.
        return

    def _on_auto_update_toggled(self, checked: bool) -> None:
        if self._suppress_option_handlers:
            return
        self._set_auto_update_state(checked)

    def _set_auto_update_state(self, checked: bool) -> None:
        self._suppress_option_handlers = True
        try:
            self._auto_update_action.setChecked(checked)
            tray_auto = getattr(self, "_tray_auto_update_action", None)
            if tray_auto is not None:
                tray_auto.setChecked(checked)
        finally:
            self._suppress_option_handlers = False

    def event(self, event) -> bool:  # type: ignore[override]
        event_type = event.type()
        if event_type == QEvent.Type.WindowDeactivate and self._setup_btn.isChecked():
            self._setup_auto_hide_timer.start()
        elif event_type == QEvent.Type.WindowActivate:
            self._setup_auto_hide_timer.stop()
        return super().event(event)

    def _toggle_settings_from_tray(self) -> None:
        self._setup_btn.setChecked(not self._setup_btn.isChecked())
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._update_tray_state()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _update_tray_state(self) -> None:
        tray = getattr(self, "_tray_icon", None)
        if tray is None:
            return
        elapsed = self._canvas.get_elapsed_ms()
        tracking = self._canvas.is_tracking()
        if tracking:
            self._tray_toggle_action.setText("Pause")
        else:
            self._tray_toggle_action.setText("Start" if elapsed == 0 else "Resume")
        can_save = tracking or elapsed > 0
        self._tray_save_image_action.setEnabled(can_save)
        self._tray_save_csv_action.setEnabled(can_save)
        self._tray_reset_action.setEnabled(elapsed > 2000)
        self._tray_settings_action.setText("Hide Settings" if self._setup_btn.isChecked() else "Show Settings")
        tray.setIcon(self._icon("MenuBarIconPause.png" if tracking else "MenuBarIconRecord.png"))

    def _sync_ui_state(self) -> None:
        elapsed = self._canvas.get_elapsed_ms()
        tracking = self._canvas.is_tracking()
        can_save = tracking or elapsed > 0
        can_reset = elapsed > 2000

        self._toggle_btn.setChecked(tracking)
        self._update_toggle_icon()

        self._save_btn.setEnabled(can_save)
        self._update_save_icon()

        self._reset_action.setEnabled(can_reset)
        self._tracking_reset_action.setEnabled(can_reset)
        self._save_image_action.setEnabled(can_save)
        self._save_csv_action.setEnabled(can_save)

        if tracking:
            self._tracking_toggle_action.setText("Pause")
        else:
            self._tracking_toggle_action.setText("Start" if elapsed == 0 else "Resume")

        self._update_tray_state()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
