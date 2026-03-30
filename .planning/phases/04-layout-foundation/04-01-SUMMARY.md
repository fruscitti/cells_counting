---
phase: 04-layout-foundation
plan: 01
subsystem: testing
tags: [pyside6, qt, pytest, tdd, sidebar, status-bar]

# Dependency graph
requires:
  - phase: 03-batch-management
    provides: MainWindow with _images dict, _current_file, load_images, statusBar
provides:
  - 7 failing tests defining Phase 4 acceptance criteria (RED phase of TDD)
  - Test coverage for SIDE-01, SIDE-02, SIDE-03, STAT-01, STAT-02, STAT-03, STAT-04
affects: [04-layout-foundation plan-02, any phase touching sidebar or status bar layout]

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD RED phase — tests written before implementation, assertions target attributes Plan 02 will add]

key-files:
  created: []
  modified:
    - tests/test_main_window.py

key-decisions:
  - "Tests import PySide6.QtCore.Qt and QPushButton inline (inside test bodies) to keep top-level imports minimal"
  - "test_sidebar_no_buttons uses isVisibleTo(left_scroll) for accurate visibility check inside scroll area widget tree"
  - "test_status_bar_cell_count injects _images entry directly rather than going through load_images+analyze (isolates _update_status_bar)"

patterns-established:
  - "Phase 4 TDD: all 7 requirements have explicit failing tests before any production code is written"
  - "Status bar tests use attribute name convention: _status_batch_lbl, _status_count_lbl, _status_cells_lbl"

requirements-completed: [SIDE-01, SIDE-02, SIDE-03, STAT-01, STAT-02, STAT-03, STAT-04]

# Metrics
duration: 8min
completed: 2026-03-30
---

# Phase 4 Plan 01: Layout Foundation (RED Phase) Summary

**7 failing TDD tests for outer QSplitter sidebar layout and permanent QStatusBar labels — all fail with AttributeError/AssertionError against unmodified MainWindow**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-30T22:05:00Z
- **Completed:** 2026-03-30T22:13:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Appended 7 test functions to `tests/test_main_window.py` covering all Phase 4 requirements
- Confirmed all 7 tests fail with assertion/attribute errors (not import errors) — clean RED state
- Confirmed all 5 pre-existing passing tests remain unaffected
- Identified and noted pre-existing failure in `test_total_count` (ValueError in process_image call — pre-dates this plan, not introduced here)

## Task Commits

1. **Task 1: Write 7 failing tests for Phase 4 requirements** - `de172b3` (test)

**Plan metadata:** pending

## Files Created/Modified

- `tests/test_main_window.py` - 7 new test functions appended (lines 98-155)

## Test to Requirement Mapping

| Test function | Requirement | What it asserts |
|---|---|---|
| test_splitter_exists | SIDE-01 | main_window.outer_splitter exists, orientation == Qt.Horizontal |
| test_sidebar_minimum_width | SIDE-02 | main_window.left_scroll.minimumWidth() >= 220 |
| test_sidebar_no_buttons | SIDE-03 | No visible QPushButton inside left_scroll widget tree |
| test_status_bar_initial | STAT-01/02/03 | _status_batch_lbl == "No batch", 0 in count/cells labels |
| test_status_bar_image_count | STAT-02 | "1" in _status_count_lbl.text() after load_images |
| test_status_bar_cell_count | STAT-03 | "5" in _status_cells_lbl.text() after injecting algo_count=3 + 2 manual_marks |
| test_status_bar_transient | STAT-04 | showMessage() does not overwrite _status_batch_lbl |

## Decisions Made

- Tests import Qt symbols inline (inside test bodies) — keeps top-level test file imports minimal and consistent with existing test style
- `test_sidebar_no_buttons` uses `isVisibleTo(left_scroll)` rather than `isVisible()` — Qt visibility is parent-chain aware, this is the correct check for scroll area children
- `test_status_bar_cell_count` injects `_images` dict directly to isolate `_update_status_bar()` without requiring a full analyze cycle

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pre-existing `test_total_count` failure (ValueError: too many values to unpack in process_image call) was present before this plan. Confirmed via git stash verification. Not introduced by this plan, not in scope to fix here.

## Known Stubs

None — this plan only writes tests. No production code was changed.

## Next Phase Readiness

- Plan 02 (GREEN phase) can begin: all 7 tests are wired and fail cleanly
- Plan 02 must add: `outer_splitter`, `left_scroll`, `_status_batch_lbl`, `_status_count_lbl`, `_status_cells_lbl` to MainWindow and implement `_update_status_bar()`
- The pre-existing `test_total_count` failure should be investigated in a separate quick fix before or during Plan 02

---
*Phase: 04-layout-foundation*
*Completed: 2026-03-30*
