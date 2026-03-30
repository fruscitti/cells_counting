# Quick Task 260330-eto: Fix Batch Management — Research

**Researched:** 2026-03-30
**Domain:** PySide6 desktop app — batch open/save, results table rendering
**Confidence:** HIGH (all findings from direct source code inspection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Total count: Add a "Total" summary row at the bottom of the File/Cell Count table, summing all images
- Save Batch: When a batch is already open (has a current batch name), Save Batch should silently overwrite/update without prompting for a name
- After saving, show a brief toast/status confirmation message ("Batch saved") for 2-3 seconds

### Claude's Discretion
- Implementation details for how batch state is read/restored from manifest.json
- Exact styling of the Total row and toast message

### Deferred Ideas (OUT OF SCOPE)
- None listed
</user_constraints>

---

## Summary

Three independent bugs in `ui/main_window.py`. All fixes are surgical — no architecture changes needed. The root causes are: (1) `_load_batch_from_path` never calls `_update_results_row` after populating `self._images`, so the table stays empty; (2) `_on_save_batch` always prompts for a name with no branch for the already-open case; (3) `_update_results_row` has no concept of a Total row.

**Primary recommendation:** All three fixes are in `ui/main_window.py` only. No changes needed to `batch_manager.py`.

---

## Bug 1: Cell Counts Not Restored on Batch Open

### Root Cause

`_load_batch_from_path` (lines 463-528) rebuilds `self._images` and calls `self.image_list.addItem(filename)` for each image, but **never calls `_update_results_row`**. The results table (`self.results_table`) is cleared by `_on_clear()` at line 283 (`self.results_table.setRowCount(0)`) and is never repopulated during batch load.

### Data Path

The cell count is present in memory after load:
```
manifest["images"][i]["cell_count"]  →  loaded at line 506:
    self._images[filename] = {
        ...
        "algo_count": entry.get("cell_count", 0),   # line 506
        ...
    }
```

It just never flows into the table. The table is only updated via `_update_results_row` (line 370), which is called from `_on_image_done` (line 342) and `_on_reanalyze_image_done` (line 601) — both worker callbacks that don't run during batch open.

### Fix Location

`ui/main_window.py`, inside `_load_batch_from_path`, after the `self.image_list.addItem(filename)` call at line 510. After each image is added to `self._images`, call:

```python
total = entry.get("cell_count", 0) + len(entry.get("manual_marks", []))
self._update_results_row(filename, total)
```

Insert this block between lines 510 and 511 (after `self.image_list.addItem(filename)`).

**Note on manual marks + algo count:** The table shown during live analysis (via `_on_image_done`) shows only `algo_count`. But `_on_reanalyze_image_done` shows `algo + manual`. For the restore case, the manifest stores `algo_count` in `cell_count` and `manual_marks` separately. Showing `algo + manual` as the total is consistent with the re-analyze path and what the user sees in `count_label`.

---

## Bug 2: Save Batch Always Prompts for Name

### Root Cause

`_on_save_batch` (lines 438-447) unconditionally calls `QInputDialog.getText(...)`. There is no branch checking `self._current_batch_dir`.

```python
def _on_save_batch(self):
    name, ok = QInputDialog.getText(self, "Save Batch", "Batch name:")  # always runs
    if not ok or not name.strip():
        return
    params = self.param_panel.get_params()
    batch_dir = BatchManager.save_batch(name.strip(), self._images, params)
    self._current_batch_dir = batch_dir
    self.setWindowTitle(f"Cell Counter — {name.strip()}")
    self.status_label.setText(f"Batch saved: {batch_dir.name}")
```

`self._current_batch_dir` is set at line 445 (after first save) and at line 289 (`_on_clear` resets it to `None`). When a batch is open, it holds a `Path` to the batch folder.

### Existing Update Method

`BatchManager.update_manifest` (batch_manager.py line 194) already exists and rewrites the manifest with current image data and parameters. However it does not copy/overwrite image files — it only updates the JSON.

For a true "overwrite" save when a batch is already open, the right call is `BatchManager.save_batch` with the **existing batch name**, but that would create a new timestamped folder with `_resolve_unique` appending a suffix (line 38).

**Better approach:** When `_current_batch_dir` is set, call `BatchManager.update_manifest(self._current_batch_dir, self._images, params)` — this updates the manifest in-place without creating a new folder, matching user expectation of "overwrite in-place".

### Fix Location

`ui/main_window.py`, replace `_on_save_batch` (lines 438-447) with a branching version:

```python
def _on_save_batch(self):
    if self._current_batch_dir is not None:
        # Batch already open — update in-place
        params = self.param_panel.get_params()
        BatchManager.update_manifest(self._current_batch_dir, self._images, params)
        self.status_label.setText("Batch saved")
        self.statusBar().showMessage("Batch saved", 2500)
        return
    # No batch open — prompt for name
    name, ok = QInputDialog.getText(self, "Save Batch", "Batch name:")
    if not ok or not name.strip():
        return
    params = self.param_panel.get_params()
    batch_dir = BatchManager.save_batch(name.strip(), self._images, params)
    self._current_batch_dir = batch_dir
    self.setWindowTitle(f"Cell Counter — {name.strip()}")
    self.status_label.setText(f"Batch saved: {batch_dir.name}")
```

**Toast mechanism:** `self.statusBar().showMessage(text, ms)` is already used in `_on_reanalyze_finished` (line 622) and `_on_export_csv` (line 636) — no new mechanism needed.

---

## Bug 3: No Total Cell Count Row in Table

### Root Cause

`_update_results_row` (lines 370-383) only inserts/updates per-file rows. There is no Total row logic anywhere.

### Current Table Structure

```python
self.results_table = QTableWidget(0, 2)           # line 144
self.results_table.setHorizontalHeaderLabels(["File", "Cell Count"])
```

### Fix Location

Two changes needed in `ui/main_window.py`:

**A. New helper `_refresh_total_row`** — to be called after every `_update_results_row` call:

```python
def _refresh_total_row(self):
    """Maintain a bold 'Total' row at the bottom of the results table."""
    TOTAL_LABEL = "Total"
    # Sum all non-total rows
    total = 0
    total_row_idx = None
    for row in range(self.results_table.rowCount()):
        item = self.results_table.item(row, 0)
        if item and item.text() == TOTAL_LABEL:
            total_row_idx = row
            continue
        count_item = self.results_table.item(row, 1)
        if count_item:
            try:
                total += int(count_item.text().split()[0])  # handles "0 (warning)"
            except ValueError:
                pass
    # Insert or update Total row
    if total_row_idx is None:
        total_row_idx = self.results_table.rowCount()
        self.results_table.insertRow(total_row_idx)
    label_item = QTableWidgetItem(TOTAL_LABEL)
    count_item = QTableWidgetItem(str(total))
    font = QFont()
    font.setBold(True)
    label_item.setFont(font)
    count_item.setFont(font)
    self.results_table.setItem(total_row_idx, 0, label_item)
    self.results_table.setItem(total_row_idx, 1, count_item)
```

**B. Call `_refresh_total_row()`** at the end of every `_update_results_row` call. `_update_results_row` is the single funnel point — all three paths (live analysis, re-analysis, batch open after fix #1) go through it.

Also call `_refresh_total_row()` after `self.results_table.setRowCount(0)` in `_on_clear` is NOT needed — clearing the table already removes all rows including any Total row.

---

## All Changes Summary

| File | Location | Change |
|------|----------|--------|
| `ui/main_window.py` | `_load_batch_from_path`, after `self.image_list.addItem(filename)` (~line 510) | Call `_update_results_row(filename, total)` for each loaded image |
| `ui/main_window.py` | `_on_save_batch` (lines 438-447) | Branch on `self._current_batch_dir` — call `update_manifest` in-place when batch is open |
| `ui/main_window.py` | `_update_results_row` (line 383, end of method) | Add call to `_refresh_total_row()` |
| `ui/main_window.py` | new method | Add `_refresh_total_row()` helper |

No changes to `batch_manager.py`, `analysis_core.py`, or any other file.

---

## Key Facts

- `self._current_batch_dir` is `None` when no batch open, `Path` when open — reliable branch condition (confidence: HIGH, direct code inspection)
- `BatchManager.update_manifest` already handles updating images + params without creating a new folder (confidence: HIGH, lines 194-213 of batch_manager.py)
- `self.statusBar().showMessage(text, ms)` auto-clears after `ms` milliseconds — already used twice (confidence: HIGH, lines 622, 636)
- The results table is a plain `QTableWidget` with no delegate or model — direct `setItem` manipulation is correct (confidence: HIGH)
- `QFont` is already imported in main_window.py (line 11) — no new imports needed for the bold Total row

## Sources

All findings are from direct inspection of:
- `/Users/ferar/fun/celulas/ui/main_window.py` (primary)
- `/Users/ferar/fun/celulas/batch_manager.py` (secondary, update_manifest signature)
