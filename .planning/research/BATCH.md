# Batch Management Patterns
**Research date:** 2026-03-29

---

## 1. Folder Structure

### Recommended layout

```
batches/
  <batch-slug>/
    manifest.json       # single source of truth for the batch
    images/             # copies of originals (not references)
      cell_image_01.tif
      cell_image_02.tif
    annotated/          # algorithm output PNGs, regenerated on re-analysis
      annotated_cell_image_01.png
      annotated_cell_image_02.png
    export.csv          # optional, written on demand by the user
```

**One directory per batch.** The batch slug is a URL-safe, human-readable string derived from the batch name at creation time (e.g., `"My Experiment 1"` → `my-experiment-1`). Append a short timestamp suffix (`_20260329`) only when a slug collision is detected (see §7).

### Why copy images instead of storing references

References (absolute paths) break silently when the user moves, renames, or archives source folders. For a desktop science tool used by researchers who routinely reorganize data:

- **Copy on create.** Call `shutil.copy2(src, batch_dir / "images" / filename)` at batch creation time. `copy2` preserves mtime so the original timestamp survives.
- **Annotated images are always derived.** Never treat them as originals. Delete and regenerate freely during re-analysis.
- **Cost is acceptable.** Fluorescence microscopy TIFFs are typically 2–20 MB each. A 20-image batch is well under 400 MB.

If storage is a later concern, a `use_references` flag can be added to `manifest.json` and the loader falls back gracefully (see §6).

---

## 2. Manifest Schema

### Recommended `manifest.json`

```json
{
  "schema_version": 1,
  "id": "a3f2c1d0-...",
  "name": "Experiment Control – Day 3",
  "created_at": "2026-03-29T14:22:00Z",
  "modified_at": "2026-03-29T15:10:44Z",
  "parameters": {
    "brightness_threshold": 120,
    "min_cell_area": 25,
    "max_cell_area": 500,
    "blur_strength": 9,
    "use_cleaning": true,
    "use_tophat": true,
    "tophat_kernel": 50,
    "adaptive_block": 99,
    "adaptive_c": -5
  },
  "images": [
    {
      "filename": "cell_image_01.tif",
      "original_path": "/Users/alice/data/day3/cell_image_01.tif",
      "annotated_filename": "annotated_cell_image_01.png",
      "cell_count": 47,
      "manual_marks": [[120, 88], [305, 412]],
      "manual_count": 2,
      "total_count": 49,
      "analyzed_at": "2026-03-29T14:25:11Z",
      "status": "ok"
    },
    {
      "filename": "cell_image_02.tif",
      "original_path": "/Users/alice/data/day3/cell_image_02.tif",
      "annotated_filename": "annotated_cell_image_02.png",
      "cell_count": 31,
      "manual_marks": [],
      "manual_count": 0,
      "total_count": 31,
      "analyzed_at": "2026-03-29T14:25:19Z",
      "status": "ok"
    }
  ]
}
```

### Field rationale

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Increment when the schema changes. Lets the loader detect and migrate old batches. Start at `1`. |
| `id` | uuid4 string | Stable identifier. The folder slug can be renamed; the ID never changes. Generate with `str(uuid.uuid4())`. |
| `name` | string | Human-editable display name. Separate from the slug. |
| `created_at` / `modified_at` | ISO 8601 UTC | Use `datetime.utcnow().isoformat() + "Z"`. Update `modified_at` on every save. |
| `parameters` | object | Snapshot of analysis settings at last run. All 9 current parameters are stored. Adding new parameters later is non-breaking (loader uses `.get()` with defaults). |
| `images[].filename` | string | Basename only. Full path is always `batch_dir / "images" / filename`. |
| `images[].original_path` | string | Informational. Not used by the loader; useful for audit trails. |
| `images[].annotated_filename` | string | Basename of the output PNG in `annotated/`. Predictable pattern: `"annotated_" + filename_stem + ".png"`. |
| `images[].cell_count` | int | Algorithm-only count from the last analysis run. |
| `images[].manual_marks` | `[[x,y], ...]` | List of pixel coordinates added via click-to-annotate. |
| `images[].manual_count` | int | `len(manual_marks)`. Denormalized for fast reads. |
| `images[].total_count` | int | `cell_count + manual_count`. Denormalized for CSV export. |
| `images[].analyzed_at` | ISO 8601 UTC | Timestamp of the last algorithm run for this image. |
| `images[].status` | string | `"ok"`, `"missing"`, `"error"`. Set by the loader at open time (see §6). |

### Python dataclass representation

```python
from dataclasses import dataclass, field
from typing import List, Tuple
import uuid, datetime, json, os

@dataclass
class ImageEntry:
    filename: str
    original_path: str
    annotated_filename: str
    cell_count: int = 0
    manual_marks: List[Tuple[int, int]] = field(default_factory=list)
    manual_count: int = 0
    total_count: int = 0
    analyzed_at: str = ""
    status: str = "ok"

@dataclass
class BatchManifest:
    schema_version: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Batch"
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    modified_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    parameters: dict = field(default_factory=dict)
    images: List[ImageEntry] = field(default_factory=list)
```

Use `dataclasses.asdict()` for serialization; `json.dumps(asdict(manifest), indent=2)` writes clean, readable JSON.

---

## 3. Atomic Manifest Save

Never write `manifest.json` directly — a crash mid-write corrupts the file.

**Pattern:** write to a temp file in the same directory, then atomically replace.

```python
import json, os, tempfile
from pathlib import Path

def save_manifest(batch_dir: Path, data: dict) -> None:
    target = batch_dir / "manifest.json"
    tmp_fd, tmp_path = tempfile.mkstemp(dir=batch_dir, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target)   # atomic on POSIX; best-effort on Windows
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
```

`os.replace()` is atomic on the same filesystem (POSIX guarantee). It works on Windows too but is not guaranteed atomic there — acceptable for a single-user desktop tool.

---

## 4. Batch Listing UI

### Widget choice

**Use `QListWidget`**, not `QTreeWidget`. The batch list is flat (no hierarchy). `QListWidget` is simpler, has built-in selection, double-click signals, and context menus without the overhead of `QTreeWidget`.

### Loading pattern

```python
from pathlib import Path
import json

BATCHES_ROOT = Path("batches")

def list_batches() -> list[dict]:
    """Return list of {slug, name, created_at, image_count} sorted newest-first."""
    results = []
    for d in BATCHES_ROOT.iterdir():
        if not d.is_dir():
            continue
        manifest_path = d / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            with open(manifest_path, encoding="utf-8") as f:
                m = json.load(f)
            results.append({
                "slug": d.name,
                "name": m.get("name", d.name),
                "created_at": m.get("created_at", ""),
                "image_count": len(m.get("images", [])),
            })
        except (json.JSONDecodeError, OSError):
            # Corrupted or unreadable manifest — skip silently
            continue
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return results
```

**Display item text:** `"{name}  ({image_count} images)  –  {created_at[:10]}"`. Show the date component only (first 10 chars of ISO string).

**Open/load on double-click:** Connect `QListWidget.itemDoubleClicked` to load the full manifest and populate the main UI.

**Context menu on right-click:** "Rename", "Delete", "Export CSV". Delete moves the folder to OS trash via `send2trash` library rather than permanent deletion.

---

## 5. Re-analysis Pattern

Re-analysis replaces `cell_count`, `annotated_filename`, and `analyzed_at` for each image. It does NOT touch `manual_marks` — the user's manual additions survive the re-run.

```python
def reanalyze_batch(batch_dir: Path, manifest: dict, new_params: dict) -> dict:
    manifest["parameters"] = new_params
    manifest["modified_at"] = utcnow_iso()

    for entry in manifest["images"]:
        if entry["status"] == "missing":
            continue   # skip images that have already been flagged missing
        img_path = batch_dir / "images" / entry["filename"]
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            entry["status"] = "error"
            continue

        # Run analysis with new parameters
        ann_bgr, count = process_image(img_bgr, **params_to_kwargs(new_params))

        # Overwrite annotated file
        ann_path = batch_dir / "annotated" / entry["annotated_filename"]
        ann_path.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(ann_path), ann_bgr)

        entry["cell_count"] = count
        entry["manual_count"] = len(entry["manual_marks"])
        entry["total_count"] = count + entry["manual_count"]
        entry["analyzed_at"] = utcnow_iso()
        entry["status"] = "ok"

    save_manifest(batch_dir, manifest)
    return manifest
```

**Key constraint:** `blur_strength` in `manifest.json` stores the integer (e.g., `9`), not the tuple. `process_image` in `main.py` receives the integer and passes it to `cv2.GaussianBlur` as `(blur_strength, blur_strength)` — no tuple storage needed in JSON.

---

## 6. Add and Remove Images

### Adding images

```python
def add_images_to_batch(batch_dir: Path, manifest: dict, new_paths: list[Path]) -> dict:
    existing = {e["filename"] for e in manifest["images"]}
    added = []
    for src in new_paths:
        dest_name = src.name
        # Deduplicate filename within batch
        if dest_name in existing:
            stem, suffix = src.stem, src.suffix
            dest_name = f"{stem}_1{suffix}"  # simple increment
        shutil.copy2(src, batch_dir / "images" / dest_name)
        manifest["images"].append({
            "filename": dest_name,
            "original_path": str(src),
            "annotated_filename": f"annotated_{Path(dest_name).stem}.png",
            "cell_count": 0,
            "manual_marks": [],
            "manual_count": 0,
            "total_count": 0,
            "analyzed_at": "",
            "status": "ok",
        })
        existing.add(dest_name)
        added.append(dest_name)
    manifest["modified_at"] = utcnow_iso()
    save_manifest(batch_dir, manifest)
    return manifest, added
```

Newly added images have `cell_count = 0` and `status = "ok"` — they are flagged for analysis but not yet analyzed. The UI should highlight unanalyzed images.

### Removing images

**Remove from manifest only, leave files on disk.** This is the safer default:

```python
def remove_image_from_batch(batch_dir: Path, manifest: dict, filename: str) -> dict:
    manifest["images"] = [e for e in manifest["images"] if e["filename"] != filename]
    manifest["modified_at"] = utcnow_iso()
    save_manifest(batch_dir, manifest)
    # Files are left in batch_dir/images/ and batch_dir/annotated/
    # They become "orphaned" but are recoverable
    return manifest
```

Offer a separate "Clean up unused files" action that deletes orphaned image and annotated files not referenced in the manifest. This two-step approach prevents accidental data loss.

---

## 7. CSV Export

```python
import pandas as pd

def export_csv(batch_dir: Path, manifest: dict) -> Path:
    rows = []
    for entry in manifest["images"]:
        rows.append({
            "file": entry["filename"],
            "algorithm_count": entry["cell_count"],
            "manual_additions": entry["manual_count"],
            "total_count": entry["total_count"],
            "status": entry["status"],
        })
    df = pd.DataFrame(rows)
    out_path = batch_dir / "export.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    return out_path
```

**Column order matters** for researchers who open CSVs in Excel. Put the most important column (`total_count`) last so it is the rightmost "answer" column. Always use `index=False` — the DataFrame index is meaningless here.

For a multi-batch export (summary across all batches), collect rows from all manifests and add a `batch_name` column as the first field.

---

## 8. Missing Files (Edge Cases)

### Detection at batch open time

```python
def validate_batch(batch_dir: Path, manifest: dict) -> dict:
    """Mark each image entry 'ok', 'missing', or 'no_annotated' at load time."""
    for entry in manifest["images"]:
        img_path = batch_dir / "images" / entry["filename"]
        if not img_path.exists():
            entry["status"] = "missing"
        elif entry["annotated_filename"] and not (
            batch_dir / "annotated" / entry["annotated_filename"]
        ).exists():
            entry["status"] = "no_annotated"  # image OK, just needs re-analysis
        else:
            entry["status"] = "ok"
    return manifest
```

**Do NOT save `status` back to the manifest.** Status is runtime state derived from disk contents. Saving it would create stale information the next time the batch is opened on a different machine.

### UI treatment

| Status | UI indicator | User action offered |
|---|---|---|
| `ok` | Normal | — |
| `no_annotated` | Yellow warning icon | "Re-analyze" |
| `missing` | Red warning icon, greyed out | "Locate file…" (re-link) or "Remove from batch" |

### "Locate file" re-link pattern

Open a file dialog, let the user pick the replacement file, copy it to `batch_dir / "images" / entry["filename"]`, update `entry["original_path"]`, set `entry["status"] = "ok"`, save manifest.

---

## 9. Batch Naming and Slug Conflicts

```python
import re
from pathlib import Path

def name_to_slug(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:48] or "batch"  # max 48 chars

def unique_batch_dir(batches_root: Path, name: str) -> Path:
    slug = name_to_slug(name)
    candidate = batches_root / slug
    if not candidate.exists():
        return candidate
    # Append incrementing suffix
    i = 2
    while True:
        candidate = batches_root / f"{slug}-{i}"
        if not candidate.exists():
            return candidate
        i += 1
```

The `id` field in the manifest is the stable identifier across renames. The folder slug (directory name) is only used for filesystem navigation. Renaming a batch = renaming the directory + updating `manifest["name"]` + updating `manifest["modified_at"]`.

---

## 10. Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Folder structure (copy vs reference) | HIGH | Derived from patterns in labelme, napari, CellProfiler; copy-on-create is universal in desktop science tools |
| Manifest JSON schema | HIGH | Fields match what the existing `main.py` state dict tracks; aligns with annotation tools like VIA and SuperAnnotate |
| Atomic save via temp+replace | HIGH | Standard POSIX pattern, documented in Python stdlib discussions |
| QListWidget for batch listing | HIGH | Flat list of batches is the canonical use case for QListWidget |
| Re-analysis preserving manual marks | HIGH | Derives directly from the current `annotation_state` structure in `main.py` |
| CSV via pandas `to_csv` | HIGH | Official pandas docs, stable API |
| Missing file handling | MEDIUM | Pattern is standard; specific UI treatment (yellow/red icons) is an implementation recommendation, not a community standard |

---

## Sources

- [CellProfiler Batch Processing Documentation](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.4/help/other_batch.html)
- [labelme annotation tool (GitHub)](https://github.com/wkentaro/labelme)
- [napari image viewer (napari.org)](https://napari.org/stable/tutorials/fundamentals/viewer.html)
- [Atomic file writes in Python (python-atomicwrites)](https://python-atomicwrites.readthedocs.io/)
- [Crash-safe JSON: atomic writes + recovery (DEV Community)](https://dev.to/constanta/crash-safe-json-at-scale-atomic-writes-recovery-without-a-db-3aic)
- [pandas DataFrame.to_csv documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html)
- [QListWidget — Qt for Python](https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QListWidget.html)
- [pyJSON Schema Loader: file-based metadata management (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2352711024003157)
- [VGG Image Annotator (VIA) project format](https://www.robots.ox.ac.uk/~vgg/software/via/)
- [SuperAnnotate image annotation JSON format](https://doc.superannotate.com/docs/vector-json)
