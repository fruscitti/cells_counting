# Quick Task 260330-i45: Unmark Detected Cells — Research

**Researched:** 2026-03-30
**Domain:** PySide6 Qt desktop UI — click-to-toggle cell marks, batch persistence
**Confidence:** HIGH (all findings from direct codebase inspection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Hit area = same as the drawn circle radius (radius 18px — matches cv2.circle calls)
- Unmarked cells disappear entirely from the canvas
- Counter drops immediately on click
- Full toggle: click an active mark to unmark it, click the spot again to re-mark

### Claude's Discretion
- How unmarked cell state is persisted in the batch JSON (e.g., a `removed_indices` list or a per-cell `active` flag)
- Whether the toggle re-mark works by showing a ghost/invisible hit area on the original detected position, or by some other mechanism

### Deferred Ideas (OUT OF SCOPE)
- None stated
</user_constraints>

---

## Critical Architectural Gap: Centroids Not Persisted

**This is the most important finding.** The current `process_image()` in `analysis_core.py` draws circles directly onto the `viz` (annotated) image and returns `(viz, count)`. The centroid list is consumed internally and discarded — it is never stored in `self._images[filename]`.

The `_images` dict structure today:
```python
{
    "original_bgr": ndarray,
    "original_rgb": ndarray,
    "annotated_rgb": ndarray,   # baked image with red circles already drawn on it
    "algo_count": int,
    "manual_marks": [(x, y), ...]   # green manual marks only
}
```

To support click-to-unmark on algo-detected cells, the centroid positions must be available at click time. They are not. This gap must be closed as part of this task.

---

## How Marks Are Currently Rendered

**Mark type 1 — Algo-detected cells (red):**
- Drawn by `process_image()` in `analysis_core.py` using `cv2.circle(..., 18, (0,0,255), 2)` and `cv2.putText`
- Baked into `annotated_rgb` numpy array — no separate centroid list stored
- `annotated_rgb` is saved as `annotated_<filename>.png` in the batch folder

**Mark type 2 — Manual marks (green):**
- Stored as `[(x, y), ...]` in `entry["manual_marks"]`
- Drawn by `draw_manual_marks()` in `analysis_core.py` on top of `annotated_rgb` every time `_redraw_annotated()` is called
- NOT baked; always re-rendered from the list

**`_redraw_annotated()` flow (ui/main_window.py:345–361):**
```python
base_rgb = entry["annotated_rgb"]          # has red circles baked in
display_rgb = draw_manual_marks(base_rgb, entry["manual_marks"])  # adds green circles on top
self.annotated_label.setPixmap(numpy_rgb_to_pixmap(display_rgb))
total = entry["algo_count"] + len(entry["manual_marks"])
```

**Click signal path (ScaledImageLabel → MainWindow):**
`ScaledImageLabel.mousePressEvent` → emits `clicked(orig_x, orig_y)` in original image coordinates (scaling/offset already removed) → connected to `_on_annotated_click` in `main_window.py`.

The coordinate translation already handles zoom correctly (line 138–140 in `scaled_image_label.py`).

---

## Recommended Architecture for Toggle

### Step 1: Store algo centroids alongside annotated_rgb

Modify `process_image()` to return centroids:
```python
# analysis_core.py — change return signature
return viz, count, centroid_list   # centroid_list: [(cx, cy), ...]
```

Store in `_images`:
```python
self._images[filename] = {
    ...
    "algo_count": count,
    "algo_centroids": centroid_list,   # NEW — list of (cx, cy) tuples
    "removed_indices": [],              # NEW — indices into algo_centroids that are toggled off
    "manual_marks": [],
}
```

Update `AnalysisSignals` and `AnalysisWorker` to pass centroids through, and update `_on_image_done` / `_on_reanalyze_image_done` to store them.

### Step 2: Rewrite _redraw_annotated to draw from state

Instead of using the baked `annotated_rgb`, draw everything fresh from `original_rgb` + the active algo centroids + manual marks. This is the cleanest approach:

```python
def _redraw_annotated(self):
    entry = self._images[self._current_file]
    base = entry["original_rgb"].copy()   # start from clean original
    removed = set(entry.get("removed_indices", []))
    active_centroids = [
        c for i, c in enumerate(entry.get("algo_centroids", []))
        if i not in removed
    ]
    # draw algo cells (red) — renumber sequentially
    for n, (cx, cy) in enumerate(active_centroids, 1):
        cv2.circle(base, (cx, cy), 18, (0, 0, 255), 2)
        cv2.putText(base, str(n), (cx-10, cy-25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    # draw manual marks (green) on top
    from analysis_core import draw_manual_marks
    display = draw_manual_marks(base, entry["manual_marks"])
    self.annotated_label.setPixmap(numpy_rgb_to_pixmap(display))
    total = len(active_centroids) + len(entry["manual_marks"])
    self.count_label.setText(f"Cell Count: {total}")
    self._update_results_row(self._current_file, total)
```

This eliminates the baked annotated_rgb as the drawing base and gives full control.

**Trade-off:** The `annotated_rgb` field currently saved to disk contains baked-in red circles. With this approach, `annotated_rgb` could remain for batch persistence of the base annotated image OR be generated on-demand before save. The simplest approach: keep saving `annotated_rgb` to disk (from `process_image`) but do NOT use it as the draw base in the UI — redraw from `original_rgb` + centroid state instead.

### Step 3: Hit-test on click

In `_on_annotated_click`, before adding a new manual mark, check whether the click lands within radius 18 of any active algo centroid or any manual mark:

```python
CIRCLE_RADIUS = 18

def _on_annotated_click(self, orig_x, orig_y):
    entry = self._images[self._current_file]

    # Check algo centroids (toggle remove/restore)
    removed = set(entry.get("removed_indices", []))
    for i, (cx, cy) in enumerate(entry.get("algo_centroids", [])):
        if (orig_x - cx)**2 + (orig_y - cy)**2 <= CIRCLE_RADIUS**2:
            if i in removed:
                removed.discard(i)   # re-mark
            else:
                removed.add(i)       # unmark
            entry["removed_indices"] = list(removed)
            self._redraw_annotated()
            return

    # Check manual marks (toggle remove)
    for i, (mx, my) in enumerate(entry["manual_marks"]):
        if (orig_x - mx)**2 + (orig_y - my)**2 <= CIRCLE_RADIUS**2:
            entry["manual_marks"].pop(i)
            self._redraw_annotated()
            self.undo_mark_btn.setEnabled(bool(entry["manual_marks"]))
            return

    # No hit — add new manual mark
    entry["manual_marks"].append((orig_x, orig_y))
    self._redraw_annotated()
    self.undo_mark_btn.setEnabled(True)
```

**Priority:** algo centroids checked first, then manual marks, then add-new. This matches the visual layering (manual marks drawn on top, but both checked).

### Step 4: Batch persistence

Add `removed_indices` to the manifest JSON. Both `save_batch` and `update_manifest` in `batch_manager.py` iterate `entry.get("manual_marks", [])` — the same pattern applies:

```python
# In manifest_images.append({...}) blocks:
"removed_indices": list(entry.get("removed_indices", [])),
```

On load in `load_batch`:
```python
img_entry["removed_indices"] = list(img_entry.get("removed_indices", []))
```

And in `_load_batch_from_path` (main_window.py):
```python
self._images[filename] = {
    ...
    "algo_count": entry.get("cell_count", 0),
    "algo_centroids": [tuple(c) for c in entry.get("algo_centroids", [])],
    "removed_indices": list(entry.get("removed_indices", [])),
    "manual_marks": list(entry.get("manual_marks", [])),
}
```

`algo_centroids` also needs to be persisted in the manifest (they're not stored today). Add to manifest per image:
```python
"algo_centroids": [list(c) for c in entry.get("algo_centroids", [])],
```

---

## Common Pitfalls

### Pitfall 1: annotated_rgb is a baked image — centroids are lost after analysis
`process_image()` today returns only `(viz_bgr, count)`. To toggle algo cells, centroids must be extracted and stored. The fix is to return `(viz, count, centroids)` and propagate through the worker signal.

**Worker signal change required:** `image_done = Signal(str, object, int)` → `image_done = Signal(str, object, int, object)` (adds centroids list).

### Pitfall 2: Coordinate space — click events are in original image coordinates
`ScaledImageLabel.mousePressEvent` already converts widget-pixel coordinates back to original image coordinates before emitting `clicked(orig_x, orig_y)`. The hit-test math should use original image coordinates directly — no additional scaling needed.

### Pitfall 3: Removed index stability across re-analysis
When the user hits Re-Analyze, `algo_centroids` changes (new detection). Old `removed_indices` point to positions in the old centroid list — they become invalid. On re-analysis completion, `removed_indices` must be reset to `[]` (same as how `manual_marks` are backed up and restored, but removal state cannot be meaningfully transferred). The marks backup in `_on_re_analyze` already clears and restores `manual_marks` — the same handler should reset `removed_indices = []` after re-analysis.

### Pitfall 4: Export CSV under-counts if removed cells not accounted for
`export_csv` in `batch_manager.py` computes `total_count = algo + manual`. After this change, `algo` should reflect active count (algo_count minus removed), not raw algo_count. The `cell_count` stored in manifest should be the active count (len(algo_centroids) - len(removed_indices)), not the raw detected count. Update `batch_manager.update_manifest` to write the effective count.

### Pitfall 5: Saving annotated_rgb to disk still uses baked image
The on-disk `annotated_<filename>.png` is used only for display restoration on batch load. After this change, the UI draws from `original_rgb` + centroids, so the on-disk annotated file is no longer used for display. It can remain for reference, but on load `annotated_rgb` loaded from disk will be ignored for rendering purposes. Confirm `_load_batch_from_path` does not pass `annotated_rgb` as the draw base to the new `_redraw_annotated` — it won't, since the new version draws from `original_rgb` directly.

---

## Files to Change

| File | Change |
|------|--------|
| `analysis_core.py` | `process_image()` returns `(viz, count, centroids_list)` |
| `workers/analysis_worker.py` | Update signal signature, pass centroids through |
| `ui/main_window.py` | `_on_image_done`, `_on_reanalyze_image_done` store centroids; `_on_annotated_click` hit-tests; `_redraw_annotated` draws from state; `_load_batch_from_path` loads centroids + removed_indices |
| `batch_manager.py` | `save_batch`, `update_manifest`, `load_batch` handle `algo_centroids` + `removed_indices` |
| `analysis_core.py` | `draw_manual_marks` stays unchanged (green marks only) |

---

## Sources

- Direct inspection of `/Users/ferar/fun/celulas/analysis_core.py` — process_image signature, centroid handling, draw_manual_marks
- Direct inspection of `/Users/ferar/fun/celulas/ui/main_window.py` — _images structure, _redraw_annotated, _on_annotated_click, batch load/save
- Direct inspection of `/Users/ferar/fun/celulas/ui/scaled_image_label.py` — click coordinate translation, zoom handling
- Direct inspection of `/Users/ferar/fun/celulas/batch_manager.py` — manifest JSON schema, save/load/update patterns
- Direct inspection of `/Users/ferar/fun/celulas/workers/analysis_worker.py` — signal types, worker run loop

**Confidence:** HIGH — all findings from direct source code, no external dependencies.
