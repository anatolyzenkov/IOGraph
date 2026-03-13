from __future__ import annotations


def check_updates_label(*, is_downloading: bool, is_checking: bool) -> str:
    if is_downloading:
        return "Downloading Update..."
    if is_checking:
        return "Checking for Updates..."
    return "Check for Updates"


def apply_check_updates_status(*, label: str, menu_action, tray_action) -> None:
    if menu_action is not None:
        menu_action.setText(label)
        menu_action.setEnabled(True)
    if tray_action is not None:
        tray_action.setText(label)
        tray_action.setEnabled(True)
