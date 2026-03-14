from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import QMenu


@dataclass(frozen=True)
class TrayMenuRefs:
    menu: QMenu
    more_menu: QMenu
    language_menu: QMenu
    links_menu: QMenu
    install_update_action: object
    update_separator_action: object
    toggle_action: object
    reset_action: object
    save_image_action: object
    save_csv_action: object
    settings_action: object
    check_updates_action: object
    auto_update_action: object
    about_action: object
    quit_action: object
    about_iographica_action: object
    website_action: object
    source_action: object
    support_action: object
    language_actions: dict[str, object]


def build_tray_menu(
    parent,
    *,
    tr,
    language_options,
    current_language_mode: str,
    on_language_mode_selected,
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
    tray_install_update_action = tray_menu.addAction(tr("menu.update_now"))
    tray_install_update_action.triggered.connect(on_open_downloaded_update)
    tray_update_sep_action = tray_menu.addSeparator()

    tray_toggle_action = tray_menu.addAction(tr("menu.start"))
    tray_toggle_action.triggered.connect(on_toggle_tracking)
    tray_reset_action = tray_menu.addAction(tr("menu.reset"))
    tray_reset_action.triggered.connect(on_reset)
    tray_reset_action.setEnabled(False)

    tray_menu.addSeparator()
    tray_save_image_action = tray_menu.addAction(tr("menu.save_image"))
    tray_save_image_action.triggered.connect(on_save_image)
    tray_save_image_action.setEnabled(False)
    tray_save_csv_action = tray_menu.addAction(tr("menu.save_raw_data"))
    tray_save_csv_action.triggered.connect(on_save_csv)
    tray_save_csv_action.setEnabled(False)

    tray_menu.addSeparator()
    tray_settings_action = tray_menu.addAction(tr("tray.show_settings"))
    tray_settings_action.triggered.connect(on_toggle_settings)

    more_menu = tray_menu.addMenu(tr("tray.more"))
    tray_check_updates_action = more_menu.addAction(tr("menu.check_updates"))
    tray_check_updates_action.triggered.connect(on_check_updates)
    tray_auto_update_action = more_menu.addAction(tr("menu.auto_updates"))
    tray_auto_update_action.setCheckable(True)
    tray_auto_update_action.toggled.connect(on_auto_update_toggled)

    language_menu = more_menu.addMenu(tr("menu.language"))
    language_group = QActionGroup(parent)
    language_group.setExclusive(True)
    language_actions: dict[str, QAction] = {}
    for code, title in language_options:
        action = QAction(title, parent)
        action.setCheckable(True)
        action.setChecked(code == current_language_mode)
        action.triggered.connect(lambda checked, mode=code: on_language_mode_selected(mode) if checked else None)
        language_group.addAction(action)
        language_menu.addAction(action)
        language_actions[code] = action
        if code == "auto":
            language_menu.addSeparator()

    more_menu.addSeparator()
    links_menu = more_menu.addMenu(tr("menu.resources"))
    about_iographica_action = links_menu.addAction(tr("menu.about_iographica"), on_open_about_iographica)
    website_action = links_menu.addAction(tr("menu.iograph_website"), on_open_website)
    source_action = links_menu.addAction(tr("menu.get_source"), on_open_source)
    support_action = links_menu.addAction(tr("menu.support_iographica"), on_open_support)

    more_menu.addSeparator()
    about_action = more_menu.addAction(tr("menu.about_iograph"), on_about)
    tray_menu.addSeparator()
    quit_action = tray_menu.addAction(tray_exit_label, on_quit)

    return TrayMenuRefs(
        menu=tray_menu,
        more_menu=more_menu,
        language_menu=language_menu,
        links_menu=links_menu,
        install_update_action=tray_install_update_action,
        update_separator_action=tray_update_sep_action,
        toggle_action=tray_toggle_action,
        reset_action=tray_reset_action,
        save_image_action=tray_save_image_action,
        save_csv_action=tray_save_csv_action,
        settings_action=tray_settings_action,
        check_updates_action=tray_check_updates_action,
        auto_update_action=tray_auto_update_action,
        about_action=about_action,
        quit_action=quit_action,
        about_iographica_action=about_iographica_action,
        website_action=website_action,
        source_action=source_action,
        support_action=support_action,
        language_actions=language_actions,
    )
