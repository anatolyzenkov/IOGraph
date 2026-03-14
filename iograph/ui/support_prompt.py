from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox


def show_support_prompt(
    parent,
    *,
    title: str,
    text: str,
    informative_text: str,
    reject_text: str = "Maybe later",
    accept_text: str = "Support the project",
) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(text)
    box.setInformativeText(informative_text)
    box.addButton(reject_text, QMessageBox.ButtonRole.RejectRole)
    support_btn = box.addButton(accept_text, QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(support_btn)
    box.exec()
    return box.clickedButton() == support_btn
