---
phase: 04-layout-foundation
plan: 02
subsystem: ui
tags: [pyside6, qt, sidebar, splitter, status-bar, tdd-green]

# Dependency graph
requires:
  - phase: 04-layout-foundation
    plan: 01
    provides: 7 failing RED tests for SIDE-01/02/03 and STAT-01/02/03/04
provides:
  - Resizable sidebar via QSplitter (outer_splitter wrapping left_scroll + right_splitter)
  - Persistent status bar with batch name, image count, and total cell count
  - All QPushButtons hidden from sidebar
affects: [05-actions-surface, 06-cleanup-shortcuts]

# Tech tracking
tech-stack:
  added: [QSettings for splitter state persistence, QTimer for deferred restore]
  patterns:
    - "outer_splitter = QSplitter(Qt.Horizontal) wrapping left_scroll + right_splitter"
    - "_update_status_bar() called at end of every state-mutating slot"
    - "addPermanentWidget() for always-visible labels; showMessage() only for transient messages"
    - "QTimer.singleShot(0, _restore_splitter_state) for deferred splitter restore after window show"

key-files:
  created: []
  modified:
    - ui/main_window.py
    - tests/test_main_window.py

key-decisions:
  - "status_label kept as attribute (not in layout) to avoid breaking existing slot references"
  - "progress_bar moved to status bar addWidget() (left side) instead of left_layout"
  - "Sidebar buttons hidden via setVisible(False) loop — addWidget calls preserved for Phase 5 re-use"
  - "7 Phase 4 RED tests added to this worktree (were on sibling worktree-agent-a68ffc39)"

metrics:
  duration: 15min
  completed: "2026-03-30T22:13:00Z"
  tasks: 2
  files_modified: 2
---

# Phase 4 Plan 02: Layout Foundation (GREEN Phase) Summary

**QSplitter sidebar replaces fixed-width layout; persistent status bar with 3 permanent labels — all 7 Phase 4 tests now green**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-30T22:00:00Z
- **Completed:** 2026-03-30T22:13:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

### Task 1: Replace fixed sidebar with outer QSplitter and hide action buttons

- Removed `left_panel.setFixedWidth(278)` — sidebar now resizable
- Changed `left_scroll` from local variable with `setFixedWidth(298)` to `self.left_scroll` with `setMinimumWidth(220)` and `setMaximumWidth(500)`
- Created `self.outer_splitter = QSplitter(Qt.Horizontal)` wrapping `left_scroll` (index 0) and `right_splitter` (index 1) — stretch factors 0 and 1 respectively
- Hidden all 11 QPushButtons in `left_layout` via a `setVisible(False)` loop
- Removed `status_label` and `progress_bar` from `left_layout` — kept as attributes, moved to status bar
- Added `QTimer` and `QSettings` to imports
- Added `_setup_status_bar()` and `_update_status_bar()` method stubs
- Added 7 Phase 4 TDD tests to `tests/test_main_window.py` (were on sibling worktree only)

### Task 2: Add _setup_status_bar and _update_status_bar; wire call sites

- `_setup_status_bar()`: creates `_status_batch_lbl`, `_status_count_lbl`, `_status_cells_lbl`; adds `progress_bar` to left side of status bar; adds 3 permanent labels separated by `|` separators
- `_update_status_bar()`: reads `_images` and `_current_batch_dir`, computes image count and total cell count (algo + manual), updates all 3 labels
- Wired `_update_status_bar()` as last call in: `load_images`, `_on_clear`, `_on_image_done`, `_on_reanalyze_image_done`, `_load_batch_from_path`, `_on_remove_image`, `_redraw_annotated`
- Called `_update_status_bar()` at end of `__init__` for correct initial state
- Added `closeEvent()` to persist splitter position via `QSettings("CellCounter", "Layout")`
- Added `_restore_splitter_state()` with deferred call via `QTimer.singleShot(0, ...)`

## Task Commits

1. **Task 1** — `7519bc9` feat(04-02): replace fixed sidebar with outer QSplitter and hide action buttons
2. **Task 2** — `ca5871f` feat(04-02): add _setup_status_bar, _update_status_bar and wire call sites

## Test to Requirement Mapping

| Test | Requirement | Result |
|------|-------------|--------|
| test_splitter_exists | SIDE-01 | PASS |
| test_sidebar_minimum_width | SIDE-02 | PASS |
| test_sidebar_no_buttons | SIDE-03 | PASS |
| test_status_bar_initial | STAT-01/02/03 | PASS |
| test_status_bar_image_count | STAT-02 | PASS |
| test_status_bar_cell_count | STAT-03 | PASS |
| test_status_bar_transient | STAT-04 | PASS |

## Pre-existing Failures (out of scope, not introduced by this plan)

- `test_total_count` — ValueError from `process_image()` returning 3 values (noted in 04-01 summary)
- `test_update_manifest` — BatchManager cell_count not updated correctly (pre-dates Phase 4)
- `test_tophat_visibility` — param panel tophat slider visibility issue (pre-dates Phase 4)
- `test_undo_mark` — same ValueError in process_image call

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Phase 4 RED tests missing from current worktree**

- **Found during:** Task 1 setup
- **Issue:** The 7 Phase 4 RED tests committed in plan 04-01 were on `worktree-agent-a68ffc39` branch, not present in this worktree (`worktree-agent-a5dc1af9`)
- **Fix:** Added the 7 tests directly to `tests/test_main_window.py` using the content from `git show de172b3:tests/test_main_window.py`
- **Files modified:** `tests/test_main_window.py`
- **Commit:** `7519bc9`

## Known Stubs

None — all status bar labels are wired to live `_images` state via `_update_status_bar()`.

## Observed Behavior

- Sidebar draggable via the splitter handle; respects minimum width of 220px
- Status bar shows "No batch | 0 images | 0 cells" on startup
- `showMessage()` calls (e.g., "Batch saved", "Re-analysis complete") appear on the left of the status bar and do not overwrite permanent labels on the right
- Splitter state persists across sessions via QSettings

## Self-Check: PASSED

- FOUND: `.planning/phases/04-layout-foundation/04-02-SUMMARY.md`
- FOUND: `ui/main_window.py` with `outer_splitter`, `left_scroll`, `_setup_status_bar`, `_update_status_bar`
- FOUND: commit `7519bc9` feat(04-02): replace fixed sidebar with outer QSplitter
- FOUND: commit `ca5871f` feat(04-02): add _setup_status_bar, _update_status_bar and wire call sites
- FOUND: commit `622fdce` docs(04-02): complete layout-foundation GREEN phase plan
- All 7 Phase 4 tests pass: test_splitter_exists, test_sidebar_minimum_width, test_sidebar_no_buttons, test_status_bar_initial, test_status_bar_image_count, test_status_bar_cell_count, test_status_bar_transient
