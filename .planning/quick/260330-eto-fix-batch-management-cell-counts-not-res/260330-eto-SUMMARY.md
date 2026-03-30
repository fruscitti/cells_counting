---
phase: quick
plan: 260330-eto
subsystem: ui
tags: [bug-fix, batch-management, results-table]
dependency_graph:
  requires: []
  provides: [BATCH-RESTORE, BATCH-SAVE-INPLACE, BATCH-TOTAL-ROW]
  affects: [ui/main_window.py]
tech_stack:
  added: []
  patterns: [in-place save branch, total row upsert]
key_files:
  modified: [ui/main_window.py]
decisions:
  - "_refresh_total_row called from _update_results_row as single funnel point — covers live analysis, re-analysis, and batch open paths"
  - "Total row upserted by searching for existing 'Total' row before inserting to avoid duplicates"
  - "In-place save uses update_manifest directly; statusBar toast used for confirmation (consistent with re-analysis pattern at line 622)"
metrics:
  duration: "~8 minutes"
  completed: "2026-03-30T13:46:42Z"
  tasks_completed: 2
  files_modified: 1
---

# Phase quick Plan 260330-eto: Fix Batch Management Cell Counts Not Restored Summary

Three batch management bugs fixed in `ui/main_window.py`: cell counts now populate the results table when opening a saved batch, Save Batch silently overwrites in-place when a batch is already open, and a bold Total row shows the running sum of all cell counts.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Restore cell counts on batch open and add Total row | 4a4ff5f | ui/main_window.py |
| 2 | Save Batch overwrites in-place when batch is open | 73e6ff8 | ui/main_window.py |

## What Was Built

**Task 1 — Batch restore + Total row:**
- Added `_update_results_row(filename, total)` call after `image_list.addItem(filename)` in `_load_batch_from_path`. The total is computed as `cell_count + len(manual_marks)` from the manifest entry, matching the re-analyze path.
- Added `_refresh_total_row()` method: iterates all non-Total rows, parses count text (handles "0 (warning)" format via `split()[0]`), upserts a bold "Total" row using `QFont().setBold(True)` and `QTableWidgetItem`.
- Added `_refresh_total_row()` call at both return points in `_update_results_row` so the total stays current for all update paths (live analysis, re-analysis, batch open).

**Task 2 — In-place save:**
- Replaced `_on_save_batch` with branching version: if `self._current_batch_dir is not None`, calls `BatchManager.update_manifest(...)` directly and shows `statusBar().showMessage("Batch saved", 2500)` toast, then returns early. If no batch is open, the existing prompt-for-name flow runs unchanged.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- `ui/main_window.py` exists and imports without error
- All 5 plan verification assertions pass
- Commits 4a4ff5f and 73e6ff8 present in git log
