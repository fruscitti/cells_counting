---
phase: 05-actions-surface
plan: 01
subsystem: ui
tags: [qaction, menu-bar, toolbar, enable-disable, migration]
dependency_graph:
  requires: [04-layout-foundation]
  provides: [menu-bar, toolbar, action-based-enable-disable]
  affects: [ui/main_window.py]
tech_stack:
  added: [QAction (PySide6.QtGui), QToolBar (PySide6.QtWidgets)]
  patterns: [shared-QAction-instance, triggered.connect, setEnabled-on-action]
key_files:
  created: []
  modified:
    - ui/main_window.py
    - tests/test_main_window.py
    - tests/conftest.py
decisions:
  - QAction.MenuRole.NoRole applied to all 12 custom actions (prevents macOS menu hijacking, D-04)
  - window fixture added to conftest.py as alias for main_window (cleaner Phase 5 test names)
  - _update_batch_buttons renamed to _update_action_states per D-13
  - _disable_batch_buttons_during_analysis renamed to _disable_actions_during_analysis
metrics:
  duration: "~5 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_modified: 3
---

# Phase 05 Plan 01: Actions Surface Summary

**One-liner:** QAction-based menu bar (File/Batch/Analysis) and locked toolbar (Analyze/Auto-Optimize/Undo Mark/Clear All) wired via 12 shared QAction instances, with all ~25 enable/disable sites migrated from hidden QPushButtons to actions.

## What Was Built

### Task 1: QActions, menu bar, toolbar
- `_build_actions()` creates 12 QAction instances stored as `self.act_*` with `QAction.MenuRole.NoRole` on each
- `_build_menu_bar()` adds File (5 items + separator), Batch (3 items), and Analysis (4 items) menus
- `_build_toolbar()` adds a locked, non-movable, text-only toolbar with 4 analysis actions
- Same QAction instance added to both menu and toolbar (single enable/disable source of truth — TOOL-03)
- Action `triggered.connect()` calls added to `_connect_signals()` for all 12 actions
- 8 new tests added and all pass (GREEN)

### Task 2: Migration and cleanup
- All QPushButton definitions for action buttons removed from `_build_ui()` (D-14)
- `setVisible(False)` loop removed (buttons no longer exist)
- All old `.clicked.connect()` calls removed from `_connect_signals()`
- All ~25 `*_btn.setEnabled(...)` call sites migrated to `act_*.setEnabled(...)` across:
  - `load_images()`, `_on_image_selected()`, `_on_annotated_click()`, `_on_undo_mark()`
  - `_on_clear()`, `_on_analyze()`, `_on_analysis_finished()`, `_on_auto_optimize()`
  - `_load_batch_from_path()`, `_on_add_images()`, `_on_re_analyze()`, `_on_reanalyze_finished()`
- `_update_batch_buttons` renamed to `_update_action_states` (D-13)
- `_disable_batch_buttons_during_analysis` renamed to `_disable_actions_during_analysis`

## Verification

All verification criteria from plan:

| Check | Result |
|-------|--------|
| All 20 tests pass (excl. pre-existing test_total_count failure) | PASS |
| `grep -c "act_.*setEnabled" ui/main_window.py` | 41 |
| `grep -c "_btn\.setEnabled" ui/main_window.py` | 0 |
| `grep "MenuRole.NoRole" ui/main_window.py \| wc -l` | 12 |
| `grep "setMovable(False)" ui/main_window.py` | present |
| `grep "_update_batch_buttons" ui/main_window.py` | 0 results |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing fixture] Added `window` fixture to conftest.py**
- **Found during:** Task 1 RED phase
- **Issue:** Tests used `window` fixture but only `main_window` existed in conftest.py
- **Fix:** Added `window` fixture as an alias to `main_window` in `tests/conftest.py`
- **Files modified:** `tests/conftest.py`
- **Commit:** 4334658

### Pre-existing Issue Noted (Out of Scope)

`test_total_count` was already failing before this plan due to wrong `process_image` signature (expects 2 return values but function returns more). This is a pre-existing test issue unrelated to Phase 5 work. Deferred.

## Known Stubs

None — all actions are wired to existing slot methods via `triggered.connect()`. No placeholder data.

## Self-Check: PASSED
