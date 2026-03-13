from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QMenu


@dataclass(frozen=True)
class TrayMenuRefs:
    menu: QMenu
    install_update_action: object
    update_separator_action: object
    toggle_action: object
    reset_action: object
    save_image_action: object
    save_csv_action: object
    settings_action: object
    check_updates_action: object
    auto_update_action: object


def build_tray_menu(
    parent,
    *,
    tray_exit_label: str,
    on_open_downloaded_update,
    on_toggle_tracking,
    on_reset,
    on_save_image,
    on_save_csv,
    on_toggle_settings,
    on_check_updates,
    on_auto_update_toggled,
    on_open_about_iographica,
    on_open_website,
    on_open_source,
    on_open_support,
    on_about,
    on_quit,
) -> TrayMenuRefs:
    tray_menu = QMenu(parent)
    tray_install_update_action = tray_menu.addAction("Update now")
    tray_install_update_action.triggered.connect(on_open_downloaded_update)
    tray_update_sep_action = tray_menu.addSeparator()

    tray_toggle_action = tray_menu.addAction("Start")
    tray_toggle_action.triggered.connect(on_toggle_tracking)
    tray_reset_action = tray_menu.addAction("Reset")
    tray_reset_action.triggered.connect(on_reset)
    tray_reset_action.setEnabled(False)

    tray_menu.addSeparator()
    tray_save_image_action = tray_menu.addAction("Save Image...")
    tray_save_image_action.triggered.connect(on_save_image)
    tray_save_image_action.setEnabled(False)
    tray_save_csv_action = tray_menu.addAction("Save Raw Data...")
    tray_save_csv_action.triggered.connect(on_save_csv)
    tray_save_csv_action.setEnabled(False)

    tray_menu.addSeparator()
    tray_settings_action = tray_menu.addAction("Show Settings")
    tray_settings_action.triggered.connect(on_toggle_settings)

    more_menu = tray_menu.addMenu("More")
    tray_check_updates_action = more_menu.addAction("Check for Updates")
    tray_check_updates_action.triggered.connect(on_check_updates)
    tray_auto_update_action = more_menu.addAction("Check for Updates Automatically")
    tray_auto_update_action.setCheckable(True)
    tray_auto_update_action.toggled.connect(on_auto_update_toggled)

    more_menu.addSeparator()
    links_menu = more_menu.addMenu("Resources")
    links_menu.addAction("About IOGraphica", on_open_about_iographica)
    links_menu.addAction("IOGraph Website", on_open_website)
    links_menu.addAction("Get Source Code", on_open_source)
    links_menu.addAction("Support IOGraphica", on_open_support)

    more_menu.addSeparator()
    more_menu.addAction("About IOGraph", on_about)
    tray_menu.addSeparator()
    tray_menu.addAction(tray_exit_label, on_quit)

    return TrayMenuRefs(
        menu=tray_menu,
        install_update_action=tray_install_update_action,
        update_separator_action=tray_update_sep_action,
        toggle_action=tray_toggle_action,
        reset_action=tray_reset_action,
        save_image_action=tray_save_image_action,
        save_csv_action=tray_save_csv_action,
        settings_action=tray_settings_action,
        check_updates_action=tray_check_updates_action,
        auto_update_action=tray_auto_update_action,
    )
