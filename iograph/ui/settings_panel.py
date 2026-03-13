from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QCheckBox, QGridLayout, QHBoxLayout, QPushButton, QWidget


@dataclass(frozen=True)
class SettingsPanelRefs:
    ignore_stops_box: QCheckBox
    use_desktop_box: QCheckBox
    update_desktop_btn: QPushButton
    multi_monitor_box: QCheckBox
    colorful_box: QCheckBox


def build_settings_panel(
    parent: QWidget,
    *,
    on_refresh_desktop_snapshot,
    on_update_desktop_pressed,
    on_update_desktop_released,
    icon_loader,
) -> SettingsPanelRefs:
    control_layout = QGridLayout(parent)
    control_layout.setContentsMargins(8, 0, 0, 0)
    control_layout.setHorizontalSpacing(24)
    control_layout.setVerticalSpacing(0)

    ignore_stops_box = QCheckBox("Ignore Mouse Stops", parent)
    control_layout.setAlignment(ignore_stops_box, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    control_layout.addWidget(ignore_stops_box, 0, 0)

    desktop_row = QWidget(parent)
    desktop_row_layout = QHBoxLayout(desktop_row)
    desktop_row_layout.setContentsMargins(0, 0, 0, 0)
    desktop_row_layout.setSpacing(6)

    use_desktop_box = QCheckBox("Use Desktop", desktop_row)
    desktop_row_layout.addWidget(use_desktop_box, 0)

    update_desktop_btn = QPushButton(desktop_row)
    update_desktop_btn.clicked.connect(on_refresh_desktop_snapshot)
    update_desktop_btn.setFixedSize(18, 18)
    update_desktop_btn.setIconSize(QSize(18, 18))
    update_desktop_btn.setFlat(True)
    update_desktop_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding-top: 2px; }")
    update_desktop_btn.setIcon(icon_loader("UpdateDesktopDisabledBtn.png"))
    update_desktop_btn.pressed.connect(on_update_desktop_pressed)
    update_desktop_btn.released.connect(on_update_desktop_released)
    size_policy = update_desktop_btn.sizePolicy()
    size_policy.setRetainSizeWhenHidden(True)
    update_desktop_btn.setSizePolicy(size_policy)
    update_desktop_btn.setVisible(False)
    desktop_row_layout.addWidget(update_desktop_btn, 0)
    desktop_row_layout.addStretch(1)
    control_layout.setAlignment(desktop_row, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    control_layout.addWidget(desktop_row, 0, 1)

    multi_monitor_box = QCheckBox("Use Multiple Monitors", parent)
    control_layout.setAlignment(multi_monitor_box, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    control_layout.addWidget(multi_monitor_box, 1, 0)

    colorful_row = QWidget(parent)
    colorful_row_layout = QHBoxLayout(colorful_row)
    colorful_row_layout.setContentsMargins(0, 0, 0, 0)
    colorful_row_layout.setSpacing(0)
    colorful_box = QCheckBox("Use Colorful Scheme", colorful_row)
    colorful_row_layout.addWidget(colorful_box, 0)
    colorful_row_layout.addStretch(1)
    control_layout.setAlignment(colorful_row, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    control_layout.addWidget(colorful_row, 1, 1)

    return SettingsPanelRefs(
        ignore_stops_box=ignore_stops_box,
        use_desktop_box=use_desktop_box,
        update_desktop_btn=update_desktop_btn,
        multi_monitor_box=multi_monitor_box,
        colorful_box=colorful_box,
    )
