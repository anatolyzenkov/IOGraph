from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import QSettings, Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import sys

from .tracker import TrackCanvas


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("iographica", "IOGraphPython")
        self.setWindowTitle("IOGraph (Python)")
        self.resize(1200, 800)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self._canvas = TrackCanvas(self)
        layout.addWidget(self._canvas, stretch=1)

        self._toggle_btn = QPushButton("Start tracking", self)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.clicked.connect(self._on_toggle_clicked)
        layout.addWidget(self._toggle_btn, stretch=0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(central)
        self._setup_actions()
        self._load_settings()
        self._timer_label = QLabel("00:00:00", self)
        self.statusBar().addPermanentWidget(self._timer_label)
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(200)
        self._ui_timer.timeout.connect(self._update_timer_label)
        self._ui_timer.start()
        self.statusBar().showMessage("Ready")

    def _setup_actions(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        options_menu = self.menuBar().addMenu("&Options")

        save_image_action = QAction("Save &Image...", self)
        save_image_action.setShortcut("Ctrl+S")
        save_image_action.triggered.connect(self._save_image)
        file_menu.addAction(save_image_action)

        save_csv_action = QAction("Save &CSV...", self)
        save_csv_action.setShortcut("Ctrl+Shift+S")
        save_csv_action.triggered.connect(self._save_csv)
        file_menu.addAction(save_csv_action)

        reset_action = QAction("&Reset", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._reset_canvas)
        file_menu.addAction(reset_action)

        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self._ignore_stops_action = QAction("Ignore Mouse Stops", self)
        self._ignore_stops_action.setCheckable(True)
        self._ignore_stops_action.toggled.connect(self._canvas.set_ignore_mouse_stops)
        options_menu.addAction(self._ignore_stops_action)

        self._colorful_action = QAction("Colourful Scheme", self)
        self._colorful_action.setCheckable(True)
        self._colorful_action.toggled.connect(self._canvas.set_colorful_scheme)
        options_menu.addAction(self._colorful_action)

        self._use_desktop_action = QAction("Use Desktop Background", self)
        self._use_desktop_action.setCheckable(True)
        self._use_desktop_action.toggled.connect(self._on_use_desktop_toggled)
        options_menu.addAction(self._use_desktop_action)

        self._multi_monitor_action = QAction("Use Multiple Monitors", self)
        self._multi_monitor_action.setCheckable(True)
        self._multi_monitor_action.setChecked(True)
        self._multi_monitor_action.toggled.connect(self._canvas.set_use_multiple_monitors)
        options_menu.addAction(self._multi_monitor_action)

        self._refresh_desktop_action = QAction("Update Desktop Snapshot", self)
        self._refresh_desktop_action.triggered.connect(self._refresh_desktop_snapshot)
        self._refresh_desktop_action.setEnabled(False)
        options_menu.addAction(self._refresh_desktop_action)

    def _on_toggle_clicked(self, checked: bool) -> None:
        if checked:
            self._canvas.start_tracking()
            self._toggle_btn.setText("Stop tracking")
            self.statusBar().showMessage("Tracking started")
        else:
            self._canvas.stop_tracking()
            self._toggle_btn.setText("Start tracking")
            self.statusBar().showMessage("Tracking stopped")

    def _reset_canvas(self) -> None:
        self._canvas.reset()
        self.statusBar().showMessage("Canvas reset")

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
        self.statusBar().showMessage("Image saved" if ok else "Failed to save image")

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
        self.statusBar().showMessage("CSV saved")

    def _on_use_desktop_toggled(self, checked: bool) -> None:
        self._canvas.set_use_desktop_background(checked)
        self._refresh_desktop_action.setEnabled(checked)
        if checked:
            self._refresh_desktop_snapshot()
        else:
            self.statusBar().showMessage("Desktop background disabled")

    def _refresh_desktop_snapshot(self) -> None:
        ok = self._canvas.update_desktop_background()
        self.statusBar().showMessage(
            "Desktop snapshot updated" if ok else "Failed to capture desktop snapshot"
        )

    def _load_settings(self) -> None:
        ignore_stops = self._settings.value("options/ignore_mouse_stops", False, bool)
        colorful = self._settings.value("options/colorful_scheme", False, bool)
        use_desktop = self._settings.value("options/use_desktop_background", False, bool)
        use_multi_monitor = self._settings.value("options/use_multiple_monitors", True, bool)

        self._ignore_stops_action.setChecked(ignore_stops)
        self._colorful_action.setChecked(colorful)
        self._multi_monitor_action.setChecked(use_multi_monitor)
        self._use_desktop_action.setChecked(use_desktop)
        self._refresh_desktop_action.setEnabled(use_desktop)

    def _save_settings(self) -> None:
        self._settings.setValue("options/ignore_mouse_stops", self._ignore_stops_action.isChecked())
        self._settings.setValue("options/colorful_scheme", self._colorful_action.isChecked())
        self._settings.setValue("options/use_multiple_monitors", self._multi_monitor_action.isChecked())
        self._settings.setValue("options/use_desktop_background", self._use_desktop_action.isChecked())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_settings()
        super().closeEvent(event)

    def _update_timer_label(self) -> None:
        self._timer_label.setText(self._format_elapsed_ms(self._canvas.get_elapsed_ms()))

    def _build_export_base_name(self) -> str:
        stamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        return f"IOGraphica - {stamp} ({self._format_elapsed_ms(self._canvas.get_elapsed_ms())})"

    @staticmethod
    def _format_elapsed_ms(ms: int) -> str:
        total = max(0, ms // 1000)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
