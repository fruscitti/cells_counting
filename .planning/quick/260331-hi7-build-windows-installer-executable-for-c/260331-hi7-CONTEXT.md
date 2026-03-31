---
name: 260331-hi7 Context
description: Decisions for Windows installer build pipeline via GitHub Actions
type: project
---

# Quick Task 260331-hi7: Build Windows Installer for Cell Counter App - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Task Boundary

Build a Windows installer (.exe) for the PySide6 Qt desktop app (`app.py`) using GitHub Actions CI.
Add a `releases/` folder with workflow config. Installer should be usable by non-tech users.
The app is a Qt desktop GUI — no browser, no server.

</domain>

<decisions>
## Implementation Decisions

### Installer Type
- NSIS installer wizard: produces a professional `.exe` installer that puts the app in Program Files and adds a Start Menu entry
- PyInstaller used to bundle Python + PySide6 + dependencies into a single directory first, then NSIS wraps it

### App Launcher
- App is a Qt desktop GUI (PySide6, entry point: `app.py`)
- Installed app opens directly from Start Menu shortcut — no browser, no server
- No console window for end users (use `--windowed` / `--noconsole` in PyInstaller)

### Build Trigger
- GitHub Actions workflow triggered manually only (`workflow_dispatch`)
- No automatic builds on push or tags
- Artifacts uploaded to GitHub Actions artifact storage (or optionally GitHub Release)

### Claude's Discretion
- Choice of NSIS script structure and installer UI (use default NSIS Modern UI)
- Whether to include an uninstaller (standard practice — include it)
- PyInstaller spec file location (`releases/windows/` or repo root)
- Whether to use `--onefile` or `--onedir` (onedir recommended for PySide6 due to size/speed)

</decisions>

<specifics>
## Specific Ideas

- Entry point: `app.py`
- App icon: `icon.png` exists in repo root — use for installer and .exe
- Existing files to be aware of: `INSTALL_WINDOWS.md`, `run.bat`, `setup.bat` — may already have manual install notes
- `releases/` folder should contain: workflow YAML and NSIS script at minimum

</specifics>

<canonical_refs>
## Canonical References

- PyInstaller docs for PySide6 bundling
- NSIS Modern UI documentation
- GitHub Actions `workflow_dispatch` trigger

</canonical_refs>
