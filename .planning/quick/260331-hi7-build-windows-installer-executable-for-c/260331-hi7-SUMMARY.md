---
phase: quick-260331-hi7
plan: 01
subsystem: infra
tags: [pyinstaller, nsis, github-actions, windows, pyside6, installer]

requires: []
provides:
  - PyInstaller spec (onedir, no console, collect_all PySide6) at releases/windows/cell_counter.spec
  - NSIS MUI2 installer script with Start Menu shortcut, uninstaller, Add/Remove Programs entry at releases/windows/installer.nsi
  - GitHub Actions workflow_dispatch pipeline producing CellCounterInstaller.exe artifact at .github/workflows/build-windows.yml
affects: [future-release, deployment]

tech-stack:
  added: [pyinstaller, nsis, pillow (build-time icon conversion), astral-sh/setup-uv@v7, actions/upload-artifact@v4]
  patterns:
    - PyInstaller onedir + NSIS wrapper pattern for PySide6 Windows packaging
    - collect_all('PySide6') in spec to guarantee platforms/qwindows.dll is bundled
    - uv pip install --system in CI so pyinstaller lands on PATH

key-files:
  created:
    - releases/windows/cell_counter.spec
    - releases/windows/installer.nsi
    - .github/workflows/build-windows.yml
  modified: []

key-decisions:
  - "windows-2022 runner chosen over windows-latest — windows-latest now maps to windows-2025 where NSIS is not pre-installed"
  - "collect_all('PySide6') in spec — only reliable way to include platforms/qwindows.dll (avoids qt.qpa.plugin crash)"
  - "onedir mode (not --onefile) — avoids 10-30s startup delay from self-extraction with large PySide6 bundle"
  - "uv pip install --system — ensures pyinstaller binary lands on system PATH (without --system uv uses managed env not on PATH)"
  - "workflow_dispatch only trigger — no automatic builds on push/tag per user constraint"

requirements-completed: []

duration: 8min
completed: 2026-03-31
---

# Quick Task 260331-hi7: Windows Installer Build Summary

**GitHub Actions workflow_dispatch pipeline that bundles the PySide6 cell counter app via PyInstaller onedir and wraps it in an NSIS MUI2 installer — non-technical users receive a double-clickable CellCounterInstaller.exe with Start Menu shortcut and uninstaller.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-31T00:06:39Z
- **Completed:** 2026-03-31T00:14:39Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments

- PyInstaller spec using `collect_all('PySide6')` ensures `platforms/qwindows.dll` is bundled — eliminates the most common PySide6 Windows packaging failure
- NSIS MUI2 script produces professional wizard installer with Program Files installation, Start Menu shortcut, and Add/Remove Programs uninstall entry
- GitHub Actions workflow triggers on manual dispatch only, uses `windows-2022` runner (NSIS pre-installed), installs uv via `astral-sh/setup-uv@v7`, and uploads the installer as a 30-day artifact

## Task Commits

1. **Task 1: PyInstaller spec file** - `8a5c0f6` (feat)
2. **Task 2: NSIS installer script** - `5138385` (feat)
3. **Task 3: GitHub Actions workflow** - `c8d87d0` (feat)

## Files Created

- `releases/windows/cell_counter.spec` — PyInstaller spec; onedir, no console window, `collect_all('PySide6')`, hiddenimports for cv2/numpy/pandas, icon.png embedded
- `releases/windows/installer.nsi` — NSIS MUI2 script; admin elevation, PROGRAMFILES64, Start Menu shortcut, WriteUninstaller, registry entries for Add/Remove Programs
- `.github/workflows/build-windows.yml` — CI workflow; workflow_dispatch, windows-2022, astral-sh/setup-uv@v7, `--system` install, pwsh makensis step, artifact upload 30 days

## Decisions Made

- **windows-2022 over windows-latest:** `windows-latest` now resolves to windows-2025 where NSIS was closed as "not planned" (GitHub runner-images issue #11754). windows-2022 has NSIS 3.10 confirmed.
- **collect_all('PySide6') pattern:** Partial PySide6 collection reliably misses `plugins/platforms/` folder causing qt.qpa.plugin crash at startup. `collect_all` is the documented fix per Qt for Python deployment docs and PyInstaller issue #5414.
- **onedir over --onefile:** PySide6 bundles are 80-150MB; `--onefile` self-extracts to `%TEMP%` on every launch causing 10-30s startup delay. NSIS wraps the entire directory cleanly.
- **uv pip install --system:** Without `--system`, uv installs into a managed environment not on PATH. `pyinstaller` command not found would fail the build silently.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## How to trigger

1. Go to the GitHub repository Actions tab
2. Select "Build Windows Installer" workflow
3. Click "Run workflow" → "Run workflow"
4. Download `CellCounterInstaller-{run_number}` artifact when job completes (~5-10 min)

## Self-Check: PASSED

- `releases/windows/cell_counter.spec` — FOUND
- `releases/windows/installer.nsi` — FOUND
- `.github/workflows/build-windows.yml` — FOUND
- Commit `8a5c0f6` — FOUND
- Commit `5138385` — FOUND
- Commit `c8d87d0` — FOUND
