from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox


def show_support_prompt(parent, *, title: str, text: str, informative_text: str) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(text)
    box.setInformativeText(informative_text)
    box.addButton("Maybe later", QMessageBox.ButtonRole.RejectRole)
    support_btn = box.addButton("Support the project", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(support_btn)
    box.exec()
    return box.clickedButton() == support_btn
