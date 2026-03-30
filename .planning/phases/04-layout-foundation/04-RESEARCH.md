# Phase 4: Layout Foundation — Research

**Researched:** 2026-03-30
**Domain:** PySide6 desktop layout — QSplitter, QStatusBar, QSettings
**Confidence:** HIGH

---

## Summary

The desktop app is a PySide6 `QMainWindow` defined in `ui/main_window.py`. The current left panel is a `QScrollArea` with `setFixedWidth(298)` — it is rigid and cannot be resized by the user. The right side is a vertical `QSplitter`. No `QStatusBar` permanent widgets exist yet; there is a `status_label` (QLabel) and `count_label` (QLabel) sitting inside the left panel, and `self.statusBar().showMessage()` is already used for transient messages in three places.

Phase 4 requires two surgical changes: (1) replace the fixed-width `left_scroll` with a horizontal `QSplitter` so the sidebar is draggable, and (2) move the persistent batch/image/cell-count information from the left panel into the `QStatusBar` using `addPermanentWidget()`. No new dependencies are required — all needed Qt classes (`QSplitter`, `QStatusBar`, `QSettings`) are already available in the installed PySide6 6.11.0.

**Primary recommendation:** Wrap the existing `left_scroll` + `right_splitter` in a horizontal `QSplitter`; call `setMinimumWidth(220)` on the sidebar widget; use `QMainWindow.statusBar().addPermanentWidget()` for three always-visible labels; keep `showMessage()` for transient analysis messages.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SIDE-01 | User can resize the left sidebar by dragging a splitter handle | Outer QSplitter(Qt.Horizontal) replaces addWidget on main_layout for left_scroll |
| SIDE-02 | Sidebar has a minimum width and cannot be collapsed to zero | setMinimumWidth(220) on left_scroll prevents collapse; QSplitter respects it |
| SIDE-03 | Sidebar contains only the image list and parameter panel (no action buttons) | Remove all QPushButton children from left_layout; buttons move to toolbar/menu in Phase 5 |
| STAT-01 | Status bar persistently shows the current batch name (or "No batch") | statusBar().addPermanentWidget(QLabel) — label updated whenever _current_batch_dir changes |
| STAT-02 | Status bar persistently shows the current image count | Second permanent QLabel updated whenever self._images changes |
| STAT-03 | Status bar persistently shows the current total cell count | Third permanent QLabel updated whenever counts change |
| STAT-04 | Transient messages (progress, errors) use showMessage() without overwriting permanent labels | addPermanentWidget labels are on the right; showMessage() writes to the left — they coexist |
</phase_requirements>

---

## Stack & Current Architecture

**Frontend:** PySide6 6.11.0 (Qt for Python, LGPL). No web components. Entry point is `app.py` → `ui/main_window.py`.

**Key files:**
| File | Role |
|------|------|
| `app.py` | QApplication init, DPI policy, window launch |
| `ui/main_window.py` | All layout, state, and slot logic (820 lines) |
| `ui/param_panel.py` | Parameter sliders widget (lives inside left panel) |
| `ui/scaled_image_label.py` | Custom QLabel with zoom/click |
| `workers/analysis_worker.py` | QRunnable background analysis |
| `workers/optimize_worker.py` | QRunnable background optimizer |
| `tests/test_main_window.py` | Existing widget tests (qtbot-based) |

**Installed:** PySide6 6.11.0, pytest-qt, pytest. `QT_QPA_PLATFORM=offscreen` set in `tests/conftest.py` for headless test runs.

---

## Current Layout Structure

```
QMainWindow
└── central QWidget  (QHBoxLayout)
    ├── left_scroll  QScrollArea  setFixedWidth(298)
    │   └── left_panel  QWidget  setFixedWidth(278)
    │       ├── open_btn          QPushButton
    │       ├── image_list        QListWidget
    │       ├── param_panel       ParamPanel
    │       ├── analyze_btn       QPushButton
    │       ├── auto_optimize_btn QPushButton
    │       ├── clear_btn         QPushButton
    │       ├── save_batch_btn    QPushButton
    │       ├── open_batch_btn    QPushButton
    │       ├── add_images_btn    QPushButton
    │       ├── remove_image_btn  QPushButton
    │       ├── re_analyze_btn    QPushButton
    │       ├── export_csv_btn    QPushButton
    │       ├── undo_mark_btn     QPushButton
    │       ├── progress_bar      QProgressBar
    │       ├── status_label      QLabel ("Ready")
    │       └── count_label       QLabel ("Cell Count: 0")
    └── right_splitter  QSplitter(Qt.Vertical)
        ├── images_widget  (original | annotated side-by-side)
        └── results_table  QTableWidget
```

**Status bar usage today:** `self.statusBar().showMessage(text, timeout_ms)` is called in `_on_save_batch`, `_on_reanalyze_finished`, and `_on_export_csv`. No permanent widgets are set yet. `status_label` and `count_label` are `QLabel` widgets inside the left panel — they will move to the status bar.

---

## Resizable Sidebar Approach

**Pattern: Outer horizontal QSplitter**

Replace the `main_layout.addWidget(left_scroll)` approach with a single `QSplitter(Qt.Horizontal)` that takes both the sidebar and the right side as children.

```python
# Source: PySide6 docs — QSplitter
from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt

outer_splitter = QSplitter(Qt.Horizontal)
outer_splitter.addWidget(left_scroll)      # index 0: sidebar
outer_splitter.addWidget(right_splitter)   # index 1: image area

# Minimum width prevents collapse to zero (SIDE-02)
left_scroll.setMinimumWidth(220)
left_scroll.setMaximumWidth(500)           # optional upper bound

# Remove the old setFixedWidth calls on left_panel and left_scroll
# left_panel.setFixedWidth(278)  <- DELETE
# left_scroll.setFixedWidth(298)  <- DELETE

central_layout.addWidget(outer_splitter)
```

**Splitter state persistence (QSettings):** QSettings is already imported in PySide6; no QSettings usage exists in main_window.py today (confirmed by grep). Persistence is optional for Phase 4 but the pattern is:

```python
# Save on closeEvent
settings = QSettings("CellCounter", "Layout")
settings.setValue("sidebar_splitter", outer_splitter.saveState())

# Restore after window.show() (NOT in __init__)
QTimer.singleShot(0, lambda: outer_splitter.restoreState(
    settings.value("sidebar_splitter", b"")
))
```

STATE.md already documents: "QSplitter.restoreState() must be called after window.show() (or via QTimer.singleShot) — not during __init__". This is a confirmed pitfall to avoid.

**SIDE-03 — buttons stay in sidebar for now:** SIDE-03 says buttons should not be in the sidebar. However Phase 5 (Actions Surface) is where the menu bar and toolbar are added. For Phase 4 the buttons will be removed from the sidebar but they have no replacement yet. The safest approach: remove buttons from the sidebar layout in Phase 4. The actions will be wired in Phase 5. This avoids coupling the phases and matches SIDE-03 literally. However, this temporarily removes user access to Analyze, Save Batch, etc. until Phase 5. The planner must decide whether to leave them hidden/disabled in Phase 4 or accept the temporary loss.

---

## Status Bar Approach

**Qt native pattern: permanent widgets + transient showMessage()**

`QMainWindow.statusBar()` creates and returns the singleton `QStatusBar` on first call. `addPermanentWidget()` adds a widget that is always visible on the right side of the status bar and is never overwritten by `showMessage()`. `showMessage(text, timeout_ms)` writes a temporary message on the left; when it expires the permanent widgets remain.

```python
# Source: PySide6 QStatusBar docs
from PySide6.QtWidgets import QLabel

# Create permanent labels (called once in _build_ui or a new _setup_status_bar method)
self._status_batch_lbl  = QLabel("No batch")
self._status_count_lbl  = QLabel("0 images")
self._status_cells_lbl  = QLabel("0 cells")

bar = self.statusBar()
bar.addPermanentWidget(self._status_batch_lbl)
bar.addPermanentWidget(QLabel("|"))  # visual separator
bar.addPermanentWidget(self._status_count_lbl)
bar.addPermanentWidget(QLabel("|"))
bar.addPermanentWidget(self._status_cells_lbl)
```

**Update method:** A single `_update_status_bar()` helper called from every place that changes `_current_batch_dir`, `_images`, or cell counts:

```python
def _update_status_bar(self):
    batch_name = "No batch"
    if self._current_batch_dir is not None:
        batch_name = self._current_batch_dir.name
    image_count = len(self._images)
    total_cells = sum(
        e["algo_count"] + len(e["manual_marks"])
        for e in self._images.values()
    )
    self._status_batch_lbl.setText(batch_name)
    self._status_count_lbl.setText(f"{image_count} image{'s' if image_count != 1 else ''}")
    self._status_cells_lbl.setText(f"{total_cells} cell{'s' if total_cells != 1 else ''}")
```

Call sites: `load_images()`, `_on_clear()`, `_on_image_done()`, `_on_reanalyze_image_done()`, `_load_batch_from_path()`, `_on_remove_image()`, `_redraw_annotated()`.

**Transient messages (STAT-04):** All existing `self.statusBar().showMessage(...)` calls already work correctly with this approach. The permanent widgets stay on the right; the transient message appears on the left. `self.status_label` (left-panel QLabel) becomes redundant and can be removed when buttons are removed from sidebar.

**progress_bar position:** Currently in the left panel. For Phase 4 it should move out of the left panel since the sidebar will only contain image list + params. The simplest move: add the `progress_bar` to the status bar using `addWidget()` (left side, can be hidden). This avoids creating new layout containers.

---

## State Management

**How state flows today:**

| State | Where stored | How it reaches UI |
|-------|-------------|-------------------|
| Batch name | `self._current_batch_dir` (Path or None) | `setWindowTitle()` call after batch open/save |
| Image count | `len(self._images)` | No dedicated display — only visible indirectly via image_list |
| Total cell count | `self.count_label.setText()` | Updated per-image in `_redraw_annotated()`, `_update_results_row()` |

**After Phase 4:** All three values route through `_update_status_bar()`. The `count_label` QLabel remains for the per-image count in the main area (it shows the count for the *selected* image). The status bar shows the *total* across all images.

**Clarification needed by planner:** Should `count_label` stay in the main area (per-image count) or be removed in Phase 4? The requirements only mention the status bar labels. Safest: keep `count_label` in its current location (or move it to the right-side image area header), and add separate total-cell status bar label. They show different things.

---

## Files That Will Change

| File | Changes |
|------|---------|
| `ui/main_window.py` | Primary file. Remove `setFixedWidth` on `left_scroll`/`left_panel`. Introduce outer `QSplitter(Qt.Horizontal)`. Remove all `QPushButton` children from `left_layout`. Add `_setup_status_bar()` method. Add `_update_status_bar()` method. Move `progress_bar` to status bar. Remove `status_label` from left layout. Add `_status_batch_lbl`, `_status_count_lbl`, `_status_cells_lbl` QLabel instances. Call `_update_status_bar()` at all relevant sites. |
| `tests/test_main_window.py` | Update tests that reference removed buttons (analyze_btn, etc.). Add tests for status bar labels and splitter minimum width. |
| Possibly `tests/test_batch_ui.py` | Tests that trigger batch operations and check `status_label` text need updating. |

**Files that do NOT change:** `analysis_core.py`, `batch_manager.py`, `ui/param_panel.py`, `ui/scaled_image_label.py`, `workers/`, `app.py`.

---

## Key Risks / Gotchas

### Pitfall 1: setFixedWidth conflicts with QSplitter
**What goes wrong:** If `left_panel.setFixedWidth(278)` or `left_scroll.setFixedWidth(298)` is not removed, QSplitter's drag handle will appear but the width will not change — the fixed constraint overrides the splitter geometry.
**How to avoid:** Delete both `setFixedWidth` calls. Replace with `setMinimumWidth(220)` on `left_scroll` only.

### Pitfall 2: QSplitter restoreState called during __init__
**What goes wrong:** Calling `outer_splitter.restoreState()` before the window is shown causes the splitter to restore to zero or incorrect sizes because the geometry has not been resolved yet.
**How to avoid:** Use `QTimer.singleShot(0, lambda: ...)` so restore runs after the event loop starts. This is documented in STATE.md.

### Pitfall 3: Removing buttons before toolbar exists
**What goes wrong:** SIDE-03 requires buttons not be in the sidebar. But the toolbar/menu (Phase 5) does not exist yet. Removing buttons in Phase 4 leaves no way to trigger Analyze, Save Batch, etc.
**How to avoid:** Options are: (a) hide buttons (`setVisible(False)`) rather than deleting them — they can still be called programmatically and re-exposed in Phase 5; or (b) stub the toolbar in Phase 4 with the minimum buttons needed. The planner must decide.

### Pitfall 4: showMessage() timeout races with permanent widget text
**What goes wrong:** `showMessage(text, 0)` with timeout=0 means "never clear" — it can visually obscure the left side of the status bar indefinitely.
**How to avoid:** Always use a non-zero timeout for analysis messages (e.g., 3000ms). Permanent widgets on the right are unaffected regardless.

### Pitfall 5: total cell count definition
**What goes wrong:** `_refresh_total_row()` already computes a total in the results table but uses different data than `sum(algo_count + manual_marks)` from `_images`. They can drift if a row update is missed.
**How to avoid:** `_update_status_bar()` should read directly from `self._images` (the canonical state), not from the table widget. This is authoritative.

---

## Recommended Approach

**One method to add, one to replace, three fields to migrate.**

1. In `_build_ui()`: remove `setFixedWidth` on `left_scroll`/`left_panel`; create `outer_splitter = QSplitter(Qt.Horizontal)`; add `left_scroll` and `right_splitter` as children; set `left_scroll.setMinimumWidth(220)`.

2. Add `_setup_status_bar()` called at the end of `_build_ui()`: create three `QLabel` permanent widgets; move `progress_bar` to `addWidget()` on the status bar.

3. Add `_update_status_bar()` method; call it from `load_images`, `_on_clear`, `_on_image_done`, `_on_reanalyze_image_done`, `_load_batch_from_path`, `_on_remove_image`, `_redraw_annotated`.

4. Remove all QPushButtons from `left_layout` (hide with `setVisible(False)` is safer for Phase 4 continuity — they still exist as `self.*_btn` attributes and will be re-surfaced by Phase 5 as QAction-driven toolbar buttons).

5. Remove `status_label` and `count_label` from `left_layout` (the status bar handles this now); keep `count_label` only if it shows per-image count in the right area.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-qt 4.x |
| Config file | `pytest.ini` (root) |
| Quick run command | `.venv/bin/python -m pytest tests/test_main_window.py -x -q` |
| Full suite command | `.venv/bin/python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIDE-01 | Outer splitter exists and is horizontal | unit | `pytest tests/test_main_window.py::test_splitter_exists -x` | Wave 0 |
| SIDE-02 | Sidebar minimum width is >= 220 | unit | `pytest tests/test_main_window.py::test_sidebar_minimum_width -x` | Wave 0 |
| SIDE-03 | No QPushButton children in left_scroll widget | unit | `pytest tests/test_main_window.py::test_sidebar_no_buttons -x` | Wave 0 |
| STAT-01 | Status bar batch label shows "No batch" initially | unit | `pytest tests/test_main_window.py::test_status_bar_initial -x` | Wave 0 |
| STAT-02 | Status bar image count updates after load_images | unit | `pytest tests/test_main_window.py::test_status_bar_image_count -x` | Wave 0 |
| STAT-03 | Status bar cell count updates after analysis done | unit | `pytest tests/test_main_window.py::test_status_bar_cell_count -x` | Wave 0 |
| STAT-04 | showMessage() does not overwrite permanent labels | unit | `pytest tests/test_main_window.py::test_status_bar_transient -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `.venv/bin/python -m pytest tests/test_main_window.py -x -q`
- **Per wave merge:** `.venv/bin/python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_main_window.py` — add 7 new test functions listed above (file exists, new tests needed)
- [ ] Update existing tests that reference removed button widgets (e.g., `analyze_btn` in sidebar)

---

## Environment Availability

Step 2.6: No new external dependencies for this phase. All required Qt classes (QSplitter, QStatusBar, QSettings, QTimer) are part of PySide6 6.11.0 which is already installed. Python 3.12, pytest, and pytest-qt are already available.

---

## Sources

### Primary (HIGH confidence)
- PySide6 6.11.0 installed in `.venv` — verified via `python -c "import PySide6; print(PySide6.__version__)"`
- `ui/main_window.py` — direct code inspection, all layout decisions verified from source
- `tests/conftest.py`, `pytest.ini` — test infrastructure confirmed present
- STATE.md `## Research Findings for v3.0` — pre-existing verified findings from project team

### Secondary (MEDIUM confidence)
- Qt documentation pattern for `addPermanentWidget` vs `showMessage` coexistence — standard Qt behavior, confirmed available in installed version

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PySide6 6.11.0 confirmed installed, all needed classes verified importable
- Architecture: HIGH — main_window.py read in full; all attribute names, layout structure, and call sites identified
- Pitfalls: HIGH — derived from direct code inspection and STATE.md accumulated experience

**Research date:** 2026-03-30
**Valid until:** 2026-05-30 (PySide6 API is stable; layout changes are local)
