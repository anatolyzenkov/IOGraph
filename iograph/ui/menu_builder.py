from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QAction


@dataclass(frozen=True)
class MenuActionRefs:
    save_image_action: object
    save_csv_action: object
    reset_action: object
    tracking_toggle_action: object
    tracking_reset_action: object
    ignore_stops_action: object
    colorful_action: object
    use_desktop_action: object
    multi_monitor_action: object
    refresh_desktop_action: object
    check_updates_action: object
    auto_update_action: object
    install_downloaded_update_action: object


def build_main_menu(
    parent,
    *,
    on_save_image,
    on_save_csv,
    on_reset,
    on_quit,
    on_toggle_tracking,
    on_ignore_stops_toggled,
    on_colorful_toggled,
    on_use_desktop_toggled,
    on_multi_monitor_toggled,
    on_refresh_desktop_snapshot,
    on_about,
    on_check_updates,
    on_auto_update_toggled,
    on_open_downloaded_update,
    on_open_about_iographica,
    on_open_website,
    on_open_source,
    on_open_support,
) -> MenuActionRefs:
    file_menu = parent.menuBar().addMenu("&File")
    tracking_menu = parent.menuBar().addMenu("&Tracking")
    options_menu = parent.menuBar().addMenu("&Options")
    help_menu = parent.menuBar().addMenu("&Help")

    save_image_action = QAction("Save &Image...", parent)
    save_image_action.setShortcut("Ctrl+S")
    save_image_action.triggered.connect(on_save_image)
    file_menu.addAction(save_image_action)

    save_csv_action = QAction("Save &Raw Data...", parent)
    save_csv_action.setShortcut("Ctrl+Shift+S")
    save_csv_action.triggered.connect(on_save_csv)
    file_menu.addAction(save_csv_action)

    reset_action = QAction("&Reset", parent)
    reset_action.setShortcut("Ctrl+R")
    reset_action.triggered.connect(on_reset)
    file_menu.addAction(reset_action)

    file_menu.addSeparator()
    exit_action = QAction("E&xit", parent)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.triggered.connect(on_quit)
    file_menu.addAction(exit_action)

    tracking_toggle_action = QAction("Start", parent)
    tracking_toggle_action.setShortcut("Ctrl+R")
    tracking_toggle_action.triggered.connect(on_toggle_tracking)
    tracking_menu.addAction(tracking_toggle_action)

    tracking_reset_action = QAction("Reset", parent)
    tracking_reset_action.setShortcut("Ctrl+N")
    tracking_reset_action.triggered.connect(on_reset)
    tracking_menu.addAction(tracking_reset_action)

    ignore_stops_action = QAction("Ignore Mouse Stops", parent)
    ignore_stops_action.setCheckable(True)
    ignore_stops_action.toggled.connect(on_ignore_stops_toggled)
    options_menu.addAction(ignore_stops_action)

    colorful_action = QAction("Colorful Scheme", parent)
    colorful_action.setCheckable(True)
    colorful_action.toggled.connect(on_colorful_toggled)
    options_menu.addAction(colorful_action)

    use_desktop_action = QAction("Use Desktop Background", parent)
    use_desktop_action.setCheckable(True)
    use_desktop_action.toggled.connect(on_use_desktop_toggled)
    options_menu.addAction(use_desktop_action)

    multi_monitor_action = QAction("Use Multiple Monitors", parent)
    multi_monitor_action.setCheckable(True)
    multi_monitor_action.setChecked(True)
    multi_monitor_action.toggled.connect(on_multi_monitor_toggled)
    options_menu.addAction(multi_monitor_action)

    refresh_desktop_action = QAction("Update Desktop Snapshot", parent)
    refresh_desktop_action.triggered.connect(on_refresh_desktop_snapshot)
    refresh_desktop_action.setEnabled(False)
    options_menu.addAction(refresh_desktop_action)

    about_action = QAction("About IOGraph", parent)
    about_action.triggered.connect(on_about)
    help_menu.addAction(about_action)
    help_menu.addSeparator()

    check_updates_action = QAction("Check for Updates", parent)
    check_updates_action.triggered.connect(on_check_updates)
    help_menu.addAction(check_updates_action)

    auto_update_action = QAction("Check for Updates Automatically", parent)
    auto_update_action.setCheckable(True)
    auto_update_action.toggled.connect(on_auto_update_toggled)
    help_menu.addAction(auto_update_action)

    install_downloaded_action = QAction("Update now", parent)
    install_downloaded_action.triggered.connect(on_open_downloaded_update)
    help_menu.addAction(install_downloaded_action)

    help_menu.addSeparator()
    resources_menu = help_menu.addMenu("Resources")
    resources_menu.addAction("About IOGraphica", on_open_about_iographica)
    resources_menu.addAction("IOGraph Website", on_open_website)
    resources_menu.addAction("Get Source Code", on_open_source)
    resources_menu.addAction("Support IOGraphica", on_open_support)

    return MenuActionRefs(
        save_image_action=save_image_action,
        save_csv_action=save_csv_action,
        reset_action=reset_action,
        tracking_toggle_action=tracking_toggle_action,
        tracking_reset_action=tracking_reset_action,
        ignore_stops_action=ignore_stops_action,
        colorful_action=colorful_action,
        use_desktop_action=use_desktop_action,
        multi_monitor_action=multi_monitor_action,
        refresh_desktop_action=refresh_desktop_action,
        check_updates_action=check_updates_action,
        auto_update_action=auto_update_action,
        install_downloaded_update_action=install_downloaded_action,
    )
