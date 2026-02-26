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
- Raw data is the source of truth for drawing and session restore.
- Style/behavior switches must not reset session data:
  - `Colorful` on/off
  - `Ignore Mouse Stops` on/off
  - `Use Multiple Monitors` on/off
- These switches trigger re-render from raw data (preview + export) without confirmation dialogs.
- App starts recording automatically on launch.
- Session persistence:
  - raw data is persisted on real app exit (not on tray hide),
  - timing state is persisted and restored (`total time` + `time period`),
  - raw data is cleared only by explicit `Reset`.
- Storage model:
  - raw data is stored in chunked NDJSON files (`raw_chunks/*.ndjson`) with metadata in `session_state.json`,
  - startup loads chunked storage, with fallback compatibility for legacy inline `raw_samples`.
- Render cache:
  - preview cache and desktop background cache are saved on exit,
  - caches are reused only when render signature matches current monitor/layout context,
  - fallback path is always available (rebuild preview from raw, refresh desktop snapshot when needed).
- Heavy render path:
  - full PNG export is rendered from raw in background worker using `QImage`,
  - preview rebuild is also performed in worker to reduce UI blocking.

### Current Bug Being Fixed
- Symptom:
  - when `Ignore Mouse Stops = true` and switching style (for example B/W -> Colorful), only a central square updates first,
  - then there is a pause,
  - then final full re-render appears,
  - expected progressive preview animation is not visible in some modes (notably with ).

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
    
