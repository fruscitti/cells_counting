# Phase 2: Desktop GUI - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Cross-platform PySide6 desktop application that replicates all functionality from the Gradio web version: image loading via file dialog, all 9 parameter controls, analysis pipeline (runs in background thread), side-by-side original/annotated image display, manual click-to-count annotation with undo, and clear/reset. Entry point is `app.py` — `main.py` (Gradio web version) stays untouched.

</domain>

<decisions>
## Implementation Decisions

### Visual Style
- **D-01:** System-native Qt look — no custom stylesheet. The app uses the platform's default Qt theme on macOS, Windows, and Linux. Scientific tool; native look is appropriate.

### Analysis Progress UX
- **D-02:** Status label + progress bar. A single progress bar shows overall batch completion (e.g., 2/5 images). A status label shows the current file being processed. Simple and clear.

### Error Display
- **D-03:** Warning row in results table. Failed images appear in the results table with count = 0 and a warning indicator (⚠ Error). User sees all results in one place without popups interrupting the workflow.

### Parameter Panel Layout
- **D-04:** Single vertical list, all visible. All 9 parameter controls stacked in the left panel, always visible. The top-hat sub-controls (Top-Hat Kernel, Adaptive Block, Adaptive C) show/hide via the Use Top-Hat checkbox. No collapsible sections.

### Technical Architecture (from STATE.md)
- **D-05:** QRunnable + QThreadPool for background analysis — UI stays responsive during processing.
- **D-06:** ScaledImageLabel (QLabel subclass) for image display — aspect-ratio-preserving on window resize.
- **D-07:** BGR→RGB conversion + QImage.copy() when converting numpy arrays to QPixmap — prevents segfault.
- **D-08:** Entry point is `app.py` — reuse `process_image()` and `run_analysis()` from `main.py` unchanged.

### Claude's Discretion
- Exact progress bar placement (status bar vs panel area)
- QSpinBox vs slider for blur strength (roadmap specifies QSpinBox with step=2 for odd values)
- Splitter initial ratio between image display and results table
- Window minimum size
- Exact icon/label text for ⚠ error rows

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Processing Core
- `main.py` — Contains `process_image()` (lines 8–25) and `run_analysis()` (lines 28–43) — the functions to reuse. BGR→RGB conversion pattern, parameter signatures, return types.

### Requirements
- `.planning/REQUIREMENTS.md` — Full requirement IDs for Phase 2: APP-01–04, IMG-01–03, PARAM-01–07, ANAL-01–07, MARK-01–03, CLR-01

### Roadmap
- `.planning/ROADMAP.md` — Phase 2 section with detailed plan tasks for Plans 2.1, 2.2, 2.3

### Project Constraints
- `.planning/PROJECT.md` — Stack constraints (Python only, PySide6, uv pip install, local-ui branch)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `process_image(img_bgr, brightness_threshold, min_cell_area, blur_strength, use_cleaning, max_cell_area, use_tophat, tophat_kernel, adaptive_block, adaptive_c)` — Core detection function, returns `(annotated_img_rgb, cell_count)`. Lives in `main.py` lines 8–25.
- `run_analysis(files, ...)` — Batch orchestrator over file list. Can be adapted or replaced with a QRunnable wrapper that emits signals per image.
- `optimize_parameters(image_path)` — Auto-optimize via grid search, returns best parameter dict.

### Established Patterns
- Images are loaded with `cv2.imread()` (returns BGR numpy array). Must convert BGR→RGB before creating QImage: `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`.
- Green channel extraction: `img_bgr[:, :, 1]` — processing operates on single channel.
- Gradio's stateless model (params passed per request) maps well to Qt signals/slots: worker emits `image_ready` and `count_ready` signals.

### Integration Points
- `app.py` imports `process_image` and `optimize_parameters` from `main.py`
- QRunnable worker wraps `process_image()` call, emits results via Qt signals to main thread
- Results table (QTableWidget or QTableView) receives row updates from worker signals
- ScaledImageLabel receives QPixmap updates from worker signals

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard Qt desktop application approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope.

</deferred>

---

*Phase: 02-desktop-gui*
*Context gathered: 2026-03-29*
