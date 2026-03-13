from __future__ import annotations

from pathlib import Path

from ..core.update_ui_decisions import UpdateUiDecisions


def sync_install_update_actions(
    *,
    has_downloaded_update: bool,
    downloaded_path: Path | None,
    menu_action,
    tray_action,
    tray_separator_action,
) -> None:
    label = UpdateUiDecisions.install_action_label(downloaded_path)
    if menu_action is not None:
        menu_action.setText(label)
        menu_action.setEnabled(has_downloaded_update)
    if tray_action is not None:
        tray_action.setText(label)
        tray_action.setEnabled(has_downloaded_update)
        tray_action.setVisible(has_downloaded_update)
    if tray_separator_action is not None:
        tray_separator_action.setVisible(has_downloaded_update)
