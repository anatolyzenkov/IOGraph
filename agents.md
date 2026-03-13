# Project instructions

## Goal
Ship IOGraph Python + PyQt as production app with stable update flow.

## Rules
- Implement changes in Python codebase (`iograph_2`) unless explicitly requested otherwise.
- Work in small steps; run `python3 -m compileall iograph` after edits.
- Reporting format after each step:
  1. What was made
  2. What remains next

## Current branch/release policy
- Primary dev branch: `python-port` in `anatolyzenkov/IOGraph`.
- Active refactor branch: `refactor/pyqt-architecture` (post-`v2.0.0` architecture work).
- Java legacy baseline tag is preserved: `java-v1.0.3`.
- Stable `v2.0.0` is published (2026-03-12).
- Future pre-releases should still use `beta` / `rc` tags before next stable.
- Windows code-signing is postponed for now (test phase).
- Windows builds are available, but installation may require manual SmartScreen bypass steps.
- Pre-release tag naming (required):
  - use zero-padded numeric suffixes for correct GitHub ordering.
  - examples: `v2.0.0-rc.011`, `v2.0.0-rc.012`, `v2.0.0-beta.001`.
  - legacy non-padded tags remain as-is; all new tags must be padded.

## Release notes policy (Windows test builds)
- For every Windows `beta`/`rc` release, include a short SmartScreen bypass section:
  1. Right click installer -> `Properties` -> `Unblock` -> `Apply`.
  2. If SmartScreen blocks: `More info` -> `Run anyway`.
  3. Optional PowerShell: `Unblock-File "<path-to-installer>"`.
- Mark this as temporary until code-signing is enabled.

## Build/CI status (actual)
- GitHub Actions:
  - `Python CI` on `python-port` (compile checks).
  - `Release macOS` on tag `v*`.
  - `Release Windows` on tag `v*`.
- macOS artifacts:
  - `IOGraph-macos.zip`
  - `IOGraph-macos.dmg` with configured layout.
- Windows artifacts:
  - `IOGraph-windows-<version>.zip`
- Packaging asset path:
  - `packaging/assets/dmg/IOGraphVolume.icns`.
- Dedicated smoke/update regression workflow is not implemented yet.

## Current working state (2026-03-13)
- Branch/tag status:
  - `python-port` is release branch.
  - `refactor/pyqt-architecture` is active development branch.
  - Stable tag: `v2.0.0` (published).
  - Last retained RC tag: `v2.0.0-rc.044`.
  - Old RC tags/releases were cleaned up.
- Runtime/UX state:
  - Long-session timer/circle regressions were fixed and validated during RC cycle.
  - Help menu and tray `More` menu group external links under `Resources`.
  - Donation prompts are one-time events:
    - first image save
    - first raw data save
  - Donation links include UTM source labels by entry point.
- macOS signing/notarization:
  - Developer ID signing + notarization are active in release pipeline.
  - Stable notarized artifacts are published for `v2.0.0`.

## Version source
- App version resolution order:
  1. `IOGRAPH_VERSION` env
  2. bundled `Info.plist` (`CFBundleShortVersionString`) for frozen app
  3. repo `VERSION` file for local source runs
  4. fallback `dev`.

## Update flow (as implemented now)
- Update source: GitHub Releases API (`anatolyzenkov/IOGraph`).
- Manual check:
  - menu/tray `Check for Updates`
  - asks `Download now?`
  - if yes: downloads asset (`.dmg/.zip` on macOS) and prompts `Install now?`
  - if no: just closes dialog.
- Auto update:
  - controlled by `options/automatic_update` (default `True`)
  - checks once on startup (~1.2s delay) and then every 6 hours
  - quiet mode (no noisy notifications)
  - downloads to fixed path:
    - `~/Library/Application Support/IOGraph/updates/<asset_name>`
  - keeps one rolling file per asset name
  - after download prompts install; if install is opened, app closes automatically.
- Install action:
  - dynamic menu/tray item:
    - `Install IOGraph <version>` when downloaded file exists
    - fallback label `Install Downloaded Update`.
- Stored update keys in `QSettings`:
  - `updates/last_downloaded_path`
  - `updates/last_downloaded_version`
  - `updates/last_auto_downloaded_version`
  - `updates/last_prompted_version`.
- Cleanup:
  - on startup, if current app version is already >= downloaded version, old downloaded update artifacts are removed.

## Update flow target (next)
- Keep macOS updater helper flow reliable across future releases:
  1. download ZIP update
  2. close app
  3. replace app in `/Applications`
  4. relaunch
- Keep `.dmg` as manual install path.
- Add lightweight smoke/update regression CI checks (post-release backlog).
- Windows code-signing remains postponed.

## Refactor track (post-2.0.0)
- Goal: split monolithic `iograph/main.py` into maintainable PyQt architecture with explicit boundaries.
- Target structure:
  - `iograph/ui` for widgets/presentation only.
  - `iograph/core` for tracking/session/update business logic.
  - `iograph/app` for bootstrap and wiring.
  - `iograph/services` for cross-cutting services (`QSettings`, filesystem, etc.).
- Communication model:
  - use Qt signals/slots for module-to-module communication;
  - avoid direct cross-layer state mutation.
- First milestone:
  - introduce centralized settings service and migrate raw `QSettings` access behind it without behavior changes.

## Refactor roadmap (ordered, do not skip)
- Step 1: Foundation (in progress)
  - [x] Add module skeleton: `app/core/ui/services`.
  - [x] Add centralized settings wrapper (`AppSettings`, `SettingsKeys`).
  - [x] Replace most magic settings keys in `main.py` with `SettingsKeys`.
  - [x] Extract update service/workers/storage/controller into `core`.
  - [x] Finish update UI decision extraction (prompt text/action branching).
- Step 2: Tracking/session extraction
  - [x] Move tracking/session orchestration from `main.py` into `core/session_controller.py`.
  - [x] Keep `TrackCanvas` rendering in `ui/tracker` or existing module until behavior parity is verified.
  - [x] Introduce signal-based session events for UI updates.
  - Note: final behavior parity for start/pause/resume/reset/restore must be confirmed via local manual GUI run.
- Step 3: Export/render extraction
  - [x] Move export and preview rerender orchestration into `core/export_controller.py`.
  - [x] Keep UI-specific progress dialogs in `main.py` (temporary), business logic in `core`.
- Step 4: UI split
  - [x] Split monolithic `MainWindow` into smaller UI/core helpers (iterative extraction complete for current scope).
  - Extracted so far:
    - `ui/tray_menu.py`
    - `ui/menu_builder.py`
    - `ui/icon_loader.py`
    - `ui/settings_panel.py`
    - `ui/panel_widgets.py`
    - `ui/layout_scaffold.py`
    - `ui/toggle_button.py`
    - `ui/support_prompt.py`
    - `ui/panel_icon_logic.py`
    - `ui/tray_window.py`
    - `ui/desktop_snapshot_controller.py`
    - `ui/update_actions.py`
    - `ui/update_status.py`
    - `core/session_cache_restore.py`
  - [x] Keep startup/single-instance wiring in `app/bootstrap.py`.
  - Remaining (optional next refactor wave):
    - move remaining `MainWindow` orchestration into `ui/main_window.py` + presenter/service layer split.
- Step 5: Stabilization
  - [x] Add lightweight regression checks for update + startup in CI.
  - [x] Validate behavior parity before merging back to `python-port` (manual pass done; full `Install Downloaded Update` path to be rechecked on next RC with a fresh release).
    
