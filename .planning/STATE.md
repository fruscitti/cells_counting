---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: — Fluorescence Cell Counter Web App
status: Milestone complete
last_updated: "2026-03-30T01:27:42.122Z"
progress:
  total_phases: 1
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
---

# Project State

**Project:** Fluorescence Cell Counter — Desktop App + Batch Management
**Milestone:** v2.0
**Branch:** local-ui
**Last updated:** 2026-03-30 — Completed Plan 02-03 (Manual Annotation + Clear + Polish) — Phase 2 COMPLETE

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-29)

**Core value:** Scientists can analyze fluorescence images offline, save named batches, and return to re-examine or modify sessions without a web browser.
**Current focus:** Phase 02 — desktop-gui

## Current Position

Phase: 02
Plan: Not started

Next step: Phase 3 (Batch Management) or run `/gsd:transition`

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 2 | Desktop GUI | ● Complete (3/3 plans done) |
| 3 | Batch Management | ○ Pending |

## Key Decisions Made in Planning

- PySide6 (Qt for Python, LGPL) chosen over tkinter — better image widgets, native look on all platforms
- BGR→RGB conversion + QImage.copy() required when converting numpy arrays to QPixmap (prevents segfault)
- QRunnable + QThreadPool for background analysis — keeps UI responsive
- ScaledImageLabel (QLabel subclass) for image display — simpler than QGraphicsView for v1
- Folder structure + JSON manifest for batch storage — no database dependency
- Atomic save (write temp + os.replace) for manifest — prevents corruption on crash
- Remove-from-manifest-only (no file delete) on image removal — prevents research data loss
- All 9 parameters stored in manifest from day one (including tophat/adaptive params)
- Entry point: `app.py` — `main.py` (Gradio web version) stays untouched

## Decisions from Execution

- Plan 02-01: qtbot required for all QImage/QPixmap tests — QApplication must be active before QImage construction (abort otherwise)
- Plan 02-01: ScaledImageLabel stores _pixmap separately from QLabel.pixmap() to avoid Qt default scaling interference
- Plan 02-02: analysis_core.py isolates pure functions to avoid Gradio module-level side effects when imported by desktop app
- Plan 02-02: AnalysisSignals placed on QObject subclass (not QRunnable) — Qt requires signals on QObject
- Plan 02-02: Workers import analysis_core inside run() to avoid circular imports at module load time
- Plan 02-02: param_panel fixture calls panel.show() so Qt isVisible() correctly reflects child widget visibility (parent chain check)
- Plan 02-03: _redraw_annotated always draws fresh on base annotated_rgb (no mutation of stored state)
- Plan 02-03: _on_clear calls param_panel.reset_defaults() for full parameter reset (CLR-01)
- Plan 02-03: undo_mark_btn enabled/disabled based on marks list length for accurate UI affordance
- Plan 02-03: from analysis_core import draw_manual_marks placed inside method body to avoid circular imports
