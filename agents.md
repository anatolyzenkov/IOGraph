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

## I18n wave (feature/i18n-foundation)
- Status:
  - branch: `feature/i18n-foundation`
  - id-key migration is active and already applied to menu/tray/update/main flows.
  - supported languages now include:
    - `en`, `de`, `fr`, `es`, `pt`, `it`, `ru`, `uk`, `tr`, `ar`, `zh-Hans`, `zh-Hant`.
  - language mode:
    - `auto` (system locale with fallback to `en`)
    - explicit language selection via menu/tray.
- Implemented:
  - `I18nService` with id->source mapping and translation lookup.
  - language selection UI in main and tray menus.
  - coverage checker scripts:
    - `scripts/smoke_regression.py`
    - `scripts/i18n_missing.py`
  - current i18n coverage target keys are at 100% according to `i18n_missing.py` report.
- Current task:
  - audit all remaining hardcoded user-facing strings in `iograph/**` and remove/replace with i18n ids where appropriate.

## I18n hardcoded audit (2026-03-14)
- Confirmed user-facing hardcoded strings still present in:
  - `iograph/core/session_controller.py`
    - timer/period phrases and date/ordinal fragments (`Just started`, `From ... to ...`, `second/minute/hour/day`, `1st/2nd/3rd/...`).
  - `iograph/core/tracking_ui_decisions.py`
    - toggle labels (`Pause`, `Start`, `Resume`).
  - `iograph/core/tracking_controller.py`
    - tracking status/reset confirmation text (`Tracking started/stopped`, reset confirmation prompt).
  - `iograph/core/export_controller.py`
    - export/preview status strings.
  - `iograph/core/update_ui_decisions.py`
    - update-ready prompts and install action labels.
  - `iograph/ui/desktop_snapshot_controller.py`
    - desktop snapshot success/failure status texts.
  - `iograph/ui/support_prompt.py`
    - support prompt button labels (`Maybe later`, `Support the project`).
  - `iograph/app/bootstrap.py`
    - single-instance message (`IOGraph is already running.`).
  - `iograph/main.py`
    - app window title and about tagline text are still literal.
- Next migration target:
  - route all above strings through `I18nService` id keys, keep core modules UI-agnostic by passing translator callables from `MainWindow`.

## I18n runtime updates (2026-03-14, latest)
- Removed language-change restart notice popup; language now applies live for menu/tray/panel/settings labels.
- Dynamic toggle labels now translated via i18n keys:
  - `menu.start`
  - `menu.pause`
  - `menu.resume`
- Session dynamic time/period labels are normalized to language-neutral numeric format:
  - elapsed: `HH:MM:SS` (or `D HH:MM:SS` for multi-day sessions)
  - period: `HH:MM` or `HH:MM DD.MM -> HH:MM DD.MM`
- This avoids English-only wording in timer/period labels while full deep i18n migration of `core/*` continues.

## I18n dynamic labels (2026-03-14, latest)
- Reworked session dynamic labels back to human-readable style with i18n templates:
  - time: `Just started`, `{value} second/minute/hour/day` (localized via keys)
  - period: `From {start}` / `From {start} to {end}` (localized via keys)
- Reset confirmation popup is now fully i18n-driven:
  - base prompt + long-session suffix template use translation keys.
- Support prompt buttons are now i18n-driven:
  - `Maybe later`
  - `Support the project`

## Pluralization engine (2026-03-14, latest)
- Added plural-category routing in `I18nService` (`one/few/many/other` where applicable).
- Implemented Slavic plural rules for:
  - Russian (`ru`)
  - Ukrainian (`uk`)
- Wired session timer text to use `i18n.plural(...)`:
  - now correctly handles forms like `21 секунда`, `22 секунды`, `25 секунд`.

## Update dialogs i18n (2026-03-14, latest)
- Localized update/install prompt decisions by routing `UpdateUiDecisions` through translator callable:
  - already downloaded prompt (open package / close+install)
  - ready-to-install prompt
  - install action labels (`Install Downloaded Update...`, `Open Update Package`, `Update now`)
- Wired translation into:
  - `MainWindow` update check and download prompt flow
  - install action sync helper (`ui/update_actions.py`)
- About dialog tagline moved to i18n key (`about.tagline`).

## Additional i18n cleanup (2026-03-14, latest)
- Localized export status strings via i18n keys in `core/export_controller.py`:
  - exporting / saved / failed / preview rendering / preview ready.
- Localized desktop snapshot status strings in `ui/desktop_snapshot_controller.py`:
  - snapshot updated / snapshot failed.
- Wired both flows from `main.py` through translator callback (`tr=self._t`).

## Bootstrap i18n (2026-03-14, latest)
- Localized Windows single-instance popup in `app/bootstrap.py` using `I18nService` + `AppSettings`:
  - title: `app.single_instance.title`
  - message: `app.single_instance.message`
- Added translations for `app.single_instance.message` in `ru` and `uk`.

## New language packs (2026-03-14, latest)
- Added new language options:
  - `ja` (Japanese)
  - `kk` (Kazakh)
  - `sr` (Serbian)
- Extended `SUPPORTED_LANGUAGES` and `LANGUAGE_LABELS` in `iograph/services/i18n.py`.
- Added base menu/update translation entries in `_TRANSLATIONS` for all three new languages.
- Added runtime/session/dialog coverage entries in `_EXTRA_TRANSLATIONS` for all three new languages.
- Added Serbian plural handling:
  - new `sr` templates in `_PLURAL_TEMPLATES`
  - plural category routing (`one/few/other`) in `_plural_category`.

## Language menu UX (2026-03-14, latest)
- Language options are now sorted by displayed language label.
- `Auto (System)` is pinned at top and visually separated by a divider from explicit language choices.
- Applied in both:
  - main menu language submenu
  - tray menu language submenu

## Locale variants and date/time formatting (2026-03-14, latest)
- Added explicit locale variants:
  - `es-419`, `es-ES`
  - `pt-BR`, `pt-PT`
- Backward-compatible migration for legacy stored values:
  - `es` -> `es-419`
  - `pt` -> `pt-BR`
- Auto language resolution now chooses Spanish/Portuguese variant by system locale region.
- Added translation fallback chains:
  - `es-ES -> es-419`
  - `pt-PT -> pt-BR`
- Added `I18nService` locale helpers:
  - `effective_qlocale()`
  - `format_time(...)`
  - `format_short_date(...)`
- Session period label now uses locale-aware date/time formatting (via callbacks from `MainWindow`), while keeping localized `From ... to ...` templates.

## Locale variants polishing (2026-03-14, latest)
- Migrated translation dictionary keys from legacy:
  - `es` -> `es-419`
  - `pt` -> `pt-BR`
- Added first explicit variant overrides:
  - `pt-PT` (lexical differences like *definições*, *guardar*)
  - `es-ES` (minor lexical differences)
- Export filename generation is now locale-aware and filesystem-safe:
  - uses localized period/time labels
  - sanitizes invalid filename characters (`<>:\"/\\|?*` and control chars)
  - trims trailing dots/spaces and collapses whitespace
- Removed legacy settings alias-compatibility for old language codes (`es`/`pt`) to keep i18n mode normalization minimal and explicit.
    
