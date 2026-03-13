from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget


@dataclass(frozen=True)
class BottomScaffoldRefs:
    bottom_panel: QWidget
    bottom_layout: QHBoxLayout
    panels_viewport: QWidget
    front_panel: QWidget
    control_panel: QWidget


def build_bottom_scaffold(
    parent: QWidget,
    *,
    container_layout: QVBoxLayout,
    panel_height: int,
    viewport_event_filter,
) -> BottomScaffoldRefs:
    bottom_panel = QWidget(parent)
    bottom_panel.setFixedHeight(panel_height)
    bottom_layout = QHBoxLayout(bottom_panel)
    bottom_layout.setContentsMargins(6, 0, 6, 0)
    bottom_layout.setSpacing(0)
    container_layout.addWidget(bottom_panel, stretch=0)

    panels_viewport = QWidget(bottom_panel)
    panels_viewport.setContentsMargins(0, 0, 0, 0)
    panels_viewport.setFixedHeight(panel_height)
    panels_viewport.installEventFilter(viewport_event_filter)
    bottom_layout.addWidget(panels_viewport, stretch=1)

    front_panel = QWidget(panels_viewport)
    control_panel = QWidget(panels_viewport)

    return BottomScaffoldRefs(
        bottom_panel=bottom_panel,
        bottom_layout=bottom_layout,
        panels_viewport=panels_viewport,
        front_panel=front_panel,
        control_panel=control_panel,
    )
