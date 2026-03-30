# Phase 2: Desktop GUI - Research

**Researched:** 2026-03-29
**Domain:** PySide6 desktop GUI with background threading, image display, and interactive annotation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** System-native Qt look — no custom stylesheet. Platform default Qt theme on macOS, Windows, and Linux.
- **D-02:** Status label + progress bar for analysis progress. Progress bar shows batch completion (e.g., 2/5 images). Status label shows current file.
- **D-03:** Warning row in results table for failed images. Count = 0 and "⚠ Error" indicator. No popups.
- **D-04:** Single vertical list, all 9 parameter controls always visible. Top-hat sub-controls (Top-Hat Kernel, Adaptive Block, Adaptive C) show/hide via Use Top-Hat checkbox. No collapsible sections.
- **D-05:** QRunnable + QThreadPool for background analysis — UI stays responsive during processing.
- **D-06:** ScaledImageLabel (QLabel subclass) for image display — aspect-ratio-preserving on window resize.
- **D-07:** BGR→RGB conversion + QImage.copy() when converting numpy arrays to QPixmap — prevents segfault.
- **D-08:** Entry point is `app.py` — reuse `process_image()` and `run_analysis()` from `main.py` unchanged.

### Claude's Discretion

- Exact progress bar placement (status bar vs panel area)
- QSpinBox vs slider for blur strength (roadmap specifies QSpinBox with step=2 for odd values)
- Splitter initial ratio between image display and results table
- Window minimum size
- Exact icon/label text for error rows

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 2 scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| APP-01 | Desktop window launches with `python app.py` | QApplication + QMainWindow pattern documented |
| APP-02 | Window title shows "Cell Counter" with batch name | `setWindowTitle()` method on QMainWindow |
| APP-03 | Runs on Windows, macOS, Linux without modification | PySide6 is cross-platform; no platform-specific code needed |
| APP-04 | High-DPI displays render correctly (DPI policy before QApp init) | Qt6 enables HiDPI by default; `QApplication.setHighDpiScaleFactorRoundingPolicy()` still recommended on Windows |
| IMG-01 | Open images via file dialog (multi-select, PNG/JPG/TIFF/BMP) | `QFileDialog.getOpenFileNames()` with filter string |
| IMG-02 | Loaded image filenames listed in sidebar | `QListWidget` for file list |
| IMG-03 | Select image from list to view in display area | `QListWidget.currentItemChanged` signal |
| PARAM-01 | Brightness Threshold slider (0–255, default 120, step 1) | `QSlider` + `QLabel` for value display |
| PARAM-02 | Min Cell Area slider (1–500, default 25, step 1) | `QSlider` + `QLabel` for value display |
| PARAM-03 | Blur Strength spinbox (1–31, default 9, step 2, odd only) | `QSpinBox` with `setSingleStep(2)`, odd starting value |
| PARAM-04 | Max Cell Area slider (50–5000, default 500, step 10) | `QSlider` + `QLabel` for value display |
| PARAM-05 | Use Cleaning checkbox (default checked) | `QCheckBox` |
| PARAM-06 | Use Top-Hat checkbox with show/hide sub-controls | `QCheckBox` + `QWidget` container with `setVisible()` |
| PARAM-07 | Each control shows current numeric value next to it | `QLabel` wired to slider `valueChanged` signal |
| ANAL-01 | Analyze button runs `process_image()` on all images | Worker pattern described below |
| ANAL-02 | Processing runs in background thread (QRunnable) | WorkerSignals + QRunnable pattern documented |
| ANAL-03 | Progress indicated during analysis | `QProgressBar` + status `QLabel` |
| ANAL-04 | Side-by-side display, aspect-ratio preserved, scales on resize | `ScaledImageLabel` subclass with `paintEvent` override |
| ANAL-05 | Cell count displayed prominently for selected image | `QLabel` updated from worker signal |
| ANAL-06 | Results table shows filename + cell count for all images | `QTableWidget` with 2 columns |
| ANAL-07 | Auto-Optimize button runs grid search, updates sliders | Second QRunnable worker wrapping `optimize_parameters()` |
| MARK-01 | Click annotated image to add manual mark (green circle + M{n}) | Override `mousePressEvent` on ScaledImageLabel, map coords |
| MARK-02 | Undo Mark button removes last manual mark | Pop from list, redraw via `draw_manual_marks()` |
| MARK-03 | Total count = algo count + manual mark count | Integer addition, update displayed QLabel |
| CLR-01 | Clear button resets all state to defaults | Reset all widget values, clear internal state dicts |
</phase_requirements>

---

## Summary

Phase 2 builds a PySide6 desktop application (`app.py`) that delivers full feature parity with the existing Gradio web version. All image processing logic lives in `main.py` and is imported unchanged. The Qt layer wraps processing in a `QRunnable` worker that emits per-image signals, keeping the UI responsive during batch analysis.

The key technical challenge is the image display pipeline: numpy arrays from OpenCV (BGR) must be converted to RGB, then to `QImage` with explicit `bytes_per_line` and a `.copy()` call to prevent garbage-collection segfaults, then to `QPixmap` for display. The `ScaledImageLabel` (a `QLabel` subclass overriding `resizeEvent` + `paintEvent`) handles aspect-ratio-preserving display that responds to window resize.

Manual click-to-count requires coordinate mapping from label space back to original image space — the click position relative to the label must account for letterbox padding introduced by aspect-ratio scaling. This is a non-obvious calculation that must be handled correctly.

**Primary recommendation:** Use the `WorkerSignals` + `QRunnable` pattern from pythonguis.com for background threading. Use `ScaledImageLabel` with `paintEvent` override for image display. Use `QImage(array.data, w, h, bpl, Format_RGB888).copy()` for safe numpy-to-pixmap conversion.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.0 | Qt for Python GUI framework | LGPL, official Qt binding, cross-platform |
| opencv-python | 4.13.0 (installed) | Image loading, BGR→RGB conversion, annotation drawing | Already in project, established |
| numpy | installed | Array representation for images | Already in project |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-qt | 4.5.0 | Qt-aware pytest fixtures (qtbot, waitSignal) | Wave 0 test infrastructure |
| pytest | latest | Test runner | Wave 0 test infrastructure |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| QRunnable + WorkerSignals | QThread subclass | QThread is heavier; QRunnable with signals is the recommended modern pattern |
| ScaledImageLabel (paintEvent) | QGraphicsView | QGraphicsView supports zoom/pan (v2 req) but is significantly more complex; ScaledImageLabel is correct for v1 |
| QTableWidget | QTableView + model | QTableWidget is simpler for fixed 2-column result display |

**Installation:**
```bash
uv pip install PySide6
uv pip install pytest pytest-qt
```

**Version verification (confirmed against PyPI registry, 2026-03-29):**
- PySide6: 6.11.0
- pytest-qt: 4.5.0
- opencv-python: 4.13.0 (already installed in .venv)

---

## Architecture Patterns

### Recommended Project Structure

```
celulas/
├── app.py                  # Entry point — QApplication + MainWindow
├── main.py                 # Untouched — process_image(), draw_manual_marks(), optimize_parameters()
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # MainWindow class
│   ├── scaled_image_label.py  # ScaledImageLabel subclass
│   ├── param_panel.py      # Parameter controls widget
│   └── results_table.py    # QTableWidget wrapper
├── workers/
│   ├── __init__.py
│   ├── analysis_worker.py  # QRunnable + WorkerSignals for process_image()
│   └── optimize_worker.py  # QRunnable + WorkerSignals for optimize_parameters()
└── tests/
    ├── conftest.py
    ├── test_scaled_image_label.py
    ├── test_analysis_worker.py
    ├── test_param_panel.py
    └── test_coordinate_mapping.py
```

### Pattern 1: WorkerSignals + QRunnable

**What:** Signals container as a separate QObject, attached to a QRunnable for cross-thread communication.
**When to use:** Any background operation that needs to report results or progress back to the GUI thread.

```python
# Source: https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/
from PySide6.QtCore import QObject, QRunnable, Signal, Slot

class AnalysisSignals(QObject):
    image_done = Signal(str, object, int)   # filename, annotated_rgb_array, count
    progress = Signal(int, int)             # current, total
    error = Signal(str, str)                # filename, error_message
    finished = Signal()

class AnalysisWorker(QRunnable):
    def __init__(self, file_paths, params):
        super().__init__()
        self.file_paths = file_paths
        self.params = params
        self.signals = AnalysisSignals()

    @Slot()
    def run(self):
        for i, path in enumerate(self.file_paths):
            try:
                img_bgr = cv2.imread(path)
                ann_bgr, count = process_image(img_bgr, **self.params)
                ann_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)
                self.signals.image_done.emit(os.path.basename(path), ann_rgb, count)
            except Exception as e:
                self.signals.error.emit(os.path.basename(path), str(e))
            self.signals.progress.emit(i + 1, len(self.file_paths))
        self.signals.finished.emit()
```

### Pattern 2: Safe numpy-to-QPixmap Conversion

**What:** Convert a numpy RGB uint8 array to QPixmap without segfault.
**When to use:** Every time you display an OpenCV image in Qt.

```python
# Source: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html
# Source: https://medium.com/@bgallois/numpy-ndarray-qimage-beware-the-trap-52dcbe7388b9
from PySide6.QtGui import QImage, QPixmap
import numpy as np

def numpy_rgb_to_pixmap(rgb_array: np.ndarray) -> QPixmap:
    """Convert H x W x 3 uint8 RGB array to QPixmap. Thread-safe via .copy()."""
    h, w, ch = rgb_array.shape
    assert ch == 3 and rgb_array.dtype == np.uint8
    bytes_per_line = ch * w
    # .copy() transfers pixel data ownership to Qt — numpy array can be GC'd safely
    qimg = QImage(rgb_array.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)
```

### Pattern 3: ScaledImageLabel

**What:** QLabel subclass that scales its pixmap to fill available space while preserving aspect ratio.
**When to use:** Any image display that should resize with the window.

```python
# Source: https://www.codeflamingo.eu/blog/aspectratio-qpixmap/
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter

class ScaledImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setMinimumSize(1, 1)
        self.setAlignment(Qt.AlignCenter)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter = QPainter(self)
        painter.drawPixmap(x, y, scaled)
```

### Pattern 4: Click Coordinate Mapping (ScaledImageLabel)

**What:** Map a mouse click on the scaled+letterboxed label back to original image pixel coordinates.
**When to use:** Manual click-to-count annotation (MARK-01).

```python
def mousePressEvent(self, event):
    if self._pixmap is None or not self._click_enabled:
        return
    # Compute the rectangle occupied by the scaled pixmap within the label
    scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    x_offset = (self.width() - scaled.width()) // 2
    y_offset = (self.height() - scaled.height()) // 2
    # Click position relative to the image (not the label)
    img_x = event.position().x() - x_offset
    img_y = event.position().y() - y_offset
    # Reject clicks outside the image rect
    if img_x < 0 or img_y < 0 or img_x >= scaled.width() or img_y >= scaled.height():
        return
    # Scale back to original pixel coords
    orig_x = int(img_x * self._pixmap.width() / scaled.width())
    orig_y = int(img_y * self._pixmap.height() / scaled.height())
    self.clicked.emit(orig_x, orig_y)
```

### Pattern 5: QSpinBox with Odd-Only Enforcement

**What:** Blur strength requires odd values (kernel size constraint in OpenCV GaussianBlur).
**When to use:** PARAM-03.

```python
# Source: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSpinBox.html
class OddSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(1)
        self.setMaximum(31)
        self.setSingleStep(2)
        self.setValue(9)    # default odd value

    def stepBy(self, steps):
        super().stepBy(steps)
        # Ensure value stays odd after any change
        if self.value() % 2 == 0:
            self.setValue(self.value() + 1)
```

### Pattern 6: High-DPI on Windows

**What:** Ensure correct rendering on Windows HiDPI screens.
**When to use:** APP-04 — must be set before QApplication is created.

```python
# Source: Qt6 built-in HiDPI; rounding policy still recommended on Windows
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

if sys.platform == "win32":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
app = QApplication(sys.argv)
```

Note: `Qt.AA_EnableHighDpiScaling` is DEPRECATED in Qt6/PySide6. HiDPI is enabled by default. Only the rounding policy needs explicit setting on Windows.

### Anti-Patterns to Avoid

- **setScaledContents(True) on QLabel:** Does NOT preserve aspect ratio — stretches the image. Use the paintEvent approach instead.
- **Emitting signals from non-QObject QRunnable:** QRunnable does not inherit QObject. Signals MUST be defined on a separate QObject (WorkerSignals). Attempting to add signals directly to QRunnable will fail silently or raise AttributeError.
- **Passing numpy array directly to QImage without .copy():** The array can be garbage-collected while QImage holds a raw pointer, causing a segfault. Always call `.copy()` on the QImage or keep a reference to the array alive.
- **Blocking the main thread with cv2.imread in a signal handler:** All image I/O and processing must happen in the worker thread, not in slot callbacks.
- **Creating QApplication inside a test without pytest-qt:** Results in "QApplication already exists" errors or segfaults. Use the `qtbot` fixture from pytest-qt.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Background threading | Custom threading.Thread wrapper | QRunnable + QThreadPool | Thread pool management, Qt event loop integration, signal safety |
| Image aspect-ratio scaling | Manual math in resize handler | ScaledImageLabel with paintEvent | Handles all edge cases (empty pixmap, very small widget) |
| numpy-to-Qt conversion | Custom byte manipulation | QImage(array.data, w, h, bpl, Format_RGB888).copy() | Alignment, stride, memory ownership all handled |
| Odd-value enforcement | Input validation on every value change | OddSpinBox subclass with stepBy override | Single responsibility, handles keyboard entry too |

**Key insight:** PySide6 has well-established patterns for every problem in this phase. The non-obvious ones (coordinate mapping, QRunnable signals) have authoritative tutorials and minimal custom code.

---

## Common Pitfalls

### Pitfall 1: QRunnable Signals Pattern

**What goes wrong:** Developer adds `Signal()` directly to the `QRunnable` subclass, which silently fails because QRunnable does not inherit QObject.
**Why it happens:** PyQt/PySide signals look like class attributes; the missing QObject inheritance isn't obvious.
**How to avoid:** Always create a separate `WorkerSignals(QObject)` class. Attach it as `self.signals = WorkerSignals()` inside the QRunnable `__init__`.
**Warning signs:** No errors thrown, but signals never fire. Slots are never called.

### Pitfall 2: Segfault from numpy buffer GC

**What goes wrong:** App crashes with a segfault when displaying an image.
**Why it happens:** `QImage(array.data, ...)` holds a raw C pointer to numpy's buffer. If the numpy array goes out of scope (end of function, reassignment), Python GC frees it while Qt still holds the pointer.
**How to avoid:** Always call `.copy()` on the QImage immediately: `QImage(...).copy()`. This transfers pixel ownership to Qt.
**Warning signs:** Works sometimes, crashes other times (race condition with GC). More frequent in tight loops.

### Pitfall 3: Click coordinates off by letterbox offset

**What goes wrong:** Manual marks appear in the wrong position on the original image.
**Why it happens:** When an image is displayed with aspect-ratio padding (letterboxing), the click position on the label includes the padding offset. Not subtracting the offset before scaling back gives wrong coordinates.
**How to avoid:** Always subtract the letterbox offset `(label_width - scaled_width) // 2` from click X before scaling back. Reject clicks outside the image rect.
**Warning signs:** Marks drift toward the center of the image; marks near edges appear outside the image.

### Pitfall 4: OddSpinBox keyboard entry

**What goes wrong:** User types "10" into the blur spinbox; an even value is submitted to OpenCV, causing a crash in `cv2.GaussianBlur`.
**Why it happens:** `setSingleStep(2)` only applies to arrow key / scroll steps, not to direct keyboard entry.
**How to avoid:** Override `validate()` or `stepBy()` in the subclass. At minimum, clamp to odd in the `valueChanged` handler before passing to `process_image()`: `v if v % 2 == 1 else v + 1`.
**Warning signs:** OpenCV raises `cv2.error` with "kernel size must be positive and odd".

### Pitfall 5: Progress bar update from worker thread

**What goes wrong:** Intermittent crashes or "QObject::setParent: Cannot set parent from a different thread" warnings.
**Why it happens:** Directly calling `progress_bar.setValue()` from the worker thread is not thread-safe in Qt.
**How to avoid:** Emit a signal from the worker; connect it to the progress bar's `setValue` slot. Qt's queued connection ensures the update runs in the main thread.
**Warning signs:** Crashes only under load (multiple images); works fine with a single image.

---

## Runtime State Inventory

Step 2.5: SKIPPED — Phase 2 is greenfield (new `app.py`). No rename/refactor/migration involved.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All | Yes | 3.12.11 | — |
| uv | Package install | Yes | 0.8.10 | pip directly |
| opencv-python | Image processing | Yes (in .venv) | 4.13.0 | — |
| numpy | Array ops | Yes (in .venv) | via gradio deps | — |
| PySide6 | GUI framework | No | — | Must install |
| pytest | Test runner | No | — | Must install |
| pytest-qt | Qt test fixtures | No | — | Must install |

**Missing dependencies with no fallback:**
- PySide6 6.11.0 — install in Wave 0: `uv pip install PySide6`

**Missing dependencies with fallback:**
- pytest / pytest-qt — needed for Nyquist validation; install in Wave 0: `uv pip install pytest pytest-qt`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-qt 4.5.0 |
| Config file | `pytest.ini` — Wave 0 gap |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APP-01 | `python app.py` launches window | smoke | `pytest tests/test_app_launch.py -x` | Wave 0 gap |
| APP-04 | HiDPI policy set before QApp | unit | `pytest tests/test_app_launch.py::test_highdpi_policy -x` | Wave 0 gap |
| IMG-01 | File dialog filter string correct | unit | `pytest tests/test_main_window.py::test_file_filter -x` | Wave 0 gap |
| IMG-02 | Loaded files appear in list widget | unit | `pytest tests/test_main_window.py::test_image_list -x` | Wave 0 gap |
| IMG-03 | List selection updates displayed image | unit | `pytest tests/test_main_window.py::test_image_selection -x` | Wave 0 gap |
| PARAM-01 | Brightness slider range + default | unit | `pytest tests/test_param_panel.py::test_brightness_slider -x` | Wave 0 gap |
| PARAM-03 | Blur spinbox odd enforcement | unit | `pytest tests/test_param_panel.py::test_blur_odd_enforcement -x` | Wave 0 gap |
| PARAM-06 | Top-hat sub-controls visibility toggle | unit | `pytest tests/test_param_panel.py::test_tophat_visibility -x` | Wave 0 gap |
| PARAM-07 | Value labels update on slider move | unit | `pytest tests/test_param_panel.py::test_value_labels -x` | Wave 0 gap |
| ANAL-02 | Analysis does not freeze UI | integration | `pytest tests/test_analysis_worker.py::test_background_thread -x` | Wave 0 gap |
| ANAL-04 | ScaledImageLabel preserves aspect ratio | unit | `pytest tests/test_scaled_image_label.py::test_aspect_ratio -x` | Wave 0 gap |
| MARK-01 | Click coords map correctly to image space | unit | `pytest tests/test_coordinate_mapping.py::test_click_mapping -x` | Wave 0 gap |
| MARK-02 | Undo removes last mark | unit | `pytest tests/test_coordinate_mapping.py::test_undo_mark -x` | Wave 0 gap |
| MARK-03 | Total count = algo + manual | unit | `pytest tests/test_main_window.py::test_total_count -x` | Wave 0 gap |
| CLR-01 | Clear resets all state to defaults | unit | `pytest tests/test_main_window.py::test_clear_resets -x` | Wave 0 gap |
| D-07 | numpy-to-pixmap does not segfault | unit | `pytest tests/test_scaled_image_label.py::test_pixmap_conversion -x` | Wave 0 gap |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ -x -q` (run quick suite)
- **Per wave merge:** `python -m pytest tests/ -v` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/conftest.py` — shared fixtures (sample image array, app instance via qtbot)
- [ ] `tests/test_app_launch.py` — covers APP-01, APP-04
- [ ] `tests/test_main_window.py` — covers IMG-01–03, MARK-03, CLR-01
- [ ] `tests/test_param_panel.py` — covers PARAM-01–07
- [ ] `tests/test_analysis_worker.py` — covers ANAL-02, ANAL-03
- [ ] `tests/test_scaled_image_label.py` — covers ANAL-04, D-07
- [ ] `tests/test_coordinate_mapping.py` — covers MARK-01, MARK-02
- [ ] `pytest.ini` — configure qt_api = pyside6
- [ ] Framework install: `uv pip install pytest pytest-qt`

---

## Code Examples

### Minimal app.py entry point

```python
# Source: https://doc.qt.io/qtforpython-6/
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

if sys.platform == "win32":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

app = QApplication(sys.argv)
window = MainWindow()
window.setWindowTitle("Cell Counter")
window.show()
sys.exit(app.exec())
```

### Main window skeleton

```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QListWidget, QTableWidget, QPushButton, QProgressBar, QLabel
)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1024, 700)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left panel: param controls + action buttons
        left_panel = QWidget()
        left_panel.setFixedWidth(260)
        # ... param panel, analyze button, etc.

        # Right side: vertical splitter for image area + results table
        right_splitter = QSplitter(Qt.Vertical)
        image_area = QWidget()  # contains side-by-side ScaledImageLabels
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["File", "Cell Count"])
        right_splitter.addWidget(image_area)
        right_splitter.addWidget(self.results_table)
        right_splitter.setSizes([500, 200])  # Claude's discretion

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_splitter, 1)
```

### Worker launch pattern

```python
from PySide6.QtCore import QThreadPool

def on_analyze_clicked(self):
    params = self._collect_params()
    worker = AnalysisWorker(self._file_paths, params)
    worker.signals.image_done.connect(self._on_image_done)
    worker.signals.progress.connect(self._update_progress)
    worker.signals.error.connect(self._on_image_error)
    worker.signals.finished.connect(self._on_analysis_finished)
    self._progress_bar.setMaximum(len(self._file_paths))
    self._progress_bar.setValue(0)
    QThreadPool.globalInstance().start(worker)
```

### pytest-qt conftest

```python
# Source: https://pytest-qt.readthedocs.io/en/latest/intro.html
import numpy as np
import pytest

@pytest.fixture
def sample_rgb_array():
    """200x300 RGB uint8 test image."""
    return np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)

@pytest.fixture
def main_window(qtbot):
    from ui.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    return w
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `Qt.AA_EnableHighDpiScaling` attribute | Built-in HiDPI in Qt6 | Qt6 release (2020) | Do NOT set this attribute in PySide6 — it's deprecated and may warn |
| QThread subclass for background work | QRunnable + QThreadPool | Qt5 era | QRunnable + pool is lighter; QThread is still valid but heavier |
| `setScaledContents(True)` | `paintEvent` override with `Qt.KeepAspectRatio` | PyQt/PySide era | setScaledContents stretches — never use for aspect-ratio display |

**Deprecated/outdated:**
- `Qt.AA_EnableHighDpiScaling`: Deprecated in Qt6. Remove from any old code.
- `QRunnable.signals = Signal(...)`: Invalid. Signals on QRunnable don't work. Use separate QObject.

---

## Open Questions

1. **PySide6 packaging size on macOS**
   - What we know: PySide6 6.11.0 is a large package (~200 MB installed). The `.venv` size will grow significantly.
   - What's unclear: Whether `PySide6-Essentials` alone (without Addons) is sufficient for this phase.
   - Recommendation: Install full `PySide6` first; if CI/distribution is needed, narrow to Essentials later.

2. **pytest-qt on macOS with no display**
   - What we know: pytest-qt supports headless testing via offscreen platform plugin.
   - What's unclear: Whether macOS requires `QT_QPA_PLATFORM=offscreen` for CI runs.
   - Recommendation: Add `QT_QPA_PLATFORM=offscreen` to the pytest.ini or conftest.py if tests fail in headless mode.

---

## Project Constraints (from CLAUDE.md)

- Use `.venv` local environment for all dependencies
- Install packages with `uv pip install <library>` (not pip directly)
- Entry point for web version is `main.py` — do NOT modify it
- Desktop entry point is `app.py` — separate file
- Stack: Python backend, simplest useful UI
- Dependencies already in `.venv`: `opencv-python`, `pandas`, `numpy`, `gradio`

---

## Sources

### Primary (HIGH confidence)

- https://doc.qt.io/qtforpython-6/PySide6/QtCore/QRunnable.html — QRunnable API
- https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThreadPool.html — QThreadPool API
- https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html — QImage constructor with numpy buffer, Format_RGB888
- https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSpinBox.html — QSpinBox setSingleStep, stepBy
- https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html — QSplitter API
- https://pytest-qt.readthedocs.io/en/latest/intro.html — pytest-qt qtbot fixture

### Secondary (MEDIUM confidence)

- https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/ — WorkerSignals pattern (verified against Qt docs)
- https://www.codeflamingo.eu/blog/aspectratio-qpixmap/ — ScaledImageLabel paintEvent pattern (verified against Qt docs)
- https://medium.com/@bgallois/numpy-ndarray-qimage-beware-the-trap-52dcbe7388b9 — GC segfault explanation (consistent with Qt docs memory model)

### Tertiary (LOW confidence)

- PyPI version data: PySide6 6.11.0, pytest-qt 4.5.0 — confirmed via curl to pypi.org/pypi/*/json

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions confirmed against PyPI registry directly
- Architecture: HIGH — patterns verified against official Qt for Python docs
- Pitfalls: HIGH (segfault, signals on QRunnable) — documented in official sources; MEDIUM (coordinate mapping) — derived from Qt mouse event docs and geometry math
- Test infrastructure: HIGH — pytest-qt is the standard tool for this domain

**Research date:** 2026-03-29
**Valid until:** 2026-05-29 (60 days; PySide6 is stable, slow-moving)
