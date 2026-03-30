---
phase: 03-batch-management
plan: "01"
subsystem: batch-persistence
tags: [batch-manager, file-io, pyside6, dialogs, atomic-write, tdd]
dependency_graph:
  requires: []
  provides: [batch_manager.py, ui/batch_dialogs.py, batch-save-load-ui]
  affects: [ui/main_window.py]
tech_stack:
  added: []
  patterns: [tempfile+os.replace atomic write, RGB/BGR conversion for disk save, pure-Python IO class with no Qt imports]
key_files:
  created:
    - batch_manager.py
    - ui/batch_dialogs.py
    - tests/test_batch_manager.py
    - tests/test_batch_ui.py
  modified:
    - ui/main_window.py
decisions:
  - BatchManager is pure Python with no Qt imports, making unit tests runnable without QApplication
  - annotated_rgb saved as BGR (cv2.imwrite requirement) with explicit cvtColor before write
  - status field computed at load time (not persisted) so missing-file state is always fresh
  - manual_marks normalized from JSON lists to Python tuples on load
  - save_batch always creates new folder; duplicate names get _2/_3 counter suffix
metrics:
  duration_seconds: 258
  completed_date: "2026-03-30"
  tasks_completed: 2
  tasks_total: 2
  files_created: 4
  files_modified: 1
---

# Phase 03 Plan 01: BatchManager + Save/Open Batch UI Summary

**One-liner:** Pure-Python BatchManager with atomic JSON manifest save/load, and Save/Open Batch buttons wired into MainWindow with full state restore.

## What Was Built

### batch_manager.py

New pure-Python module with no Qt imports. Implements:

- `BatchManager.save_batch(name, images, params)` — creates `batches/YYYY-MM-DD_name/` with original image copies, BGR-converted annotated images, and an atomic `manifest.json`
- `BatchManager.load_batch(batch_dir)` — reads manifest and computes `status='ok'/'missing'` per image; normalizes `manual_marks` to tuples
- `BatchManager.list_batches()` — returns sorted metadata list (newest first)
- `BatchManager._atomic_write_manifest(batch_dir, manifest)` — write to `.tmp` then `os.replace()` for crash-safe saves
- `BatchManager._resolve_unique(candidate)` — appends `_2`, `_3` suffix on name collisions

### ui/batch_dialogs.py

New `OpenBatchDialog(QDialog)` with:
- `QListWidget` populated from `BatchManager.list_batches()`
- Each item shows: `name | YYYY-MM-DD | N images`
- `selected_path()` returns the `Path` of the selected batch or `None`
- OK/Cancel via `QDialogButtonBox`

### ui/main_window.py (updated)

- Added `BatchManager` and `OpenBatchDialog` imports at module level
- Added `self._current_batch_dir = None` to state initialization
- Added `Save Batch` and `Open Batch` buttons in left panel (after Clear)
- `_update_batch_buttons()`: enables Save Batch only when `self._images` is non-empty
- `_on_save_batch()`: prompts for name via `QInputDialog`, calls `BatchManager.save_batch()`, updates title
- `_on_open_batch()`: lists batches, shows `OpenBatchDialog`, delegates to `_load_batch_from_path()`
- `_load_batch_from_path()`: clears state, loads manifest, restores images (BGR→RGB), params, annotated images, marks; warns on missing files; updates title

### Tests

- `tests/test_batch_manager.py`: 10 unit tests (all passing, no Qt required)
- `tests/test_batch_ui.py`: 6 integration tests (all passing with qtbot)

## Checkpoint Auto-Approved

Task 3 (human-verify) was auto-approved per `auto_advance: true` configuration. The app is ready for manual verification of the Save/Open Batch flow by following the how-to-verify steps in the plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect test assertion in test_save_converts_rgb_to_bgr**
- **Found during:** Task 1, GREEN phase
- **Issue:** Test asserted `saved_bgr[0,0,0] == 255` (blue channel) but when RGB R=255 is converted to BGR, it maps to BGR channel 2 (R), not channel 0 (B)
- **Fix:** Changed assertion to `saved_bgr[0,0,2] == 255` (correct BGR red channel)
- **Files modified:** tests/test_batch_manager.py
- **Commit:** fa5283a

## Self-Check: PASSED

- batch_manager.py: FOUND
- ui/batch_dialogs.py: FOUND
- tests/test_batch_manager.py: FOUND
- tests/test_batch_ui.py: FOUND
- Commit fa5283a (Task 1): FOUND
- Commit 054cb2a (Task 2): FOUND
