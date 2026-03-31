# Fluorescence Cell Counter

A desktop application for counting fluorescent cells in microscopy images. Load images, tune detection parameters with live sliders, and get annotated results with cell counts — no coding required.

---

## Features

- **Batch sessions** — load multiple images into a named batch, save and reopen them later
- **Live parameter tuning** — sliders update detection in real time, no re-run needed
- **Auto-Optimize** — grid search finds the most stable parameter set for your image
- **Clump splitting** — watershed algorithm separates touching cells
- **Flat-field correction** — top-hat filter + adaptive threshold handles uneven illumination backgrounds
- **Manual annotation** — click on the image to add or remove cell marks the algorithm missed
- **Side-by-side view** — compare original and annotated images at the same zoom level
- **Export CSV** — one-click export of cell counts per image
- **Zoom & pan** — mouse wheel zoom, click-drag pan on both image panels

---

## Installation

### Windows — Installer (recommended for non-technical users)

1. Go to the [Releases page](https://github.com/fruscitti/cells_counting/releases)
2. Download `CellCounterInstaller.exe` from the latest release
3. Run the installer — it will add **Cell Counter** to your Start Menu
4. Launch it from Start Menu → Cell Counter

> The installer bundles Python and all dependencies. No separate Python installation required.

### macOS / Linux — From source

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/fruscitti/cells_counting.git
cd cells_counting
uv venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install PySide6 opencv-python pandas numpy
python app.py
```

---

## Usage

### 1. Load images

Use **File → Open Images** (or the toolbar button) to load one or more `.tif`, `.tiff`, `.png`, or `.jpg` files. Images appear in the list on the left.

### 2. Analyze

Click **Analyze** to run detection on all loaded images. The annotated result appears on the right with red circles marking detected cells and a running count.

### 3. Tune parameters

Adjust the sliders in the left panel and click **Re-Analyze** to reprocess with new settings. Use **Auto-Optimize** to let the app find a stable starting point for your image automatically.

### 4. Manual corrections

Click anywhere on the annotated image to add a manual mark (shown in green). Click an existing mark to remove it. The total count updates immediately.

### 5. Save a batch

Use **File → Save Batch** to save your images, parameters, counts, and manual marks to a named folder. Reopen it later with **File → Open Batch** to continue where you left off.

### 6. Export results

**File → Export CSV** saves a `cell_counts_report.csv` with one row per image (filename, algorithm count, manual marks, total).

---

## Detection Pipeline

The pipeline runs on the **green channel** of each image, where fluorescent cells appear brightest.

### Step 1 — Green channel extraction

Fluorescence signal is strongest in the green channel of the BGR image. Isolating it reduces interference from background autofluorescence in red and blue channels.

### Step 2 — Gaussian blur

A Gaussian blur (`Blur Strength × Blur Strength` kernel) smooths local noise and merges nearby bright pixels that belong to the same cell into a single connected region. Larger values merge split cells; smaller values preserve fine detail.

### Step 3 — Thresholding

Two modes, selectable via **Flat-Field Correction**:

- **Global threshold (off):** All pixels above `Brightness Threshold` are set to white. Simple and fast; works well when background illumination is uniform.
- **Flat-field correction (on):** A two-step approach for uneven illumination:
  1. **Top-hat morphological filter** — subtracts the local background by computing `image − morphological_opening(image, ellipse_kernel)`. The `Top-Hat Kernel` size controls how broad a background gradient is removed; set it larger than the largest cell.
  2. **Adaptive Gaussian threshold** — thresholds each pixel relative to its local neighbourhood (`Adaptive Block Size` × `Adaptive Block Size`). The `Adaptive Constant C` shifts the threshold; more negative values are stricter (fewer false positives).

### Step 4 — Speckle cleaning (optional)

A 3×3 morphological opening (`erosion → dilation`) removes isolated bright pixels that are smaller than the structuring element. Enable **Speckle Cleaning** when images contain salt-and-pepper noise.

### Step 5 — Connected-component labelling

`cv2.connectedComponentsWithStats` groups the remaining white pixels into labelled blobs. Blobs smaller than `Min Cell Area` are discarded as debris.

### Step 6 — Clump splitting (watershed)

Blobs larger than `Max Cell Area` are likely clumps of touching cells. Each oversized blob is processed independently:

1. **Distance transform** — computes each pixel's distance to the nearest background pixel, creating a height map with local peaks at cell centres.
2. **Sure foreground** — pixels above 50 % of the peak distance become seed markers, one per cell.
3. **Watershed** — floods from the seed markers outward, stopping where adjacent floods meet. This draws boundaries between touching cells.
4. Each separated region contributes one centroid to the count.

### Step 7 — Visualisation

A red circle (radius 18 px) and an index number are drawn on a copy of the original image at each detected centroid. Manual marks are drawn in green (`M1`, `M2`, …).

---

## Parameters

| Parameter | Default | Range | Effect |
|---|---|---|---|
| Brightness Threshold | 120 | 0 – 255 | Global threshold level; higher ignores dimmer spots |
| Min Cell Area | 25 px | 1 – 500 | Blobs below this area are discarded as debris |
| Max Cell Area | 500 px | 50 – 5000 | Blobs above this are split by watershed |
| Blur Strength | 9 | 1 – 31 (odd) | Gaussian kernel size; larger merges split cells |
| Speckle Cleaning | On | on/off | Morphological opening removes isolated noise pixels |
| Flat-Field Correction | On | on/off | Enables top-hat + adaptive threshold for uneven backgrounds |
| Top-Hat Kernel | 50 | 10 – 200 | Ellipse size for background subtraction; should exceed largest cell |
| Adaptive Block Size | 99 | 3 – 299 (odd) | Local neighbourhood for adaptive threshold; ~1–2 cell diameters |
| Adaptive Constant C | −5 | −20 – 0 | Threshold offset; more negative = stricter |

---

## Building the Windows Installer

The installer is produced by a GitHub Actions workflow triggered manually:

1. Go to **Actions → Build Windows Installer → Run workflow**
2. Enter a version string (e.g. `v1.1.0`)
3. The workflow builds with PyInstaller + NSIS on a `windows-2022` runner and publishes a GitHub Release with `CellCounterInstaller.exe` attached (~120–150 MB)

Build scripts are in `releases/windows/`:
- `cell_counter.spec` — PyInstaller spec (bundles PySide6, OpenCV, NumPy, pandas)
- `installer.nsi` — NSIS MUI2 installer script

---

## Stack

| Component | Library |
|---|---|
| Desktop GUI | [PySide6](https://doc.qt.io/qtforpython/) (Qt 6) |
| Image processing | [OpenCV](https://opencv.org/) |
| Array operations | [NumPy](https://numpy.org/) |
| Results export | [pandas](https://pandas.pydata.org/) |
| Packaging | [PyInstaller](https://pyinstaller.org/) + [NSIS](https://nsis.sourceforge.io/) |
