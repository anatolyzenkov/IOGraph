# Project Instructions

## Goal
Ship and maintain IOGraph Python + PyQt as a stable production app with reliable update flow.

## Working Rules
- Implement changes in Python codebase (`iograph_2`) unless explicitly requested otherwise.
- Work in small steps.
- After code edits, run `python3 -m compileall iograph`.
- Reporting format after each step:
  1. What was made
  2. What remains next

## Branch / Release Policy
- Primary dev and release branch: `python-port` in `anatolyzenkov/IOGraph`.
- Java legacy baseline tag is preserved: `java-v1.0.3`.
- Current stable tag: `v2.0.2`.
- Old RC tags were cleaned up from GitHub and local repo.
- RC/beta tags must use zero-padded numeric suffixes (e.g. `v2.0.2-rc.001`).

## CI / Build Status
- GitHub Actions:
  - `Python CI` on `python-port`
  - `Release macOS` on tag `v*`
  - `Release Windows` on tag `v*`
- Actions versions:
  - `actions/checkout@v5`
  - `actions/setup-python@v6`
- Ubuntu CI installs required PyQt6 system libs before smoke checks.
- macOS release target:
  - build as `universal2` app bundle
  - CI must verify both `x86_64` and `arm64` slices are present

## Release Artifacts
- macOS:
  - `IOGraph-macos-<version>.zip`
  - `IOGraph-macos-<version>.dmg`
- Windows:
  - `IOGraph-windows-<version>.zip`
- DMG volume icon asset:
  - `packaging/assets/dmg/IOGraphVolume.icns`

## Version Source Priority
1. `IOGRAPH_VERSION` env
2. bundled `Info.plist` (`CFBundleShortVersionString`) for frozen app
3. repo `VERSION` file for local source runs
4. fallback `dev`

## Update Flow (Current)
- Source: GitHub Releases API (`anatolyzenkov/IOGraph`).
- Manual update check:
  - from menu/tray `Check for Updates`
  - prompts download and install/open package
- Auto-update:
  - setting key: `options/automatic_update` (default `True`)
  - checks on startup (~1.2s delay) and every 6 hours
  - downloads into:
    - `~/Library/Application Support/IOGraph/updates/<asset_name>`
  - one rolling file per asset name
- Install action label is dynamic:
  - version-aware install label if file exists
  - fallback: `Install Downloaded Update`
- Download metadata keys (`QSettings`):
  - `updates/last_downloaded_path`
  - `updates/last_downloaded_version`
  - `updates/last_auto_downloaded_version`
  - `updates/last_prompted_version`

## Update UX Principle
- Do not expose technical update internals to users unless strictly necessary.
- If multiple downloaded update artifacts exist and one is corrupted, app should recover automatically:
  - validate downloaded package before install,
  - retry download when package is invalid,
  - switch to valid artifact path when possible,
  - clean broken metadata/artifacts silently.
- User-facing update messages should stay simple and action-oriented (no low-level command errors).

## Localization Status
- Supported languages:
  - `en`, `de`, `fr`, `es-419`, `es-ES`, `pt-BR`, `pt-PT`, `it`, `ru`, `uk`, `tr`, `ar`, `zh-Hans`, `zh-Hant`, `ja`, `kk`, `sr`, `sv`, `nl`, `pl`, `el`
- Current coverage:
  - 100% required translation key coverage for all supported languages (`117/117`).
- Release gate:
  - no English fallback in update dialogs for non-English UI.

## Pre-Release / Release Checklist
1. `python3 -m compileall iograph`
2. `python scripts/smoke_regression.py`
3. translation audit via `I18nService.missing_translation_ids(...)` must be empty for all supported languages
4. push branch
5. create/push tag
6. verify both release workflows (`Release macOS` and `Release Windows`)

## Validation Notes
- Apple Silicon (`arm64`) can be validated locally.
- Intel macOS (`x86_64`) must be validated either:
  - by CI binary slice check, and
  - by external manual confirmation on an Intel Mac when architecture compatibility is changed.
