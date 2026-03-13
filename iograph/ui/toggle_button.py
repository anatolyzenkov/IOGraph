from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QPushButton, QWidget


@dataclass(frozen=True)
class ToggleButtonRefs:
    button: QPushButton
    opacity_effect: QGraphicsOpacityEffect
    fade_timer: QTimer


def build_toggle_button(
    parent: QWidget,
    *,
    on_clicked,
    on_fade_tick,
) -> ToggleButtonRefs:
    button = QPushButton(parent)
    button.setCheckable(True)
    button.setFixedSize(88, 88)
    button.setIconSize(QSize(88, 88))
    button.setFlat(True)
    button.setStyleSheet("QPushButton { border: none; background: transparent; }")
    button.clicked.connect(on_clicked)

    opacity_effect = QGraphicsOpacityEffect(button)
    opacity_effect.setOpacity(1.0)
    button.setGraphicsEffect(opacity_effect)

    fade_timer = QTimer(parent)
    fade_timer.setInterval(33)
    fade_timer.timeout.connect(on_fade_tick)
    fade_timer.start()

    return ToggleButtonRefs(button=button, opacity_effect=opacity_effect, fade_timer=fade_timer)
