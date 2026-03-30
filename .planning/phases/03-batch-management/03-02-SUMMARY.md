---
phase: 03-batch-management
plan: 02
subsystem: ui
tags: [pyside6, batch-management, pandas, csv-export, qt-buttons]

# Dependency graph
requires:
  - phase: 03-batch-management/03-01
    provides: BatchManager with save_batch/load_batch/list_batches, Save/Open Batch UI buttons

provides:
  - BatchManager.add_images: copies files into batch folder, handles duplicates with suffix
  - BatchManager.remove_image: removes manifest entry only (no file delete)
  - BatchManager.update_manifest: rewrites manifest with new params and image data
  - BatchManager.export_csv: pandas DataFrame CSV with filename/total_count/algo_count/manual_count
  - Add Images button wired to _on_add_images (file dialog + copy + list update)
  - Remove Image button wired to _on_remove_image (manifest only, file preserved)
  - Re-Analyze button wired to _on_re_analyze (AnalysisWorker + marks backup/restore)
  - Export CSV button wired to _on_export_csv (save file dialog)
  - _is_analyzing flag + _disable_batch_buttons_during_analysis (Pitfall 3 prevention)
  - 8 new BatchManager unit tests + 5 new UI tests

affects: [future batch editing phases, CSV data consumers]

# Tech tracking
tech-stack:
  added: [shutil (for file copying in add_images)]
  patterns:
    - marks backup/restore pattern for re-analyze (back up before worker, restore in image_done signal)
    - _is_analyzing flag to guard all mutation buttons during analysis
    - status field stripped before writing manifest (computed-only field never persisted)

key-files:
  created:
    - (no new files)
  modified:
    - batch_manager.py
    - ui/main_window.py
    - tests/test_batch_manager.py
    - tests/test_batch_ui.py

key-decisions:
  - "marks backup stored in self._marks_backup dict keyed by filename, restored per-image in _on_reanalyze_image_done"
  - "_is_analyzing flag set at start of both _on_analyze and _on_re_analyze, cleared in their respective finished handlers"
  - "status field stripped via img.pop('status', None) before _atomic_write_manifest in add_images and remove_image"
  - "test_reanalyze_preserves_marks uses qtbot.waitUntil on _is_analyzing flag instead of signal patching"

patterns-established:
  - "Pattern: Re-analyze with marks preservation — back up marks before worker, restore in image_done, update manifest in finished"
  - "Pattern: Batch mutation guard — _is_analyzing flag + _disable_batch_buttons_during_analysis prevents concurrent writes"

requirements-completed:
  - BMGR-04
  - BMGR-05
  - BMGR-06
  - BMGR-07

# Metrics
duration: 3min
completed: 2026-03-29
---

# Phase 03 Plan 02: Batch Management Mutations Summary

**BatchManager extended with add/remove/update/export methods; 4 mutation buttons wired in MainWindow with marks-preserving re-analyze and _is_analyzing guard**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-29T18:36:57Z
- **Completed:** 2026-03-29T18:40:00Z
- **Tasks:** 2 (+ 1 checkpoint auto-approved)
- **Files modified:** 4

## Accomplishments
- Added `add_images`, `remove_image`, `update_manifest`, `export_csv` class methods to BatchManager with 8 covering unit tests
- Wired Add Images, Remove Image, Re-Analyze, Export CSV buttons in MainWindow with proper state management
- Re-Analyze correctly preserves manual marks via backup/restore pattern across AnalysisWorker lifecycle
- All batch mutation buttons disabled when no batch is open or analysis is running (Pitfall 3 prevention)

## Task Commits

1. **Task 1: add_images, remove_image, update_manifest, export_csv + tests** - `e655e45` (feat)
2. **Task 2: Wire 4 buttons + state management + UI tests** - `d810484` (feat)

## Files Created/Modified
- `batch_manager.py` - Added shutil import + 4 new class methods (add_images, remove_image, update_manifest, export_csv)
- `ui/main_window.py` - Added 4 buttons, 4 slots, re-analyze helpers, updated _update_batch_buttons with _is_analyzing guard
- `tests/test_batch_manager.py` - 8 new unit tests for all new BatchManager methods
- `tests/test_batch_ui.py` - 5 new tests: 4 button-disabled checks + test_reanalyze_preserves_marks

## Decisions Made
- `self._marks_backup` dict is keyed by filename and populated in `_on_re_analyze` before worker starts; restored per-image in `_on_reanalyze_image_done`. This ensures marks survive even if worker emits signals out of order.
- `_is_analyzing` flag is set True at start of both `_on_analyze` and `_on_re_analyze`, cleared in their respective `_on_analysis_finished` / `_on_reanalyze_finished` handlers.
- `status` field is stripped via `img.pop("status", None)` before every `_atomic_write_manifest` call in the new methods, because `load_batch` adds a computed-only `status` key that must never be persisted.
- `test_reanalyze_preserves_marks` uses `qtbot.waitUntil(lambda: not w._is_analyzing)` instead of monkey-patching the finished method, which doesn't work with Qt bound method dispatch.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `test_reanalyze_preserves_marks` initially used Python method patching (`w._on_reanalyze_finished = patched_fn`) which does not intercept Qt slot dispatch — the signal still calls the original C++ binding. Fixed by polling `_is_analyzing` flag with `qtbot.waitUntil`.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 batch mutation operations are working and tested
- Phase 3 is complete — both plans done (03-01 Save/Open Batch + 03-02 Add/Remove/Re-Analyze/Export)
- Ready for `/gsd:verify-work` or next milestone

---
*Phase: 03-batch-management*
*Completed: 2026-03-29*
