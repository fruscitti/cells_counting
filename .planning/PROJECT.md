# Fluorescence Cell Counter — Desktop App

## What This Is

A cross-platform desktop GUI application for fluorescence microscopy cell counting. It provides the same image analysis pipeline as the existing Gradio web app (green-channel extraction, threshold/blur/cleaning parameters, watershed splitting, auto-optimize, click-to-count) but packaged as a native desktop window that runs on Windows, macOS, and Linux with no browser required. A batch management system lets users save, reopen, and modify named analysis sessions.

## Core Value

Scientists can analyze fluorescence images offline, save their work as named batches, and come back to re-examine or add/remove images — all without a running web server.

## Requirements

### Validated

- ✓ Green-channel cell detection pipeline (threshold, blur, cleaning, min area) — existing
- ✓ Watershed splitting for clumped cells (MAX_CELL_AREA slider) — existing
- ✓ Auto-parameter optimization via grid search — existing
- ✓ Manual click-to-count annotation with undo — existing
- ✓ Batch image processing (multiple files at once) — existing
- ✓ Side-by-side original/annotated image display — existing
- ✓ Results table (filename + cell count) — existing
- ✓ Clear/reset functionality — existing

## Current Milestone: v3.0 UI Redesign

**Goal:** Replace the cramped left-panel button stack with a standard desktop layout — menu bar, toolbar, and a resizable sidebar that gives the image list and parameter sliders room to breathe.

**Target features:**
- Menu bar: File / Batch / Analysis menus (all current action buttons moved in)
- Toolbar: Analyze, Auto-Optimize, Undo Mark, Clear — persistent one-click access
- Left sidebar resizable via splitter (not fixed width)
- Keyboard shortcuts (Ctrl+O, Ctrl+S, Delete to remove image, etc.)
- Status bar at the bottom (batch name, image count, cell count)

### Active

- [ ] Menu bar with File, Batch, and Analysis menus
- [ ] Toolbar with primary analysis actions
- [ ] Keyboard shortcuts for common actions

### Validated in Phase 4

- ✓ Resizable left sidebar via QSplitter (replaces fixed width) — Validated in Phase 4: layout-foundation
- ✓ Action buttons hidden from sidebar panel — Validated in Phase 4: layout-foundation
- ✓ Persistent status bar (batch name, image count, cell count) — Validated in Phase 4: layout-foundation

### Validated in Phase 3

- ✓ Save current analysis as a named batch (folder structure + JSON manifest) — Validated in Phase 3: batch-management
- ✓ Open/browse existing batches from a batch list — Validated in Phase 3: batch-management
- ✓ Re-analyze a batch with new parameters, preserving manual marks — Validated in Phase 3: batch-management
- ✓ Add images to an existing batch — Validated in Phase 3: batch-management
- ✓ Remove images from an existing batch (manifest only, no file delete) — Validated in Phase 3: batch-management
- ✓ Export batch results to CSV — Validated in Phase 3: batch-management

### Validated in Phase 2

- ✓ Desktop window GUI (PySide6/Qt) runs on Windows, macOS, Linux — Validated in Phase 2: desktop-gui
- ✓ All parameter sliders (brightness, min area, blur, max area, top-hat) in desktop UI — Validated in Phase 2: desktop-gui
- ✓ Use cleaning checkbox in desktop UI — Validated in Phase 2: desktop-gui
- ✓ Open images via file dialog (single or multi-select) — Validated in Phase 2: desktop-gui
- ✓ Analyze and display original + annotated image pairs side by side — Validated in Phase 2: desktop-gui
- ✓ Background analysis thread (UI stays responsive) — Validated in Phase 2: desktop-gui
- ✓ Results table with filename and cell count — Validated in Phase 2: desktop-gui
- ✓ Manual click-to-count annotation on annotated image with undo — Validated in Phase 2: desktop-gui
- ✓ Clear/reset button — Validated in Phase 2: desktop-gui

### Out of Scope

- Web server / browser-based UI — keeping Gradio version intact in main branch; this work lives in a separate branch
- SQLite database — folder structure + JSON manifest is simpler and portable
- Cloud sync or remote storage — local-only
- Real-time preview as sliders move — too slow for large images; analyze on demand

## Context

- Existing implementation: `main.py` (Gradio 6.9.0 + FastAPI + Uvicorn, port 7860)
- Processing core in `process_image()` and `run_analysis()` — will be reused as-is
- Stack: Python 3.12, uv package manager, OpenCV 4.13, NumPy, Pandas
- New dependency: PySide6 (Qt for Python) — best cross-platform desktop GUI for Python
- All work happens in a new git branch; `main` branch stays untouched
- Batch storage: `batches/` folder at project root, each batch = subfolder with `manifest.json` + copied images

## Constraints

- **Tech Stack**: Python only for backend/logic — no Electron, no JS
- **GUI Framework**: PySide6 — Qt is the gold standard for cross-platform desktop Python apps
- **Storage**: Folder structure + JSON — no database dependency
- **Branch**: All changes in `local-ui` branch — main branch must remain working
- **Package Manager**: `uv pip install` for new dependencies

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| PySide6 over tkinter | Qt has native image widgets, proper sliders, and looks modern on all platforms | ✓ Confirmed — Phase 2 |
| Reuse existing processing core | process_image() is well-tested; no need to rewrite | ✓ Confirmed — analysis_core.py extracts functions cleanly |
| Folder structure over SQLite | Zero dependencies, human-readable, portable across OS | ✓ Confirmed — Phase 3 |
| Separate branch from main | Keeps Gradio web version stable and shippable while desktop is built | ✓ Confirmed — local-ui branch |
| analysis_core.py instead of importing main.py | main.py has module-level Gradio setup code that crashes desktop app on import | ✓ Confirmed — Phase 2 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-30 after Phase 4 complete — resizable sidebar, hidden buttons, persistent status bar all verified green*
