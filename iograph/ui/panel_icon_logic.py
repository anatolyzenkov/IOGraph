from __future__ import annotations


def save_icon_name(*, enabled: bool, pressed: bool) -> str:
    if not enabled:
        return "SaveDisabledBtn.png"
    if pressed:
        return "SavePressedBtn.png"
    return "SaveBtn.png"


def setup_icon_name(*, checked: bool, pressed: bool) -> str:
    if pressed:
        return "SetupPressedBtnC.png" if checked else "SetupPressedBtn.png"
    return "SetupBtnC.png" if checked else "SetupBtn.png"


def update_desktop_icon_name(*, enabled: bool, pressed: bool) -> str:
    if not enabled:
        return "UpdateDesktopDisabledBtn.png"
    if pressed:
        return "UpdateDesktopPressedBtn.png"
    return "UpdateDesktopBtn.png"


def heart_icon_name(*, pressed: bool) -> str:
    return "HeartPressedBtn.png" if pressed else "HeartBtn.png"
