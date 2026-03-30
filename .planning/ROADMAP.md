# Roadmap

## Milestone: v1.0 — Fluorescence Cell Counter Web App

> Existing working app. Using GSD quick mode for incremental improvements.

| Phase | Name | Status |
|-------|------|--------|
| 1 | Web UI (existing) | ✓ Complete |

---

## Milestone: v2.0 — Desktop App + Batch Management

**Branch:** `local-ui`
**Created:** 2026-03-29

| Phase | Name | Plans | Status | Goal |
|-------|------|-------|--------|------|
| 2 | Desktop GUI | 3/3 | Complete   | 2026-03-30 |
| 3 | Batch Management | 2/2 | Complete   | 2026-03-30 |

---

### Phase 2 — Desktop GUI

**Goal:** A cross-platform PySide6 desktop application that replicates all functionality from the Gradio web version: image loading, all parameter controls, analysis pipeline, side-by-side display, manual annotation, and clear/reset.

**Entry criteria:** `local-ui` branch created, PySide6 installed in `.venv`

**Exit criteria:**
- `python app.py` launches a desktop window on all three platforms
- All parameter controls (9 parameters) present and functional
- Analyze button processes all loaded images in background thread; UI stays responsive
- Side-by-side original/annotated display scales with window resize
- Auto-optimize updates sliders from selected image
- Manual click-to-count with undo works
- Clear resets to defaults
- Results table shows all filenames + counts

**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md — App Scaffold + Image Display
- [x] 02-02-PLAN.md — Parameter Controls + Analysis Engine
- [x] 02-03-PLAN.md — Manual Annotation + Clear + Polish

#### Plan 2.1 — App Scaffold + Image Display

**Covers:** APP-01–04, IMG-01–03, ANAL-04–05

**Tasks:**
1. Install PySide6 via `uv pip install PySide6`
2. Create `app.py` entry point with `QApplication` (DPI policy, theme)
3. Build main window skeleton: left control panel + right splitter for image + table
4. Implement `ScaledImageLabel` (QLabel subclass, aspect-ratio-preserving on resize)
5. Build side-by-side image layout (original | annotated) with ScaledImageLabel
6. Implement file-open dialog (multi-select, image filters) + image list widget
7. Connect image list selection → display selected image pair

#### Plan 2.2 — Parameter Controls + Analysis Engine

**Covers:** PARAM-01–07, ANAL-01–03, ANAL-06–07

**Tasks:**
1. Build parameter panel: sliders + QSpinBox for blur (step=2, odd values) with live value labels
2. Add top-hat section (collapsed by default, revealed by checkbox)
3. Wire "Analyze" button → QRunnable worker that calls `process_image()` from `main.py`
4. Emit signals from worker thread → update image display and results table in main thread
5. Add progress bar / status label during analysis
6. Implement auto-optimize worker (calls `optimize_parameters()`) → updates sliders on completion

#### Plan 2.3 — Manual Annotation + Clear + Polish

**Covers:** MARK-01–03, CLR-01, ANAL-04 (click on image), APP-02

**Tasks:**
1. Make annotated `ScaledImageLabel` clickable: map click coords back to original image space
2. Call `draw_manual_marks()` and refresh display on each click
3. Add "Undo Mark" button: pop last click, redraw
4. Display total count = algo + manual marks
5. Implement "Clear" button: reset all state, file list, results, parameters to defaults
6. Window title updates to show loaded file count or batch name
7. Manual testing pass on macOS; smoke test on Windows/Linux paths if available

---

### Phase 3 — Batch Management

**Goal:** Users can save a named analysis session to a folder, reopen it later, add or remove images, re-run analysis with different parameters (preserving manual marks), and export results to CSV.

**Entry criteria:** Phase 2 verified — full analysis UI works

**Exit criteria:**
- "Save Batch" creates `batches/<date_name>/` with manifest.json and image copies
- "Open Batch" loads an existing batch, restores images, results, and parameters
- "Re-Analyze" re-runs processing on all batch images, preserves manual_marks
- "Add Images" / "Remove Image" correctly update manifest
- "Export CSV" writes a valid CSV with all columns
- Missing images in a batch show a warning, don't crash

**Plans:** 2/2 plans complete

Plans:
- [x] 03-01-PLAN.md — Batch Save + Open (BatchManager module + Save/Open UI)
- [x] 03-02-PLAN.md — Re-Analyze + Add/Remove + Export CSV

#### Plan 3.1 — Batch Save + Open

**Covers:** BATCH-01–06, BMGR-01–03

**Tasks:**
1. Create `batch_manager.py` module: `BatchManager` class wrapping all folder/manifest I/O
2. Implement `save_batch(name, images, params, results)`: folder creation, image copy, manifest write (atomic)
3. Manifest schema v1: `schema_version`, `name`, `created_at`, `modified_at`, `parameters` (all 9), `images[]` (filename, original_filename, annotated_filename, cell_count, manual_marks, analyzed_at)
4. Implement `list_batches()`: scan `batches/` folder, return sorted list with metadata
5. Implement `load_batch(path)`: read manifest, check image presence (compute `status` at load time), return structured data
6. Add "Save Batch" button + name dialog to main window
7. Add "Open Batch" button + batch-list dialog (shows name, date, image count, missing-file warning)
8. On batch open: populate image list, restore parameters, display results

#### Plan 3.2 — Re-Analyze + Add/Remove + Export

**Covers:** BMGR-04–07

**Tasks:**
1. "Add Images" button: open file dialog → `batch_manager.add_images()` copies files, updates manifest
2. "Remove Image" button: `batch_manager.remove_image()` removes entry from manifest only (no file delete)
3. "Re-Analyze" button: re-run `process_image()` on all batch images with current params; update cell_count + annotated files; preserve manual_marks; update manifest (modified_at, parameters)
4. "Export CSV" button: build DataFrame from manifest images list → `batch_name_results.csv`
5. UI state management: disable save/add/remove/re-analyze buttons when no batch is open
6. Edge case: handle batch images with `status: missing` during re-analyze (skip + warn)

---
*Roadmap created: 2026-03-29*
*Branch: local-ui (created before Phase 2 execution)*
