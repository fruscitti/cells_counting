# Quick Task 260331-hi7: Windows Installer Build — Research

**Researched:** 2026-03-31
**Domain:** PyInstaller + NSIS + GitHub Actions (Windows)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- NSIS installer wizard wrapping PyInstaller onedir output
- Entry point: `app.py`
- No console window (`--windowed` / `--noconsole`)
- `workflow_dispatch` trigger only (no push/tag triggers)
- Artifacts uploaded to GitHub Actions artifact storage

### Claude's Discretion
- NSIS script structure and MUI2 vs plain wizard style
- Whether to include uninstaller (standard practice — include it)
- PyInstaller spec file location (`releases/windows/` recommended)
- `--onedir` vs `--onefile` (onedir recommended for PySide6)

### Deferred Ideas (OUT OF SCOPE)
- Auto-build on push or release tag
- Code signing
</user_constraints>

---

## Summary

Bundling a PySide6 app with PyInstaller on Windows is well-supported but has one critical pitfall: the `qwindows.dll` platform plugin is frequently not found at runtime unless the `platforms/` folder is explicitly included. Using `--onedir` avoids this by keeping the folder structure intact. NSIS is pre-installed on `windows-2022` runners (3.10); `windows-latest` now maps to windows-2025 where NSIS is NOT included — use `windows-2022` explicitly. uv is not pre-installed on any runner; use `astral-sh/setup-uv` action before any `uv pip install` calls.

**Primary recommendation:** Use `windows-2022` runner, `astral-sh/setup-uv` for dependency install, PyInstaller `--onedir` with a spec file, and NSIS MUI2 script to wrap the dist folder.

---

## Standard Stack

| Tool | Version | Purpose |
|------|---------|---------|
| PyInstaller | 6.19.0 | Bundle Python + PySide6 into dist folder |
| NSIS | 3.10 (pre-installed on windows-2022) | Build `.exe` installer wizard |
| astral-sh/setup-uv | v7 | Install uv on the Actions runner |
| Pillow | latest | Auto-convert `icon.png` to `.ico` at PyInstaller build time |

**Installation in CI:**
```yaml
- uses: astral-sh/setup-uv@v7
- run: uv pip install pyinstaller pillow PySide6 opencv-python pandas numpy
```

---

## Architecture Patterns

### Recommended File Layout
```
releases/
├── windows/
│   ├── cell_counter.spec       # PyInstaller spec
│   └── installer.nsi           # NSIS script
.github/
└── workflows/
    └── build-windows.yml       # workflow_dispatch CI
```

### PyInstaller Spec File Pattern

```python
# releases/windows/cell_counter.spec
# Source: PyInstaller docs + pythonguis.com PySide6 tutorial
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# Collect all PySide6 plugin data (includes platforms/ folder)
tmp_ret = collect_all('PySide6')
datas   += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# OpenCV and NumPy hidden imports
hiddenimports += ['cv2', 'numpy', 'pandas']

a = Analysis(
    ['../../app.py'],
    pathex=['../..'],
    binaries=binaries,
    datas=datas + [('../../icon.png', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CellCounter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,        # no console window
    icon='../../icon.png',  # Pillow auto-converts to .ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CellCounter',
)
```

**Run from repo root:**
```bash
pyinstaller releases/windows/cell_counter.spec --distpath releases/dist --workpath releases/build
```

### NSIS MUI2 Script Pattern

```nsis
; releases/windows/installer.nsi
; Source: NSIS docs (nsis.sourceforge.io)

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define APPNAME     "Cell Counter"
!define APPVERSION  "1.0.0"
!define PUBLISHER   "Your Lab Name"
!define INSTALL_DIR "$PROGRAMFILES64\CellCounter"
!define DIST_DIR    "..\..\releases\dist\CellCounter"

Name "${APPNAME}"
OutFile "..\..\releases\CellCounterInstaller.exe"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel admin

; MUI Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "${DIST_DIR}\*.*"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" \
        "$INSTDIR\CellCounter.exe" "" "$INSTDIR\CellCounter.exe" 0

    ; Uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Add/Remove Programs registry entry
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "DisplayName" "${APPNAME}"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "Publisher" "${PUBLISHER}"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    RMDir  "$SMPROGRAMS\${APPNAME}"
    DeleteRegKey HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
```

### GitHub Actions Workflow Pattern

```yaml
# .github/workflows/build-windows.yml
name: Build Windows Installer

on:
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-2022    # CRITICAL: NOT windows-latest (= 2025, no NSIS)

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v7  # uv is NOT pre-installed on runners

      - name: Install Python dependencies
        run: uv pip install --system pyinstaller pillow PySide6 opencv-python pandas numpy

      - name: Build with PyInstaller
        run: pyinstaller releases/windows/cell_counter.spec --distpath releases/dist --workpath releases/build

      - name: Build NSIS installer
        run: |
          cd releases/windows
          & "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
        shell: pwsh

      - name: Upload installer artifact
        uses: actions/upload-artifact@v4
        with:
          name: CellCounterInstaller-${{ github.run_number }}
          path: releases/CellCounterInstaller.exe
          retention-days: 30
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Collecting PySide6 Qt plugins | Manual DLL copying | `collect_all('PySide6')` in spec file |
| Icon conversion PNG → ICO | Custom conversion script | Pillow auto-conversion via PyInstaller |
| Installer wizard UI | Custom NSIS code | `!include "MUI2.nsh"` |
| uv on CI runner | Shell install scripts | `astral-sh/setup-uv@v7` action |

---

## Common Pitfalls

### Pitfall 1: Missing `qwindows.dll` platform plugin
**What goes wrong:** App launches, immediately crashes: "qt.qpa.plugin: Could not find the Qt platform plugin 'windows' in ''"
**Why it happens:** PyInstaller misses the `PySide6/plugins/platforms/` folder in partial collections. More common with PySide6 6.3+ due to DLL layout changes.
**How to avoid:** Use `collect_all('PySide6')` in the spec file — this collects the entire PySide6 package including the `platforms/` folder. `--onedir` helps too, since the folder structure stays intact vs `--onefile`.
**Warning signs:** Error appears at startup before any window is shown.

### Pitfall 2: `windows-latest` maps to windows-2025 (no NSIS)
**What goes wrong:** `makensis.exe` not found, workflow fails.
**Why it happens:** As of 2025, `windows-latest` resolves to windows-2025, and NSIS was not added to that image (issue #11754 was closed as "not planned").
**How to avoid:** Use `runs-on: windows-2022` explicitly. NSIS 3.10 is confirmed pre-installed there.

### Pitfall 3: uv not pre-installed on runners
**What goes wrong:** `uv: command not found` in CI.
**Why it happens:** uv is not part of the default runner image.
**How to avoid:** Add `- uses: astral-sh/setup-uv@v7` as the first step after checkout.

### Pitfall 4: `--onefile` makes startup very slow with PySide6
**What goes wrong:** App takes 10-30 seconds to start (extraction on every launch).
**Why it happens:** `--onefile` bundles everything into a single exe that self-extracts to `%TEMP%` at launch. PySide6 bundles are large (~80-150 MB).
**How to avoid:** Use `--onedir` (default). NSIS wraps the whole directory anyway.

### Pitfall 5: Icon must be `.ico` for Windows exe
**What goes wrong:** `--icon icon.png` silently uses a default icon or errors without Pillow.
**Why it happens:** Windows requires `.ico` format for executable icons.
**How to avoid:** Install Pillow in the build environment — PyInstaller will auto-convert. Alternatively pre-convert `icon.png` to `icon.ico` and commit it.

### Pitfall 6: `uv pip install --system` vs venv activation
**What goes wrong:** `pyinstaller` command not found after `uv pip install pyinstaller`.
**Why it happens:** Without `--system`, uv installs into a managed environment not on PATH.
**How to avoid:** Use `uv pip install --system ...` or set env var `UV_SYSTEM_PYTHON: 1` at the job level.

---

## Project-Specific Notes

- **Entry point:** `app.py` — standard `if __name__ == "__main__": main()` pattern; PyInstaller will detect it cleanly.
- **Icon:** `icon.png` exists at repo root. Add Pillow to build deps; PyInstaller handles conversion.
- **Dependencies:** PySide6 6.11.0, opencv-python 4.13.0, numpy 2.4.3, pandas 3.0.1. No `requirements.txt` or `pyproject.toml` in the project root — CI must install each explicitly.
- **No `main.py` conflict:** `main.py` is the Gradio web version. Entry point is `app.py` — spec file must reference `app.py`, not `main.py`.
- **Windows HighDPI:** `app.py` already handles `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` on win32 — no changes needed.
- **`releases/` folder:** Does not exist yet — Wave 0 must create it.

---

## Environment Availability

| Dependency | Available on windows-2022 | Version | Notes |
|------------|--------------------------|---------|-------|
| NSIS | Yes | 3.10 | At `C:\Program Files (x86)\NSIS\makensis.exe` |
| Python | Yes | 3.12 | Via setup-python or uv |
| uv | No (not pre-installed) | — | Requires `astral-sh/setup-uv@v7` |
| PyInstaller | No (install in CI) | 6.19.0 | `uv pip install pyinstaller` |
| Pillow | No (install in CI) | latest | Needed for PNG→ICO conversion |

---

## Sources

### Primary (HIGH confidence)
- [Qt for Python deployment with PyInstaller](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html) — official Qt docs
- [astral-sh/setup-uv GitHub Action](https://docs.astral.sh/uv/guides/integration/github/) — official uv docs
- [NSIS on windows-2025 — closed as not planned (issue #11754)](https://github.com/actions/runner-images/issues/11754) — GitHub runner-images tracker
- [NSIS on windows-2022 — version 3.10 confirmed](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md) — GitHub runner-images

### Secondary (MEDIUM confidence)
- [Packaging PySide6 with PyInstaller for Windows — pythonguis.com](https://www.pythonguis.com/tutorials/packaging-pyside6-applications-windows-pyinstaller-installforge/) — `collect_all` pattern, spec file structure
- [PyInstaller issue #5414 — PySide6 platform plugin](https://github.com/pyinstaller/pyinstaller/issues/5414) — qwindows.dll pitfall confirmation
- [NSIS simple installer template](https://nsis.sourceforge.io/A_simple_installer_with_start_menu_shortcut_and_uninstaller) — NSIS wiki

**Research date:** 2026-03-31
**Valid until:** 2026-06-30 (stable tooling; NSIS runner availability may change)
