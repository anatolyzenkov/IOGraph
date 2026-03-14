from __future__ import annotations

import compileall
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


MODULES = (
    "iograph.main",
    "iograph.tracker",
    "iograph.app.bootstrap",
    "iograph.app.signals",
    "iograph.services.i18n",
    "iograph.core.update_controller",
    "iograph.core.update_service",
    "iograph.core.update_storage",
    "iograph.core.session_controller",
    "iograph.core.session_storage",
    "iograph.core.session_cache_restore",
    "iograph.core.tracking_controller",
    "iograph.core.export_controller",
    "iograph.ui.menu_builder",
    "iograph.ui.tray_menu",
    "iograph.ui.settings_panel",
    "iograph.ui.toggle_button",
    "iograph.ui.desktop_snapshot_controller",
)


def main() -> int:
    ok = compileall.compile_dir("iograph", force=False, quiet=1)
    if not ok:
        print("Compile smoke failed")
        return 1

    for name in MODULES:
        importlib.import_module(name)

    print("Smoke regression check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
