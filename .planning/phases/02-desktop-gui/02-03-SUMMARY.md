---
phase: 02-desktop-gui
plan: 03
subsystem: ui
tags: [pyside6, qt, opencv, click-to-count, manual-annotation, coordinate-mapping]

# Dependency graph
requires:
  - phase: 02-desktop-gui/02-01
    provides: ScaledImageLabel with clicked signal and mousePressEvent coordinate mapping
  - phase: 02-desktop-gui/02-02
    provides: analysis_core.draw_manual_marks, MainWindow state structure (_images, _current_file)
provides:
  - Click-to-count annotation on annotated image with letterbox-aware coordinate mapping
  - Undo Mark button removes last manual mark and redraws
  - Combined algo_count + manual_marks total displayed in count_label
  - Full Clear/Reset restoring all state and parameters to defaults
  - All Phase 2 tests passing (28 passed, 1 pre-existing skip)
affects: [03-batch-management]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - draw_manual_marks called on each redraw with base annotated_rgb (no in-place mutation)
    - _redraw_annotated() is the single source of truth for annotated display + count label
    - from analysis_core import draw_manual_marks inside method to avoid circular imports

key-files:
  created:
    - tests/test_coordinate_mapping.py (fully implemented, no more skips)
  modified:
    - ui/main_window.py (_on_annotated_click, _on_undo_mark, _redraw_annotated, _on_clear, undo_mark_btn)
    - tests/test_main_window.py (test_total_count, test_clear_resets implemented)

key-decisions:
  - "_redraw_annotated always draws fresh: draws draw_manual_marks(base_annotated_rgb, marks) — no mutation of stored annotated_rgb"
  - "_on_clear calls param_panel.reset_defaults() for full parameter reset (CLR-01)"
  - "undo_mark_btn enabled/disabled based on marks list length to provide accurate affordance"

patterns-established:
  - "Single redraw function pattern: _redraw_annotated() is called from _on_annotated_click, _on_undo_mark, _on_image_selected, _on_image_done — single source of truth"
  - "from analysis_core import draw_manual_marks inside method body avoids circular import at module load"

requirements-completed: [MARK-01, MARK-02, MARK-03, CLR-01]

# Metrics
duration: 8min
completed: 2026-03-30
---

# Phase 2 Plan 03: Manual Annotation + Clear + Polish Summary

**Click-to-count annotation with letterbox-aware coordinate mapping, undo mark, combined count display, and full Clear/Reset completing all Phase 2 requirements**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-30T01:21:13Z
- **Completed:** 2026-03-30T01:29:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Enabled click-to-count on the annotated label using ScaledImageLabel's existing coordinate mapping (letterbox-aware)
- Implemented _on_annotated_click, _on_undo_mark, _redraw_annotated methods in MainWindow
- Added undo_mark_btn QPushButton that is enabled/disabled based on marks state
- Updated _on_clear to reset all state including param_panel.reset_defaults() and window title
- Replaced all pytest.mark.skip stubs in test_coordinate_mapping.py and test_main_window.py
- Full test suite: 28 passed, 1 skipped (pre-existing HiDPI platform skip unrelated to Phase 2)

## Task Commits

1. **Task 03-01: Enable click-to-count annotation with coordinate mapping + undo** - `93d3255` (feat)

**Note:** Task 03-02 had no additional code changes — all _on_clear requirements were implemented atomically in Task 03-01. Smoke test and full test suite verification confirmed completion.

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `ui/main_window.py` - Added _on_annotated_click, _on_undo_mark, _redraw_annotated, undo_mark_btn; updated _on_clear, _on_image_selected, _on_image_done
- `tests/test_coordinate_mapping.py` - Replaced skipped tests with full test_click_mapping, test_click_outside_image_rejected, test_undo_mark
- `tests/test_main_window.py` - Replaced skipped test_total_count and test_clear_resets with full implementations

## Decisions Made

- `_redraw_annotated()` always calls `draw_manual_marks(base_annotated_rgb, marks)` on each click — no mutation of stored annotated_rgb, clean redraw pattern
- `undo_mark_btn` is disabled initially and when marks list becomes empty, giving accurate UI affordance
- `from analysis_core import draw_manual_marks` placed inside method body (not module level) to maintain the pattern established in Plan 02-02 for avoiding circular imports

## Deviations from Plan

None - plan executed exactly as written. The _on_clear implementation combining both task 03-01 and 03-02 requirements was natural since they were tightly coupled (undo_mark_btn.setEnabled(False) belongs in both the button wiring and the clear reset).

## Issues Encountered

None — all tests passed on first run. QMouseEvent deprecation warnings in coordinate mapping tests are benign (PySide6 6.11.0 API deprecation, not errors).

## User Setup Required

None - no external service configuration required.

## Known Stubs

None — all features are fully wired. draw_manual_marks returns real drawn overlays, coordinate mapping uses actual pixel math.

## Next Phase Readiness

- Phase 2 is complete: all requirements (APP-*, IMG-*, ANAL-*, PARAM-*, MARK-*, CLR-*) implemented and tested
- Phase 3 (Batch Management) can begin: MainWindow has stable API, _images dict structure is finalized, analysis_core is isolated
- The undo_mark_btn and _redraw_annotated pattern is a stable foundation for Phase 3 batch re-analysis workflows

## Self-Check: PASSED

All created files verified present. Commit 93d3255 verified in git log.

---
*Phase: 02-desktop-gui*
*Completed: 2026-03-30*
