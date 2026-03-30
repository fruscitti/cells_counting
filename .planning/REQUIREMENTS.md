# Requirements: Fluorescence Cell Counter — Desktop App

**Defined:** 2026-03-29
**Core Value:** Scientists can analyze fluorescence images offline, save named batches, and return to re-examine or modify sessions without a web browser.

---

## v1 Requirements

### Application Shell

- [x] **APP-01**: Desktop window launches with `python app.py` (separate entry point from `main.py`)
- [x] **APP-02**: Window title shows "Cell Counter" with current batch name when one is open
- [x] **APP-03**: Application runs on Windows, macOS, and Linux without modification
- [x] **APP-04**: High-DPI displays render correctly on Windows (DPI scale policy set before QApplication init)

### Image Loading

- [x] **IMG-01**: User can open images via a file dialog (multi-select, filters: PNG/JPG/TIFF/BMP)
- [x] **IMG-02**: Loaded image filenames are listed in a sidebar/panel
- [x] **IMG-03**: User can select an image from the list to view it in the display area

### Parameter Controls

- [x] **PARAM-01**: Brightness Threshold slider (range 0–255, default 120, step 1)
- [x] **PARAM-02**: Min Cell Area slider (range 1–500 px, default 25, step 1)
- [x] **PARAM-03**: Blur Strength spinbox (range 1–31, default 9, step 2 — enforces odd numbers)
- [x] **PARAM-04**: Max Cell Area slider (range 50–5000 px, default 500, step 10)
- [x] **PARAM-05**: Use Cleaning checkbox (default checked)
- [x] **PARAM-06**: Use Top-Hat checkbox with sub-controls: Top-Hat Kernel (range 10–200, default 50), Adaptive Block (range 3–199 odd, default 99), Adaptive C (range -50–50, default -5) — shown/hidden based on checkbox
- [x] **PARAM-07**: Each slider/spinbox shows its current numeric value next to it

### Analysis

- [x] **ANAL-01**: "Analyze" button runs `process_image()` on all loaded images with current parameters
- [x] **ANAL-02**: Processing runs in a background thread (QRunnable) — UI does not freeze
- [x] **ANAL-03**: Progress is indicated while analysis runs (progress bar or status label)
- [x] **ANAL-04**: Side-by-side display of original and annotated image for the selected image (aspect-ratio preserved, scales with window resize)
- [x] **ANAL-05**: Cell count displayed prominently for the selected image
- [x] **ANAL-06**: Results table shows filename + cell count for all analyzed images
- [x] **ANAL-07**: "Auto-Optimize" button runs grid search on the selected image and updates sliders to best parameters

### Manual Annotation

- [x] **MARK-01**: Click on the annotated image to add a manual mark (green circle + "M{n}" label)
- [x] **MARK-02**: "Undo Mark" button removes the last manual mark
- [x] **MARK-03**: Total count shown = algo count + manual mark count

### Clear / Reset

- [x] **CLR-01**: "Clear" button resets all loaded images, results, and marks; resets parameters to defaults

### Batch Save

- [x] **BATCH-01**: "Save Batch" button opens a dialog to enter a batch name
- [x] **BATCH-02**: Batch is saved as a folder under `batches/<YYYY-MM-DD_name>/` containing:
  - `manifest.json` — schema_version, name, created_at, modified_at, parameters, images list
  - Copies of all original images (`shutil.copy2`)
  - Annotated images as PNG files
- [x] **BATCH-03**: manifest.json `parameters` includes all 9 processing parameters
- [x] **BATCH-04**: manifest.json `images[].manual_marks` stores click coordinates as `[[x,y],...]`
- [x] **BATCH-05**: Atomic save — write to temp file then `os.replace()` to prevent corrupt manifests on crash
- [x] **BATCH-06**: Batch name conflicts are resolved by appending a counter suffix (`name_2`, `name_3`)

### Batch Management

- [x] **BMGR-01**: "Open Batch" button shows a list of saved batches (name + date + image count)
- [x] **BMGR-02**: Opening a batch loads all images and restores last-saved parameters and results
- [x] **BMGR-03**: Missing images in a batch are flagged with a warning icon in the list (status computed at load time, not persisted)
- [x] **BMGR-04**: "Add Images" button (when batch is open) opens file dialog and copies new images into the batch folder, updating the manifest
- [x] **BMGR-05**: "Remove Image" button removes selected image from the manifest (file stays on disk — no data loss)
- [x] **BMGR-06**: "Re-Analyze" button re-runs `process_image()` on all batch images with current parameters; preserves `manual_marks`; overwrites `cell_count` and annotated images
- [x] **BMGR-07**: "Export CSV" button saves a CSV file (`<batch_name>_results.csv`) with filename + cell count + algo count + manual count columns

---

## v2 Requirements

### Comparison

- **COMP-01**: Side-by-side comparison of two batches (same images, different parameters)
- **COMP-02**: Delta view showing count changes between original analysis and re-analysis

### UI Polish

- **UI-01**: Zoom/pan on displayed images (QGraphicsView)
- **UI-02**: Keyboard shortcut to step through images in the list
- **UI-03**: Drag-and-drop image loading

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Replacing Gradio web version | Web version stays in `main` branch; this is additive work in `local-ui` branch |
| SQLite database | Folder + JSON is simpler, portable, no dependency; SQLite adds no value at this scale |
| Cloud sync | Local-only tool; networking is out of scope |
| Real-time parameter preview | Analysis on large images takes seconds; live preview would feel laggy |
| `send2trash` for batch deletion | Not in v1 scope; remove-from-manifest is safer |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| APP-01–04 | Phase 1 | Pending |
| IMG-01–03 | Phase 1 | Pending |
| PARAM-01–07 | Phase 1 | Pending |
| ANAL-01–07 | Phase 1 | Pending |
| MARK-01–03 | Phase 1 | Pending |
| CLR-01 | Phase 1 | Complete |
| BATCH-01–06 | Phase 2 | Pending |
| BMGR-01–07 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 after initialization*
