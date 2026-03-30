---
phase: quick
plan: 260330-eto
type: execute
wave: 1
depends_on: []
files_modified: [ui/main_window.py]
autonomous: true
requirements: [BATCH-RESTORE, BATCH-SAVE-INPLACE, BATCH-TOTAL-ROW]

must_haves:
  truths:
    - "Opening a saved batch populates the File/Cell Count table with each image's count"
    - "Save Batch overwrites in-place when a batch is already open, without prompting for a name"
    - "Save Batch shows a brief toast confirmation when overwriting in-place"
    - "A bold Total row at the bottom of the results table shows the sum of all cell counts"
  artifacts:
    - path: "ui/main_window.py"
      provides: "All three bug fixes"
      contains: "_refresh_total_row"
  key_links:
    - from: "_load_batch_from_path"
      to: "_update_results_row"
      via: "call after each image is added to self._images"
      pattern: "_update_results_row\\(filename"
    - from: "_on_save_batch"
      to: "BatchManager.update_manifest"
      via: "branch on self._current_batch_dir"
      pattern: "update_manifest.*self._current_batch_dir"
    - from: "_update_results_row"
      to: "_refresh_total_row"
      via: "call at end of method"
      pattern: "_refresh_total_row"
---

<objective>
Fix three batch management bugs in ui/main_window.py: (1) cell counts not restored when opening a saved batch, (2) Save Batch always prompts for a name even when a batch is open, (3) no grand total cell count displayed.

Purpose: Batch open/save workflow is broken — users lose context and must re-analyze after opening a saved batch.
Output: Working batch restore with populated table, in-place save, and total row.
</objective>

<execution_context>
@/Users/ferar/fun/celulas/.claude/get-shit-done/workflows/execute-plan.md
@/Users/ferar/fun/celulas/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@ui/main_window.py
@.planning/quick/260330-eto-fix-batch-management-cell-counts-not-res/260330-eto-RESEARCH.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Restore cell counts on batch open and add Total row</name>
  <files>ui/main_window.py</files>
  <action>
Two changes in ui/main_window.py:

**A. Restore cell counts in `_load_batch_from_path`:**
After `self.image_list.addItem(filename)` (~line 510), add:
```python
total = entry.get("cell_count", 0) + len(entry.get("manual_marks", []))
self._update_results_row(filename, total)
```
This populates the results table from manifest data for each loaded image. The total includes both algo_count and manual_marks, consistent with the re-analyze path.

**B. Add `_refresh_total_row` helper method:**
Add a new method that:
1. Iterates all rows in `self.results_table`, skipping any existing "Total" row
2. Sums all cell count values (parsing int from text, handling "N (warning)" format via split()[0])
3. Inserts or updates a bold "Total" row at the bottom using QFont().setBold(True)
4. Uses QTableWidgetItem for both the label and count cells

**C. Call `_refresh_total_row()` at the end of `_update_results_row`:**
This is the single funnel point — all paths (live analysis via _on_image_done, re-analysis via _on_reanalyze_image_done, batch open from fix A) flow through _update_results_row, so the Total row stays current automatically.

QFont is already imported (line 11). No new imports needed.
  </action>
  <verify>
    <automated>cd /Users/ferar/fun/celulas && python -c "from ui.main_window import CellCounterWindow; print('Import OK')"</automated>
  </verify>
  <done>Opening a saved batch populates the File/Cell Count table with per-image counts and a bold Total row. The Total row updates on every table change.</done>
</task>

<task type="auto">
  <name>Task 2: Save Batch overwrites in-place when batch is open</name>
  <files>ui/main_window.py</files>
  <action>
Replace `_on_save_batch` (lines 438-447) with a branching version:

1. If `self._current_batch_dir is not None` (batch already open):
   - Call `BatchManager.update_manifest(self._current_batch_dir, self._images, params)` to update the manifest in-place without creating a new folder
   - Show toast via `self.statusBar().showMessage("Batch saved", 2500)` (2.5 seconds, already used elsewhere in the codebase at lines 622 and 636)
   - Return early

2. If `self._current_batch_dir is None` (no batch open):
   - Keep existing behavior: prompt with QInputDialog.getText, call BatchManager.save_batch, set _current_batch_dir, update window title

This matches the user decision: "When a batch is already open, Save Batch should silently overwrite/update without prompting for a name."
  </action>
  <verify>
    <automated>cd /Users/ferar/fun/celulas && python -c "
import inspect
from ui.main_window import CellCounterWindow
src = inspect.getsource(CellCounterWindow._on_save_batch)
assert '_current_batch_dir' in src, 'Missing branch on _current_batch_dir'
assert 'update_manifest' in src, 'Missing update_manifest call'
assert 'showMessage' in src, 'Missing toast message'
print('Save batch fix verified')
"</automated>
  </verify>
  <done>Save Batch silently overwrites when a batch is open (no name prompt), shows "Batch saved" toast for 2.5s. New batch still prompts for a name.</done>
</task>

</tasks>

<verification>
1. `python -c "from ui.main_window import CellCounterWindow"` — imports without error
2. Inspect `_on_save_batch` source for `_current_batch_dir` branch and `update_manifest` call
3. Inspect `_load_batch_from_path` source for `_update_results_row` call
4. Inspect `_update_results_row` source for `_refresh_total_row` call
5. Verify `_refresh_total_row` method exists with bold font logic
</verification>

<success_criteria>
- Opening a saved batch shows all image filenames with their cell counts in the results table
- A bold "Total" row appears at the bottom of the table summing all counts
- Save Batch on an open batch calls update_manifest (no QInputDialog)
- Save Batch on a new session still prompts for a batch name
- Toast "Batch saved" displayed for ~2.5 seconds on in-place save
</success_criteria>

<output>
After completion, create `.planning/quick/260330-eto-fix-batch-management-cell-counts-not-res/260330-eto-SUMMARY.md`
</output>
