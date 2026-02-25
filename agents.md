# Project instructions

## Goal
Maintain and evolve IOGraph Python + PyQt implementation.
Behavior parity with Java is still important, but Java is now legacy reference.

## Rules
- New features and fixes are implemented in Python codebase unless explicitly requested otherwise.
- Work in small steps; run `python3 -m compileall iograph` after edits.

## Reporting
After each step:
1. what was made
2. what remains next

## New Feature Baseline (raw-data-first session model)
- Tracking raw data is the primary source of truth for the current session.
- Switching drawing style must not force reset/confirmation:
  - colorful <-> monochrome
  - with stop circles <-> without stop circles
  - app must re-render full canvas and preview from raw data in the new style.
- On app start, recording starts automatically.
- On app close, raw data is persisted to disk.
- On next app start, raw data is restored and re-rendered.
- Restored session must also restore timing labels:
  - total time
  - time period
- Raw data is deleted only by explicit `Reset`.

## Build And Release (macOS first)
### Goal
- Produce reproducible desktop builds for macOS (first) and Windows (later).
- Publish builds automatically to GitHub Releases.
- Support update checks and optional automatic updates from GitHub-hosted release metadata.

### Packaging
- Use `PyInstaller` for application packaging.
- macOS output target:
  - `IOGraph.app`
  - distributable archive (`.dmg` or `.zip`)
- Keep all runtime assets in `iograph/resources` and include them in packaging config.

### Versioning
- Use semantic version tags: `vX.Y.Z`.
- Only tagged commits trigger production release pipeline.
- App version in code and release tag must match.

### CI/CD (GitHub Actions)
- Pipeline trigger: push tag `v*`.
- Steps:
  1. create clean env
  2. install deps
  3. build app with `PyInstaller`
  4. sign app (`codesign`)
  5. notarize app (Apple notary)
  6. staple notarization
  7. package artifact (`.dmg`/`.zip`)
  8. publish artifact to GitHub Release
  9. update and publish update feed metadata (appcast/manifest)

### Secrets/Signing (macOS)
- Configure GitHub secrets for:
  - Apple Developer certificate and password
  - Keychain/import password
  - Apple notarization credentials (API key or app-specific)
- Never store signing material in repo.

### Auto-Update Strategy
- Source of updates: GitHub Releases metadata feed (appcast/manifest).
- App behavior:
  - manual check command: always available
  - automatic check/update: controlled by user setting (`automatic_update`)
- Persist setting with `QSettings`.
- If auto-update is ON: check on startup (and optionally on interval).

### Windows (later)
- Keep same release model (GitHub Releases + metadata feed).
- Introduce Windows updater path (e.g. WinSparkle or equivalent) when Windows packaging is started.

### Implementation Rule
- Do not implement ad-hoc updater logic that bypasses signed release artifacts.
- Keep update pipeline deterministic and CI-driven; local manual releases are fallback only.
