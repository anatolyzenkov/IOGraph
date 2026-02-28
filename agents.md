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
- Java legacy baseline tag is preserved: `java-v1.0.3`.
- Until signing/notarization and Windows pipeline are ready:
  - publish only `beta` / `rc`
  - do not publish stable `v2.0.0`.
- Windows code-signing is postponed for now (test phase).
- Keep Windows installer flow in RC, but treat SmartScreen bypass as a temporary testing procedure.
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
- macOS artifacts:
  - `IOGraph-macos.zip`
  - `IOGraph-macos.dmg` with configured layout.
- Packaging asset path:
  - `packaging/assets/dmg/IOGraphVolume.icns`.

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
- Add signed + notarized macOS release pipeline.
- Replace DMG-assisted install with real updater helper flow:
  1. download
  2. close app
  3. replace app in `/Applications`
  4. relaunch.
- Add Windows build + installer pipeline and align update UX cross-platform.
    
