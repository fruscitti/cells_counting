---
phase: 2
plan: 2
subsystem: desktop-gui
tags: [parameter-controls, analysis-engine, workers, qrunnable, threading]
dependency_graph:
  requires: [02-01]
  provides: [analysis-core, param-panel, analysis-worker, optimize-worker]
  affects: [ui/main_window.py, workers/]
tech_stack:
  added: [PySide6.QtCore.QRunnable, PySide6.QtCore.QThreadPool, analysis_core.py]
  patterns: [WorkerSignals on QObject (not QRunnable), import-in-run to avoid Gradio side effects]
key_files:
  created:
    - analysis_core.py
    - ui/param_panel.py
    - workers/__init__.py
    - workers/analysis_worker.py
    - workers/optimize_worker.py
  modified:
    - ui/main_window.py
    - tests/test_param_panel.py
    - tests/test_analysis_worker.py
decisions:
  - "analysis_core.py isolates pure functions — importing from main.py executes module-level Gradio setup (gr.Blocks, middleware), crashing desktop app"
  - "OddSpinBox.stepBy enforces odd on step; get_params() applies +1 correction as fallback for direct setValue calls"
  - "param_panel fixture calls panel.show() so Qt isVisible() correctly reflects child widget visibility (parent chain check)"
  - "AnalysisSignals placed on QObject subclass (not QRunnable) per Qt requirement — signals on non-QObject are not supported"
  - "Workers import analysis_core inside run() method to avoid circular imports at module load time"
metrics:
  duration: "3 minutes 30 seconds"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_changed: 8
---

# Phase 2 Plan 2: Parameter Controls + Analysis Engine Summary

**One-liner:** Full 9-parameter control panel with OddSpinBox, QRunnable-based analysis/optimize workers, and wired Analyze + Auto-Optimize buttons with progress tracking and results table population.

## Tasks Completed

| Task | Name | Commit |
|------|------|--------|
| 02-01 | Extract analysis_core.py + build ParamPanel with all 9 controls + value labels | 67ada60 |
| 02-02 | Build analysis worker, optimize worker, wire Analyze + Auto-Optimize + results table | c996c30 |

## What Was Built

### analysis_core.py
Pure analysis functions extracted from `main.py` with no UI or Gradio dependencies. Contains `split_clumped_cells`, `process_image`, `optimize_parameters`, and `draw_manual_marks`. Verified: `python -c "from analysis_core import process_image, optimize_parameters, draw_manual_marks; print('OK')"` prints OK without triggering Gradio setup.

### ui/param_panel.py
`ParamPanel(QWidget)` with all 9 controls:
- `brightness_slider` (0-255, default 120) with `brightness_value` label
- `min_area_slider` (1-500, default 25) with `min_area_value` label
- `blur_spinbox` (`OddSpinBox`, 1-31, default 9, step 2, enforces odd)
- `max_area_spinbox` (50-5000, default 500) with `max_area_value` label
- `cleaning_checkbox` (default checked)
- `tophat_checkbox` with `tophat_container` (show/hide via toggle)
- `tophat_kernel_slider` (10-200, default 50)
- `adaptive_block_spinbox` (`OddSpinBox`, 3-199, default 99)
- `adaptive_c_slider` (-50 to 50, default -5)

Methods: `get_params() -> dict`, `set_params(partial_dict)`, `reset_defaults()`.

### workers/analysis_worker.py
`AnalysisSignals(QObject)` + `AnalysisWorker(QRunnable)`. Signals: `image_done(str, object, int)`, `progress(int, int)`, `error(str, str)`, `finished`. Imports `process_image` inside `run()` to avoid module-level Gradio side effects.

### workers/optimize_worker.py
`OptimizeSignals(QObject)` + `OptimizeWorker(QRunnable)`. Signals: `result(int, int, int, int)`, `error(str)`, `finished`. Imports `optimize_parameters` inside `run()`.

### ui/main_window.py changes
- `ParamPanel` wired into left panel (replacing `param_container` placeholder)
- `QThreadPool` import added
- `_on_analyze`: disables buttons, shows progress bar, starts `AnalysisWorker`
- `_on_image_done`: stores annotated image + count, updates results table + display
- `_on_image_error`: marks count=0 with warning text in results table
- `_on_progress`: updates progress bar + status label
- `_on_analysis_finished`: re-enables buttons, hides progress bar
- `_on_auto_optimize`: starts `OptimizeWorker` on current image
- `_on_optimize_result`: partial `set_params` with 3-key dict (brightness, min_area, blur)
- `_update_results_row`: find-or-insert row in results table with error support

## Test Results

```
23 passed, 5 skipped in 0.33s
```

- `tests/test_param_panel.py`: 10 tests (brightness range, min area, odd enforcement, max area, cleaning default, tophat visibility, value labels, get_params keys, set_params partial, reset defaults)
- `tests/test_analysis_worker.py`: 3 tests (background thread, progress emitted, error signal)
- Previously passing Plan 01 tests remain passing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed isVisible() returning False in test_tophat_visibility**
- **Found during:** Task 02-01, test run
- **Issue:** `isVisible()` in Qt checks the entire parent chain. The `ParamPanel` widget was created but not shown, so children's `isVisible()` returned False even after `setChecked(True)` + `setVisible(True)`.
- **Fix:** Added `panel.show()` to the `param_panel` pytest fixture so visibility is correctly reported.
- **Files modified:** `tests/test_param_panel.py`
- **Commit:** 67ada60

## Known Stubs

None — all 9 parameter controls are fully wired to `get_params()`, analysis runs via real `process_image()`, results table populates with actual cell counts.

## Self-Check: PASSED
