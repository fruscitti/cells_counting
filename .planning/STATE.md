---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: — Fluorescence Cell Counter Web App
status: verifying
last_updated: "2026-03-30T23:12:30.046Z"
last_activity: 2026-03-30
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 8
  completed_plans: 8
---

# Project State

**Project:** Fluorescence Cell Counter — Desktop App + Batch Management
**Milestone:** v3.0 — UI Redesign
**Branch:** local-ui
**Last updated:** 2026-03-30 — Roadmap created for v3.0

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-30)

**Core value:** Scientists can analyze fluorescence images offline, save named batches, and return to re-examine or modify sessions without a web browser.
**Current focus:** Phase 05 — actions-surface

## Current Position

Phase: 05
Plan: Not started
Status: Phase 05 complete — ready for verification
Last activity: 2026-03-30

```
v3.0 Progress: [████░░░░░░] ~33% (1/3 phases complete)
```

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 2 | Desktop GUI | ● Complete (3/3 plans done) |
| 3 | Batch Management | ● Complete (2/2 plans done) |
| 4 | Layout Foundation | ● Complete (2/2 plans done) |
| 5 | Actions Surface | ● Complete (1/1 plans done) |
| 6 | Cleanup and Shortcuts | ○ Not started |

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

- Plan 05-01: QAction.MenuRole.NoRole applied to all 12 custom actions — prevents macOS menu role hijacking (D-04)
- Plan 05-01: _update_batch_buttons renamed to _update_action_states; _disable_batch_buttons_during_analysis renamed to _disable_actions_during_analysis (D-13)
- Plan 05-01: window fixture added to conftest.py as alias for main_window — cleaner Phase 5 test names
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
- Plan 03-01: BatchManager is pure Python with no Qt imports for unit testability without QApplication
- Plan 03-01: annotated_rgb saved as BGR via cvtColor before cv2.imwrite (RGB/BGR pitfall from RESEARCH)
- Plan 03-01: manifest status field computed at load time, not persisted — always reflects current disk state
- Plan 03-01: manual_marks normalized from JSON lists to Python tuples on load in load_batch()
- Plan 03-02: marks backup stored in self._marks_backup dict, restored per-image in _on_reanalyze_image_done
- Plan 03-02: _is_analyzing flag guards all batch mutation buttons (prevents Pitfall 3: manifest written mid-analysis)
- Plan 03-02: status field stripped via img.pop("status", None) before every _atomic_write_manifest in new mutation methods
- Plan 03-02: test_reanalyze_preserves_marks uses qtbot.waitUntil on _is_analyzing flag (Python method patching doesn't intercept Qt slot dispatch)

## Research Findings for v3.0 (HIGH confidence)

- QAction is in PySide6.QtGui — NOT PySide6.QtWidgets (changed from Qt5; wrong import = ImportError at startup)
- QAction is a three-for-one: one instance wires menu item + toolbar button + keyboard shortcut simultaneously
- QMainWindow.menuBar() and .statusBar() are auto-created on first call — no manual instantiation needed
- Outer QSplitter(Qt.Horizontal) wraps existing left_scroll + right_splitter; replaces setFixedWidth(298)
- setMinimumWidth(220) on the sidebar widget prevents collapse to zero
- addPermanentWidget() for always-visible status labels; showMessage() only for ephemeral progress/errors
- setMovable(False) + PreventContextMenu on toolbar — prevents accidental hide
- Set QAction.MenuRole.NoRole on all custom actions to prevent macOS menu role hijacking
- QSplitter.restoreState() must be called after window.show() (or via QTimer.singleShot) — not during __init__
- After button-to-action rename: grep for old attribute names, expect zero results before proceeding
- Delete key for image removal: wire via keyPressEvent on image_list widget, not global shortcut

## Accumulated Context

### Key Todos for Phase 4

- Check main_window.py for existing QSettings usage before implementing splitter state persistence
- Decide whether progress_bar stays in sidebar or moves to status bar (visual preference call)

### Blockers

None.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260330-eto | Fix batch management: cell counts on open, save in-place, total row | 2026-03-30 | 73e6ff8 | [260330-eto-fix-batch-management-cell-counts-not-res](.planning/quick/260330-eto-fix-batch-management-cell-counts-not-res/) |
| 260330-f91 | Add mouse-wheel zoom + QScrollArea pan to both image panels | 2026-03-30 | 8137070 | [260330-f91-add-manual-cell-marking-zoom-images-mark](.planning/quick/260330-f91-add-manual-cell-marking-zoom-images-mark/) |
| 260330-i45 | Add ability to unmark detected cells by clicking | 2026-03-30 | 2d9efde | [260330-i45-add-ability-to-unmark-detected-cells-by-](.planning/quick/260330-i45-add-ability-to-unmark-detected-cells-by-/) |
