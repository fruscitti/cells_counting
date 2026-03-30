# Phase 3: Batch Management - Research

**Researched:** 2026-03-29
**Domain:** Python file I/O, JSON manifests, PySide6 dialogs, pandas CSV export, atomic file writes
**Confidence:** HIGH

## Summary

Phase 3 adds batch persistence on top of a complete PySide6 desktop application (Phase 2). The core work is two Python modules: `batch_manager.py` for all folder/manifest I/O, and UI additions in `MainWindow` for Save/Open/Add/Remove/Re-Analyze/Export actions. No new third-party dependencies are required — all needed tools (`json`, `shutil`, `os`, `tempfile`, `pandas`, `cv2`) are already installed in `.venv`.

The state model is well-defined: a batch is a folder under `batches/<YYYY-MM-DD_name>/` containing copies of original images, annotated PNG files, and a `manifest.json` that is the single source of truth for parameters, counts, and manual marks. The `_images` dict in `MainWindow` already holds every piece of data the manifest needs to store. The planner can wire directly between those two representations.

The trickiest implementation detail is atomicity: always write to a `.tmp` file then `os.replace()` so a crash mid-save cannot corrupt the only copy. The second subtlety is that `manual_marks` are stored as `[[x, y], ...]` tuples in Python but must round-trip through JSON as lists. Both are simple to get right once identified.

**Primary recommendation:** Implement `BatchManager` as a pure-Python class with no Qt imports. Keep all Qt dialog logic in `MainWindow`. This keeps `batch_manager.py` fully unit-testable without a QApplication.

---

## Project Constraints (from CLAUDE.md)

- Use `.venv` environment; install packages with `uv pip install <library>`.
- Stack: PySide6 for desktop UI, Python backend only, no new frameworks.
- Entry point is `app.py` — `main.py` (Gradio) stays untouched.
- Keep the UI as simple as useful.
- No SQLite — folder + JSON is the chosen storage format (out-of-scope section in REQUIREMENTS.md).

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BATCH-01 | "Save Batch" button opens a name dialog | `QInputDialog.getText()` — one call, built into PySide6 |
| BATCH-02 | Batch saved as `batches/<YYYY-MM-DD_name>/` with manifest + image copies | `pathlib.Path.mkdir(parents=True)` + `shutil.copy2()` |
| BATCH-03 | manifest.json parameters includes all 9 processing parameters | `ParamPanel.get_params()` already returns all 9 keys |
| BATCH-04 | manifest.json images[].manual_marks stores `[[x,y],...]` | `json.dumps()` serializes tuples as lists; `json.loads()` returns lists — round-trip works, but re-load must accept lists as marks |
| BATCH-05 | Atomic save via temp file + `os.replace()` | `tempfile.NamedTemporaryFile(delete=False, dir=batch_dir)` + `os.replace()` |
| BATCH-06 | Batch name conflicts resolved by appending `_2`, `_3` counter | Simple `while Path(candidate).exists()` loop before `mkdir` |
| BMGR-01 | "Open Batch" shows list of saved batches with metadata | Custom `QDialog` with `QListWidget` populated from `BatchManager.list_batches()` |
| BMGR-02 | Opening a batch restores images, parameters, results | `BatchManager.load_batch()` returns structured data; `MainWindow.load_images()` + `ParamPanel.set_params()` already exist |
| BMGR-03 | Missing images flagged with warning (computed at load time) | `Path(image_path).exists()` check in `load_batch()`; status field = `"ok"` or `"missing"` |
| BMGR-04 | "Add Images" copies new images into batch folder, updates manifest | `shutil.copy2()` + atomic manifest rewrite |
| BMGR-05 | "Remove Image" removes manifest entry only (no file delete) | Filter `images[]` list, atomic manifest rewrite |
| BMGR-06 | "Re-Analyze" re-runs analysis on batch images; preserves manual_marks | Re-use existing `AnalysisWorker` pattern; pass `manual_marks` through untouched |
| BMGR-07 | "Export CSV" saves `<batch_name>_results.csv` with all columns | `pandas.DataFrame.to_csv()` — pandas already installed |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` | stdlib | Manifest read/write | Zero dependency; human-readable; already used throughout project |
| `shutil` | stdlib | Image file copy | `shutil.copy2()` preserves metadata; standard for file copy |
| `pathlib` | stdlib | Path manipulation | Cross-platform paths; cleaner than `os.path` string ops |
| `tempfile` | stdlib | Atomic save staging | `NamedTemporaryFile` on same filesystem as target = atomic `os.replace()` |
| `os` | stdlib | `os.replace()` for atomic rename | POSIX-atomic on same filesystem; Windows-atomic since Python 3.3 |
| `pandas` | 3.0.1 (installed) | CSV export | Already a project dependency; `DataFrame.to_csv()` handles all edge cases |
| `datetime` | stdlib | Timestamps in manifest | ISO 8601 format via `datetime.utcnow().isoformat()` |
| `PySide6.QtWidgets` | 6.11.0 (installed) | Dialogs | `QInputDialog`, `QDialog`, `QListWidget`, `QFileDialog` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `cv2` (opencv) | 4.13.0 (installed) | Save annotated PNG to disk | `cv2.imwrite()` for persisting annotated images in batch folder |
| `pytest-qt` | installed | Qt widget testing | All tests involving Qt widgets need `qtbot` fixture |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `json` + folder | SQLite | SQLite explicitly rejected in REQUIREMENTS.md out-of-scope |
| `os.replace()` | `shutil.move()` | `os.replace()` is atomic; `shutil.move()` is not guaranteed atomic |
| `QInputDialog.getText()` | Custom dialog | `QInputDialog` is sufficient for single-field name input; custom dialog is over-engineering |

**Installation:** No new packages needed — all dependencies are in `.venv` already.

---

## Architecture Patterns

### Recommended Project Structure
```
batch_manager.py         # New: pure-Python class, no Qt imports
batches/                 # Created at first save; gitignored
  2026-03-29_control/
    manifest.json
    original_img1.png
    original_img2.png
    annotated_img1.png
    annotated_img2.png
tests/
  test_batch_manager.py  # New: unit tests for BatchManager (no Qt)
  test_batch_ui.py       # New: integration tests for batch buttons in MainWindow
```

### Pattern 1: BatchManager — Pure I/O Class (No Qt)

**What:** A standalone class with static/instance methods that handle all disk operations. No `QWidget`, no `Signal`, no imports from `ui/` or `workers/`. Returns plain Python dicts/lists.

**When to use:** Always for any file or manifest operation. Qt code in `MainWindow` calls these methods; it does not do its own `json.dumps` or `shutil.copy2`.

**Why:** Enables pure-Python unit tests that run without a `QApplication`. Phase 2 established this pattern with `analysis_core.py` (no UI imports) and it proved effective.

```python
# Source: project pattern from analysis_core.py + workers/analysis_worker.py
import json, os, shutil, tempfile
from datetime import datetime, timezone
from pathlib import Path

class BatchManager:
    SCHEMA_VERSION = 1
    BATCHES_ROOT = Path("batches")

    @classmethod
    def save_batch(cls, name: str, images: dict, params: dict, results: dict) -> Path:
        """Create batch folder, copy images, write manifest atomically."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        folder_name = f"{date_str}_{name}"
        batch_dir = cls._resolve_unique(cls.BATCHES_ROOT / folder_name)
        batch_dir.mkdir(parents=True)
        # ... copy images, build manifest, atomic write
        return batch_dir

    @classmethod
    def _atomic_write_manifest(cls, batch_dir: Path, manifest: dict):
        target = batch_dir / "manifest.json"
        tmp_fd, tmp_path = tempfile.mkstemp(dir=batch_dir, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            os.replace(tmp_path, target)
        except Exception:
            os.unlink(tmp_path)
            raise
```

### Pattern 2: Manifest Schema v1

**What:** A versioned JSON document stored as `manifest.json` in the batch folder.

**Schema:**
```json
{
  "schema_version": 1,
  "name": "control",
  "created_at": "2026-03-29T12:00:00+00:00",
  "modified_at": "2026-03-29T12:00:00+00:00",
  "parameters": {
    "brightness_threshold": 120,
    "min_cell_area": 25,
    "blur_strength": 9,
    "max_cell_area": 500,
    "use_cleaning": true,
    "use_tophat": false,
    "tophat_kernel": 50,
    "adaptive_block": 99,
    "adaptive_c": -5
  },
  "images": [
    {
      "filename": "original_img1.png",
      "original_filename": "img1.png",
      "annotated_filename": "annotated_img1.png",
      "cell_count": 42,
      "manual_marks": [[120, 88], [200, 150]],
      "analyzed_at": "2026-03-29T12:00:01+00:00",
      "status": "ok"
    }
  ]
}
```

**Key design decisions:**
- `status` field is NOT persisted — it is computed by `load_batch()` at load time by checking `Path(filename).exists()`. This means `status` is always fresh and the manifest never contains stale "missing" entries.
- `manual_marks` stored as `[[x, y], ...]`. JSON loads these as lists of lists; code must accept `list` as well as `tuple` for mark coordinates (or convert on load).
- All 9 parameters from `ParamPanel.DEFAULTS` keys must be present.
- `annotated_filename` may be `null` if image has never been analyzed.

### Pattern 3: Open Batch Dialog

**What:** A `QDialog` subclass listing available batches with name, date, and image count. Shows warning indicator for batches with missing images.

```python
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QDialogButtonBox

class OpenBatchDialog(QDialog):
    def __init__(self, batches: list, parent=None):
        """batches: list of dicts from BatchManager.list_batches()"""
        super().__init__(parent)
        self.setWindowTitle("Open Batch")
        # Populate QListWidget with name + date + count; prefix "⚠" if has_missing
        ...

    def selected_path(self) -> Path | None:
        ...
```

### Pattern 4: Re-Analyze Preserving Manual Marks

**What:** Re-run `process_image()` on all batch images using current parameters, but keep the `manual_marks` from the existing `_images` dict untouched.

```python
# In _on_re_analyze():
# 1. Collect current marks BEFORE re-running
marks_backup = {fn: list(entry["manual_marks"]) for fn, entry in self._images.items()}
# 2. Run AnalysisWorker (same as regular Analyze)
# 3. In _on_image_done(), restore marks:
self._images[filename]["manual_marks"] = marks_backup.get(filename, [])
# 4. After finished signal: update manifest via batch_manager
```

### Pattern 5: UI State Management (Batch-Aware Buttons)

**What:** Buttons that only make sense when a batch is open must be disabled by default. Introduce `self._current_batch_dir` (None when no batch open) and a helper:

```python
def _update_batch_buttons(self):
    is_open = self._current_batch_dir is not None
    self.save_batch_btn.setEnabled(bool(self._images))  # can save any time with images
    self.add_images_btn.setEnabled(is_open)
    self.remove_image_btn.setEnabled(is_open and self._current_file is not None)
    self.re_analyze_btn.setEnabled(is_open and bool(self._images))
    self.export_csv_btn.setEnabled(is_open)
```

### Anti-Patterns to Avoid

- **Writing manifest from MainWindow directly:** All `json.dumps` and file writes must go through `BatchManager`. Keeps UI code clean and testable.
- **Storing `status: missing` in manifest:** Status is volatile (file might reappear). Compute it on load; never persist it.
- **Using `shutil.move()` for atomic save:** Not atomic on all platforms. Use `tempfile` + `os.replace()`.
- **Mutating `manual_marks` during re-analyze:** Back up marks before firing worker; restore after. The existing `_redraw_annotated` pattern (draw on copy, never mutate stored state) guides this.
- **Importing from `ui/` in `batch_manager.py`:** Would break unit tests that run without QApplication.
- **Saving annotated images as BGR:** `cv2.imwrite()` expects BGR. The `_images` dict stores `annotated_rgb`. Must `cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR)` before writing to disk.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file write | Custom locking scheme | `tempfile.mkstemp()` + `os.replace()` | POSIX guarantee; Windows atomic since Python 3.3 |
| CSV with multiple columns | Manual string building | `pandas.DataFrame.to_csv()` | Handles quoting, encoding, edge cases; pandas already installed |
| Conflict-free folder naming | UUID suffix | Simple counter loop `_2`, `_3` | Matches BATCH-06 requirement; human-readable |
| Single-field text input dialog | Custom QDialog | `QInputDialog.getText()` | One line; handles cancel/empty correctly |
| Cross-platform path joining | String concatenation | `pathlib.Path` / operator | Correct on Windows and macOS/Linux |

**Key insight:** The JSON + folder pattern is deliberately simple. The only non-obvious complexity is atomic writes and the BGR/RGB conversion for saving annotated images — both have standard library solutions.

---

## Common Pitfalls

### Pitfall 1: RGB/BGR Mismatch When Saving Annotated Images

**What goes wrong:** `cv2.imwrite("annotated.png", annotated_rgb)` saves a color-shifted image (red/blue swapped).

**Why it happens:** `_images[filename]["annotated_rgb"]` is stored in RGB (converted from BGR after `process_image()` returns BGR). `cv2.imwrite()` expects BGR.

**How to avoid:** Always convert before saving: `cv2.imwrite(path, cv2.cvtColor(entry["annotated_rgb"], cv2.COLOR_RGB2BGR))`.

**Warning signs:** Annotated images look correct in the UI but have wrong colors when opened in an external viewer.

### Pitfall 2: JSON Tuple → List Coercion for manual_marks

**What goes wrong:** After loading a batch, `entry["manual_marks"]` contains `[[120, 88], ...]` (lists) instead of `[(120, 88), ...]` (tuples). Code that does `x, y = mark` works either way, but `isinstance(mark, tuple)` checks would fail.

**Why it happens:** JSON has no tuple type — `json.dumps([(1,2)])` produces `[[1, 2]]`, and `json.loads` returns `[[1, 2]]`.

**How to avoid:** In `load_batch()`, convert marks on load: `[tuple(m) for m in raw_marks]`. Or write all mark-consuming code to accept sequences (not `isinstance(mark, tuple)`).

**Warning signs:** `_redraw_annotated()` works fine because `cv2.circle` accepts any sequence for center. No crash — silent wrong type.

### Pitfall 3: Manifest Written While Analysis Is Running

**What goes wrong:** User clicks "Save Batch" or "Re-Analyze" while a previous analysis worker is still in flight. Manifest is written before all `image_done` signals have fired, so some `cell_count` values in the manifest are stale (zero).

**Why it happens:** `QRunnable` runs in background; `_on_analyze` disables the Analyze button but does not disable Save/Re-Analyze.

**How to avoid:** Disable all batch mutation buttons (save, re-analyze, add, remove) while `self._is_analyzing` flag is True. Set flag in `_on_analyze`, clear in `_on_analysis_finished`.

**Warning signs:** Intermittent stale counts in saved manifests.

### Pitfall 4: `batches/` Relative Path Breaks When Working Directory Changes

**What goes wrong:** `BatchManager.BATCHES_ROOT = Path("batches")` resolves relative to the process CWD. If `app.py` is launched from a different directory, batches are created in the wrong place.

**Why it happens:** Python `Path("batches")` is relative to `os.getcwd()` at call time, not to `app.py`'s location.

**How to avoid:** Resolve to an absolute path anchored to the project root in `batch_manager.py`:
```python
PROJECT_ROOT = Path(__file__).parent
BATCHES_ROOT = PROJECT_ROOT / "batches"
```

**Warning signs:** Batch list appears empty when app is launched from a different working directory.

### Pitfall 5: `annotated_filename` is None for Unanalyzed Images

**What goes wrong:** Saving a batch where some images have not been analyzed yet — `entry["annotated_rgb"]` is `None`. Writing `None` to manifest and then trying to `cv2.imwrite(None, ...)` will crash.

**Why it happens:** `load_images()` initializes `"annotated_rgb": None` and `"algo_count": 0`. If user saves before analyzing, these are still None.

**How to avoid:** In `save_batch()`, skip annotated image copy if `entry["annotated_rgb"] is None`; set `"annotated_filename": null` in manifest. In `load_batch()`, skip annotated display if field is null.

**Warning signs:** `AttributeError` or `cv2.error` on save.

---

## Code Examples

### Atomic Manifest Write
```python
# Source: Python docs — os.replace() + tempfile pattern
import json, os, tempfile
from pathlib import Path

def _atomic_write_manifest(batch_dir: Path, manifest: dict):
    target = batch_dir / "manifest.json"
    fd, tmp_path = tempfile.mkstemp(dir=str(batch_dir), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        os.replace(tmp_path, str(target))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
```

### Unique Folder Name Resolution
```python
# Source: project decision BATCH-06
from pathlib import Path

def _resolve_unique(candidate: Path) -> Path:
    if not candidate.exists():
        return candidate
    base = str(candidate)
    counter = 2
    while True:
        p = Path(f"{base}_{counter}")
        if not p.exists():
            return p
        counter += 1
```

### Batch Status Check at Load Time
```python
# Source: BMGR-03 requirement — status NOT persisted, computed on load
def load_batch(cls, batch_dir: Path) -> dict:
    manifest_path = batch_dir / "manifest.json"
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    for img_entry in manifest["images"]:
        img_path = batch_dir / img_entry["filename"]
        img_entry["status"] = "ok" if img_path.exists() else "missing"
        # Normalize manual_marks: JSON lists → tuples
        img_entry["manual_marks"] = [tuple(m) for m in img_entry.get("manual_marks", [])]
    return manifest
```

### Export CSV with pandas
```python
# Source: pandas docs — DataFrame.to_csv()
import pandas as pd

def export_csv(manifest: dict, output_path: Path):
    rows = []
    for img in manifest["images"]:
        algo = img.get("cell_count", 0) or 0
        manual = len(img.get("manual_marks", []))
        rows.append({
            "filename": img["original_filename"],
            "total_count": algo + manual,
            "algo_count": algo,
            "manual_count": manual,
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
```

### QInputDialog for Batch Name
```python
# Source: PySide6 docs — QInputDialog.getText()
from PySide6.QtWidgets import QInputDialog

name, ok = QInputDialog.getText(self, "Save Batch", "Batch name:")
if ok and name.strip():
    self._do_save_batch(name.strip())
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.12.11 | — |
| PySide6 | All Qt UI | Yes | 6.11.0 | — |
| pandas | Export CSV | Yes | 3.0.1 | — |
| opencv-python | Save annotated images | Yes | 4.13.0 | — |
| json (stdlib) | Manifest I/O | Yes | stdlib | — |
| shutil (stdlib) | Image copy | Yes | stdlib | — |
| tempfile (stdlib) | Atomic write | Yes | stdlib | — |
| pathlib (stdlib) | Path ops | Yes | stdlib | — |
| pytest-qt | Test suite | Yes | installed | — |

**Missing dependencies with no fallback:** None — all required libraries already installed.

**Step 2.6: No new dependencies needed for this phase.**

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-qt |
| Config file | `pytest.ini` (exists: `qt_api = pyside6`, `testpaths = tests`) |
| Quick run command | `pytest tests/test_batch_manager.py -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BATCH-01 | Save Batch button exists and is wired | unit | `pytest tests/test_batch_ui.py::test_save_batch_button -x` | No — Wave 0 |
| BATCH-02 | `save_batch()` creates correct folder structure | unit | `pytest tests/test_batch_manager.py::test_save_creates_folder -x` | No — Wave 0 |
| BATCH-03 | All 9 parameters appear in saved manifest | unit | `pytest tests/test_batch_manager.py::test_manifest_has_all_params -x` | No — Wave 0 |
| BATCH-04 | manual_marks round-trip through JSON | unit | `pytest tests/test_batch_manager.py::test_marks_roundtrip -x` | No — Wave 0 |
| BATCH-05 | Atomic save leaves no tmp file on crash | unit | `pytest tests/test_batch_manager.py::test_atomic_write -x` | No — Wave 0 |
| BATCH-06 | Duplicate names get `_2` suffix | unit | `pytest tests/test_batch_manager.py::test_unique_name -x` | No — Wave 0 |
| BMGR-01 | Open Batch dialog shows batch list | unit | `pytest tests/test_batch_ui.py::test_open_batch_dialog -x` | No — Wave 0 |
| BMGR-02 | load_batch restores images and params | unit | `pytest tests/test_batch_manager.py::test_load_batch -x` | No — Wave 0 |
| BMGR-03 | Missing image files flagged as "missing" | unit | `pytest tests/test_batch_manager.py::test_missing_image_status -x` | No — Wave 0 |
| BMGR-04 | add_images copies files and updates manifest | unit | `pytest tests/test_batch_manager.py::test_add_images -x` | No — Wave 0 |
| BMGR-05 | remove_image removes entry only (no file delete) | unit | `pytest tests/test_batch_manager.py::test_remove_image_no_delete -x` | No — Wave 0 |
| BMGR-06 | Re-Analyze preserves manual_marks | unit | `pytest tests/test_batch_ui.py::test_reanalyze_preserves_marks -x` | No — Wave 0 |
| BMGR-07 | Export CSV has correct columns and row count | unit | `pytest tests/test_batch_manager.py::test_export_csv_columns -x` | No — Wave 0 |

**Note on BMGR-06 (Re-Analyze preserves marks):** This test touches Qt signals. Use `qtbot.waitSignal()` with a short timeout (same pattern as `test_analysis_worker.py`).

### Sampling Rate
- **Per task commit:** `pytest tests/test_batch_manager.py -x -q` (fast, no Qt needed)
- **Per wave merge:** `pytest tests/ -q` (full suite, includes Qt tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_batch_manager.py` — covers BATCH-02 through BATCH-06, BMGR-02 through BMGR-05, BMGR-07
- [ ] `tests/test_batch_ui.py` — covers BATCH-01, BMGR-01, BMGR-06 (requires `qtbot`)

**Existing infrastructure is sufficient** — `pytest.ini`, `conftest.py`, `qtbot` fixture, and `QT_QPA_PLATFORM=offscreen` are already established. Both new test files follow the same patterns as Phase 2 tests.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `open(f, "w") + f.write()` | `tempfile.mkstemp()` + `os.replace()` | Python 3.3+ | Atomic on POSIX and Windows |
| `os.path.join()` | `pathlib.Path` / operator | Python 3.4+ | Cross-platform, readable |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python 3.2+ | `utcnow()` is deprecated in 3.12 — use aware datetime |

**Deprecated:**
- `datetime.utcnow()`: Deprecated in Python 3.12. Use `datetime.now(timezone.utc).isoformat()` instead.

---

## Open Questions

1. **Where should `batches/` be created if the app is launched from a different CWD?**
   - What we know: `Path("batches")` is relative to CWD; `__file__` in `batch_manager.py` gives the source file location.
   - What's unclear: Is there a user preference for batch location (e.g., next to images)?
   - Recommendation: Anchor to `Path(__file__).parent` (project root) — consistent with how `images/` and `verified_counts/` work.

2. **Should "Save Batch" overwrite an existing open batch or always create a new folder?**
   - What we know: BATCH-06 handles name conflicts for new batches. REQUIREMENTS.md doesn't specify an "update existing" flow.
   - What's unclear: Whether re-saving after adding marks should update the same folder or create a new one.
   - Recommendation: For v1, "Save Batch" always creates a new folder. Re-saving the currently open batch can be addressed in v2.

3. **What happens to the `annotated_filename` field when Re-Analyze overwrites annotated images?**
   - What we know: Re-Analyze must update `cell_count` and annotated image files.
   - What's unclear: Whether filename stays the same or gets a timestamp suffix.
   - Recommendation: Keep the same filename (overwrite in place). Simpler; `modified_at` timestamp in manifest tracks when it changed.

---

## Sources

### Primary (HIGH confidence)
- Python stdlib docs — `os.replace()`, `tempfile.mkstemp()`, `json`, `shutil`, `pathlib`
- PySide6 6.11.0 (installed, tested) — `QInputDialog`, `QDialog`, `QListWidget`, `QFileDialog`
- pandas 3.0.1 (installed, tested) — `DataFrame.to_csv()`
- Project codebase (verified by reading) — `analysis_core.py`, `ui/main_window.py`, `ui/param_panel.py`, `workers/analysis_worker.py`, `tests/conftest.py`

### Secondary (MEDIUM confidence)
- Python 3.12 deprecation notes — `datetime.utcnow()` deprecated, use `datetime.now(timezone.utc)`

### Tertiary (LOW confidence)
- None — all claims are backed by installed versions or stdlib docs.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already installed and tested in Phase 2
- Architecture: HIGH — patterns derived from existing working codebase
- Pitfalls: HIGH — derived from reading actual code (RGB/BGR issue, None annotated, CWD issue all directly observable)
- Test map: HIGH — pytest infrastructure verified to work (`28 passed` in current suite)

**Research date:** 2026-03-29
**Valid until:** 2026-06-29 (stable stdlib + PySide6 LTS; pandas API stable)
