from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


@dataclass(frozen=True)
class FrontPanelRefs:
    total_time_label: QLabel
    reset_btn: QPushButton
    period_label: QLabel


@dataclass(frozen=True)
class SecondaryPanelRefs:
    save_btn: QPushButton
    setup_btn: QPushButton
    url_btn: QPushButton


def build_front_panel(
    parent: QWidget,
    *,
    on_reset,
    icon_loader,
    is_windows: bool,
) -> FrontPanelRefs:
    front_layout = QVBoxLayout(parent)
    front_layout.setContentsMargins(28, 5, 0, 5)
    front_layout.setSpacing(0)

    top_row = QHBoxLayout()
    top_row.setContentsMargins(0, 0, 0, 0)
    top_row.setSpacing(5)
    front_layout.addLayout(top_row)

    total_time_label = QLabel("Total Time", parent)
    total_time_font_size = 24 if is_windows else 30
    total_time_label.setFont(QFont(total_time_label.font().family(), total_time_font_size))
    total_time_label.setFixedHeight(36)
    total_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    total_time_label.setVisible(False)
    top_row.addStretch(1)
    top_row.addWidget(total_time_label, stretch=0)

    reset_btn = QPushButton(parent)
    reset_btn.clicked.connect(on_reset)
    reset_btn.setVisible(False)
    reset_btn.setFixedSize(19, 28)
    reset_btn.setIconSize(QSize(19, 19))
    reset_btn.setFlat(True)
    reset_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding-top: 8px; }")
    reset_btn.setIcon(icon_loader("ResetBtn.png"))
    reset_btn.pressed.connect(lambda: reset_btn.setIcon(icon_loader("ResetPressedBtn.png")))
    reset_btn.released.connect(lambda: reset_btn.setIcon(icon_loader("ResetBtn.png")))
    top_row.addWidget(reset_btn, stretch=0)
    top_row.setAlignment(reset_btn, Qt.AlignmentFlag.AlignVCenter)
    top_row.addStretch(1)

    period_label = QLabel("Time Period", parent)
    period_font_size = 10 if is_windows else 12
    period_label.setFont(QFont(period_label.font().family(), period_font_size))
    period_label.setFixedHeight(16)
    period_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
    period_label.setVisible(False)
    front_layout.addWidget(period_label, stretch=0)
    front_layout.setAlignment(period_label, Qt.AlignmentFlag.AlignTop)

    return FrontPanelRefs(
        total_time_label=total_time_label,
        reset_btn=reset_btn,
        period_label=period_label,
    )


def build_secondary_panel(
    parent: QWidget,
    *,
    on_save_image,
    on_save_pressed,
    on_save_released,
    on_setup_pressed,
    on_setup_released,
    on_toggle_setup_panel,
    on_url_pressed,
    on_url_released,
    on_open_support,
    icon_loader,
    heart_icon_loader,
) -> SecondaryPanelRefs:
    secondary_layout = QVBoxLayout(parent)
    secondary_layout.setContentsMargins(0, 5, 0, 10)
    secondary_layout.setSpacing(4)

    save_btn = QPushButton(parent)
    save_btn.clicked.connect(on_save_image)
    save_btn.setEnabled(False)
    save_btn.setFixedSize(19, 18)
    save_btn.setIconSize(QSize(15, 15))
    save_btn.setFlat(True)
    save_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
    save_btn.setIcon(icon_loader("SaveDisabledBtn.png"))
    save_btn.pressed.connect(on_save_pressed)
    save_btn.released.connect(on_save_released)
    secondary_layout.addWidget(save_btn)

    setup_btn = QPushButton(parent)
    setup_btn.setCheckable(True)
    setup_btn.setFixedSize(19, 18)
    setup_btn.setIconSize(QSize(15, 15))
    setup_btn.setFlat(True)
    setup_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
    setup_btn.setIcon(icon_loader("SetupBtn.png"))
    setup_btn.pressed.connect(on_setup_pressed)
    setup_btn.released.connect(on_setup_released)
    setup_btn.toggled.connect(on_toggle_setup_panel)
    secondary_layout.addWidget(setup_btn)

    url_btn = QPushButton(parent)
    url_btn.setFixedSize(19, 18)
    url_btn.setIconSize(QSize(15, 15))
    url_btn.setFlat(True)
    url_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
    url_btn.setIcon(heart_icon_loader("HeartBtn.png"))
    url_btn.pressed.connect(on_url_pressed)
    url_btn.released.connect(on_url_released)
    url_btn.clicked.connect(on_open_support)
    secondary_layout.addWidget(url_btn)

    return SecondaryPanelRefs(
        save_btn=save_btn,
        setup_btn=setup_btn,
        url_btn=url_btn,
    )
