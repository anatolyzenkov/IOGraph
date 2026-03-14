from __future__ import annotations


def check_updates_label(*, is_downloading: bool, is_checking: bool, tr=lambda s: s) -> str:
    if is_downloading:
        return tr("update.download.in_progress")
    if is_checking:
        return tr("update.check.in_progress")
    return tr("update.check.idle")


def apply_check_updates_status(*, label: str, menu_action, tray_action) -> None:
    if menu_action is not None:
        menu_action.setText(label)
        menu_action.setEnabled(True)
    if tray_action is not None:
        tray_action.setText(label)
        tray_action.setEnabled(True)
