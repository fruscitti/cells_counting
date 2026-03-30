# PySide6 Desktop Patterns
**Research date:** 2026-03-29
**Confidence:** HIGH (official Qt docs + pythonguis.com + verified code patterns)

---

## 1. Why PySide6 (Not PyQt5 or PyQt6)

**Recommendation: PySide6.** Three concrete reasons:

| Criterion | PySide6 | PyQt5 | PyQt6 |
|-----------|---------|-------|-------|
| License | LGPL — embed in closed-source apps freely | LGPL — OK, but older Qt 5.x | GPL only — must open-source your app or buy commercial license |
| Maintainer | The Qt Company (official) | Riverbank Computing (third-party) | Riverbank Computing (third-party) |
| Qt version | Qt 6 (current) | Qt 5 (EOL) | Qt 6 (current) |
| Signal/Slot syntax | `Signal`, `Slot` (clean) | `pyqtSignal`, `pyqtSlot` (verbose) | `pyqtSignal`, `pyqtSlot` (verbose) |
| Enum syntax | Short form works: `Qt.KeepAspectRatio` | Short form works | **Fully qualified required**: `Qt.AspectRatioMode.KeepAspectRatio` |

PySide6 is the official Qt for Python binding. PyQt6's GPL license means any distribution of the app requires either open-sourcing the code or purchasing a commercial Riverbank license. PySide6 avoids this entirely.

**Installation:**
```bash
uv pip install PySide6
```

This pulls in Qt 6 wheels (~60 MB). No system Qt install needed — all bundled.

---

## 2. Numpy Array → QPixmap: The Critical Conversion

This is the most error-prone step. OpenCV images are BGR numpy arrays. Qt expects RGB.

### Canonical pattern (use this):

```python
import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt


def numpy_bgr_to_qpixmap(bgr_array: np.ndarray) -> QPixmap:
    """Convert an OpenCV BGR numpy array to a QPixmap for display."""
    # Step 1: BGR → RGB
    rgb = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2RGB)

    # Step 2: Build QImage — must pass bytes-per-line to avoid stride corruption
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

    # Step 3: Copy the data — QImage only holds a reference to rgb.data by default.
    # If rgb goes out of scope the pixmap shows garbage. .copy() owns the memory.
    return QPixmap.fromImage(qimg.copy())


def numpy_gray_to_qpixmap(gray_array: np.ndarray) -> QPixmap:
    """Convert a single-channel (grayscale) numpy array to QPixmap."""
    h, w = gray_array.shape
    qimg = QImage(gray_array.data, w, h, w, QImage.Format.Format_Grayscale8)
    return QPixmap.fromImage(qimg.copy())
```

**Gotcha 1 — The `.copy()` trap:** `QImage` takes a raw pointer to the numpy array's buffer. If the numpy array is a local variable in a worker thread, it gets garbage-collected and the QImage reads freed memory. Always call `.copy()` or ensure the array outlives the QImage.

**Gotcha 2 — bytes_per_line:** OpenCV arrays may have padding if sliced. Always compute `ch * w` explicitly rather than assuming contiguous memory. If the image was created by slicing a larger array, use `np.ascontiguousarray(img)` first.

**Gotcha 3 — BGR not RGB:** Missing `cvtColor` produces red/blue channel-swapped images. The symptom is: red cells appear blue. Always convert.

```python
# Safe wrapper that handles the contiguous-memory edge case:
def safe_numpy_to_qpixmap(img: np.ndarray) -> QPixmap:
    img = np.ascontiguousarray(img)  # no-op if already contiguous
    if img.ndim == 2:
        return numpy_gray_to_qpixmap(img)
    return numpy_bgr_to_qpixmap(img)
```

---

## 3. Image Display: QLabel vs QGraphicsView

### When to use QLabel

Use `QLabel` for simple side-by-side display of fixed or resizable images with no zoom/pan. It is far less code.

```python
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class ScaledImageLabel(QLabel):
    """QLabel that scales its pixmap to fit available space, preserving aspect ratio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap = None
        self.setMinimumSize(100, 100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_pixmap(self, pixmap: QPixmap):
        self._original_pixmap = pixmap
        self._update_scaled()

    def resizeEvent(self, event):
        self._update_scaled()
        super().resizeEvent(event)

    def _update_scaled(self):
        if self._original_pixmap is None:
            return
        scaled = self._original_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        super().setPixmap(scaled)
```

**Key point:** Do NOT call `label.setScaledContents(True)` — it ignores aspect ratio and distorts microscopy images. Instead override `resizeEvent` as above.

### When to use QGraphicsView

Use `QGraphicsView` when users need zoom (mouse wheel) and pan (drag). Required if images are large and users need to inspect individual cells.

```python
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class ZoomableImageView(QGraphicsView):
    """Image viewer with mouse wheel zoom and drag-to-pan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = None
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # not needed for photos
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    def set_pixmap(self, pixmap: QPixmap):
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)

    def resizeEvent(self, event):
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)
```

### Recommendation for this project

Use `ScaledImageLabel` (QLabel subclass) for the side-by-side original/annotated display. It is 30 lines vs 60+ for QGraphicsView. Microscopy images are typically 1024×1024 or similar — not so large that zoom is mandatory in v1. Add ZoomableImageView in a later iteration if users request it.

---

## 4. Side-by-Side Image Layout for Multiple Pairs

For displaying N image pairs (original + annotated) in a scrollable area:

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy
)


class ImagePairWidget(QFrame):
    """One row: filename label + original image + annotated image + cell count."""

    def __init__(self, filename: str, original: QPixmap, annotated: QPixmap, count: int):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)

        # Header: filename + count
        header = QLabel(f"{filename}  —  {count} cells")
        header.setStyleSheet("font-weight: bold;")
        layout.addWidget(header)

        # Images side by side
        images_row = QHBoxLayout()
        orig_label = ScaledImageLabel()
        orig_label.set_pixmap(original)
        orig_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        orig_label.setMinimumHeight(200)

        ann_label = ScaledImageLabel()
        ann_label.set_pixmap(annotated)
        ann_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ann_label.setMinimumHeight(200)

        images_row.addWidget(orig_label)
        images_row.addWidget(ann_label)
        layout.addLayout(images_row)


class ResultsScrollArea(QScrollArea):
    """Scrollable container for multiple ImagePairWidgets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._container)
        self.setWidgetResizable(True)  # CRITICAL: without this the scroll area won't resize child

    def add_pair(self, filename, original_pixmap, annotated_pixmap, count):
        pair = ImagePairWidget(filename, original_pixmap, annotated_pixmap, count)
        self._layout.addWidget(pair)

    def clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
```

**setWidgetResizable(True)** is mandatory. Without it, QScrollArea does not let the inner widget grow and the images stack on top of each other.

---

## 5. Main Window Layout: QSplitter

The canonical pattern for "controls on left, content on right":

```python
from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QVBoxLayout
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cell Counter")

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: controls
        control_panel = QWidget()
        control_panel.setMaximumWidth(300)
        control_panel.setMinimumWidth(220)
        self._build_controls(control_panel)
        splitter.addWidget(control_panel)

        # Right panel: results scroll area
        self._results = ResultsScrollArea()
        splitter.addWidget(self._results)

        # Give results 3× the space controls get on startup
        splitter.setSizes([260, 780])

        self.setCentralWidget(splitter)
```

`setSizes()` sets the initial pixel split. The user can drag the handle. Use `splitter.setStretchFactor(1, 1)` to make the right panel absorb all resize growth.

---

## 6. Slider Controls with Live Labels

Pattern for one labeled parameter slider:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QSpinBox
from PySide6.QtCore import Qt, Signal


class LabeledSlider(QWidget):
    """Slider with a title label and a live numeric readout."""

    value_changed = Signal(int)

    def __init__(self, title: str, minimum: int, maximum: int, default: int, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Row 1: title + current value
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel(title))
        self._value_label = QLabel(str(default))
        self._value_label.setMinimumWidth(40)  # prevents jitter when value changes width
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_row.addWidget(self._value_label)
        layout.addLayout(title_row)

        # Row 2: the slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(minimum)
        self._slider.setMaximum(maximum)
        self._slider.setValue(default)
        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider)

    def _on_change(self, value: int):
        self._value_label.setText(str(value))
        self.value_changed.emit(value)

    def value(self) -> int:
        return self._slider.value()
```

For the BLUR_STRENGTH parameter (must be odd), add a validator in the owner widget:

```python
blur_slider = LabeledSlider("Blur Strength", minimum=1, maximum=31, default=9)

def on_blur_changed(raw_value: int):
    # Force odd: round down to nearest odd
    odd_value = raw_value if raw_value % 2 == 1 else raw_value - 1
    blur_slider._slider.blockSignals(True)
    blur_slider._slider.setValue(odd_value)
    blur_slider._slider.blockSignals(False)
    blur_slider._value_label.setText(str(odd_value))
    # Use (odd_value, odd_value) as BLUR_STRENGTH tuple

blur_slider.value_changed.connect(on_blur_changed)
```

**Alternative for BLUR_STRENGTH:** Use `QSpinBox` with `setSingleStep(2)` — this naturally increments by 2, and initializing to an odd number keeps it always odd without extra logic.

```python
from PySide6.QtWidgets import QSpinBox

blur_spin = QSpinBox()
blur_spin.setMinimum(1)
blur_spin.setMaximum(31)
blur_spin.setSingleStep(2)   # always increments by 2
blur_spin.setValue(9)        # start odd → stays odd
```

---

## 7. File Dialog: Multi-Select Images

```python
from PySide6.QtWidgets import QFileDialog


def open_images(parent_widget) -> list[str]:
    """Open a file picker for multiple images. Returns list of absolute paths."""
    paths, _ = QFileDialog.getOpenFileNames(
        parent_widget,
        "Select Images",
        "",   # start directory — "" means last used / home
        "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp);;All Files (*)",
    )
    return paths  # empty list if user cancelled
```

`getOpenFileNames` (plural) returns `(list[str], selected_filter_str)`. The `_` discards the filter string. The dialog is native on all platforms — macOS Finder, Windows Explorer, Linux GTK/KDE depending on the desktop.

---

## 8. Threading: Running OpenCV Without Freezing the UI

**Never call OpenCV processing directly from a button click handler.** It blocks the Qt event loop and the window freezes.

### Pattern: QRunnable + QThreadPool (preferred over QThread subclassing)

```python
import traceback
from PySide6.QtCore import QRunnable, QThreadPool, QObject, Signal, Slot
import numpy as np


class WorkerSignals(QObject):
    """Signals must live on a QObject, not QRunnable."""
    finished = Signal()
    error = Signal(str)           # error message string
    result = Signal(object)       # the return value of the function


class ProcessingWorker(QRunnable):
    """Runs cell counting for a single image in a thread pool thread."""

    def __init__(self, image_path: str, params: dict):
        super().__init__()
        self.image_path = image_path
        self.params = params
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            result = self._process()
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(traceback.format_exc())
        finally:
            self.signals.finished.emit()

    def _process(self) -> dict:
        """Returns dict with keys: path, original_bgr, annotated_bgr, count."""
        import cv2
        img = cv2.imread(self.image_path)
        # ... call existing processing pipeline with self.params ...
        return {
            "path": self.image_path,
            "original": img,
            "annotated": annotated,
            "count": count,
        }
```

### Wiring it to the UI

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._threadpool = QThreadPool()
        self._pending = 0  # track in-flight workers

    def run_analysis(self, image_paths: list[str], params: dict):
        self._results.clear()
        self._run_button.setEnabled(False)
        self._pending = len(image_paths)

        for path in image_paths:
            worker = ProcessingWorker(path, params)
            worker.signals.result.connect(self._on_result)
            worker.signals.error.connect(self._on_error)
            worker.signals.finished.connect(self._on_one_done)
            self._threadpool.start(worker)

    @Slot(object)
    def _on_result(self, data: dict):
        """Called in the main thread — safe to update UI here."""
        original_px = safe_numpy_to_qpixmap(data["original"])
        annotated_px = safe_numpy_to_qpixmap(data["annotated"])
        self._results.add_pair(
            filename=data["path"].split("/")[-1],
            original_pixmap=original_px,
            annotated_pixmap=annotated_px,
            count=data["count"],
        )

    @Slot(str)
    def _on_error(self, tb: str):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Processing Error", tb)

    @Slot()
    def _on_one_done(self):
        self._pending -= 1
        if self._pending == 0:
            self._run_button.setEnabled(True)
```

**Key rules:**
- Signals cross thread boundaries safely — that is their purpose.
- Never touch a QWidget from a worker thread. Only emit signals; let slots update the UI.
- `QThreadPool.globalInstance()` exists as a convenience but using a per-window pool avoids surprises during shutdown.
- `setMaxThreadCount(N)` if you want to limit CPU cores used for batch processing.

### QThread subclass (alternative — use when you need a persistent loop)

```python
class VideoThread(QThread):
    frame_ready = Signal(np.ndarray)

    def run(self):
        cap = cv2.VideoCapture(0)
        while not self.isInterruptionRequested():
            ret, frame = cap.read()
            if ret:
                self.frame_ready.emit(frame)
        cap.release()
```

Use `QThread` subclass only when the background work is a continuous loop (video stream, live preview). For one-shot processing jobs, `QRunnable + QThreadPool` is cleaner.

---

## 9. Cross-Platform Gotchas

### Windows: DPI Scaling

Qt 6 enables HiDPI by default — no `setAttribute(AA_EnableHighDpiScaling)` needed. However, on Windows with mixed monitor DPI (e.g., 100% + 150%), layout rounding can cause 1-pixel gaps between widgets.

```python
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Put this BEFORE creating QApplication:
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
app = QApplication(sys.argv)
```

`PassThrough` disables rounding — fractional scale factors (e.g., 1.5) are passed as-is. This prevents the "1px jitter" on 150% scaled monitors. It is the most reliable setting for image-display apps where pixel-accurate layout matters less than smooth rendering.

### macOS: Native Menu Bar

On macOS, `QMenuBar` renders into the system menu bar at the top of the screen (not inside the window). This is correct native behavior. However, `QAction` shortcuts set with `setShortcut(QKeySequence("Ctrl+O"))` automatically become `Cmd+O` on macOS — no manual mapping needed.

If the app has no menu bar (control panel + image area only), macOS will show a minimal default menu. No action required unless you want a custom menu.

Known issue on macOS: missing icons in context menus as of PySide6 6.7.3. Workaround: use text labels on menu items, not icon-only items. This is a Qt bug, not application code issue.

### macOS: Window Close Does Not Quit

By default, closing the last window on macOS hides the app (consistent with macOS conventions) but does not call `sys.exit`. To match the expected behavior for a single-window tool:

```python
app.setQuitOnLastWindowClosed(True)  # this is actually the default — verify it is set
```

Or connect the signal explicitly:

```python
app.lastWindowClosed.connect(app.quit)
```

### Linux: Font Rendering

Qt on Linux uses the system font by default. On minimal desktop environments (no GTK/KDE fonts installed), the default font may be tiny or missing. Safe fallback:

```python
from PySide6.QtGui import QFont
app.setFont(QFont("DejaVu Sans", 10))  # available on nearly all Linux distros
```

### Linux: Missing xcb Plugin

On headless or minimal Linux installs, PySide6 will fail with:
```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```
Fix: `apt install libxcb-cursor0` (Ubuntu/Debian). This is a deployment concern, not a development one.

### OpenCV BGR Stride Issue (All Platforms)

If the image was loaded and then a region-of-interest was sliced from it:
```python
roi = img[100:200, 100:200]  # this array may not be contiguous
```
Pass `np.ascontiguousarray(roi)` to the QImage constructor — otherwise the bytes_per_line calculation is wrong and the image renders with diagonal stripes.

---

## 10. Application Entry Point

```python
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    # DPI policy must be set before QApplication is created
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Cell Counter")
    app.setOrganizationName("Lab")  # used for QSettings storage path

    window = MainWindow()
    window.resize(1200, 800)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

---

## Summary of Key Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Binding | PySide6 | Official Qt, LGPL, no GPL lock-in |
| Image widget | ScaledImageLabel (QLabel subclass) | Simplest path; QGraphicsView adds complexity only needed for zoom/pan |
| BGR→RGB | cv2.cvtColor + QImage.Format_RGB888 | Direct, no extra dependencies; PIL path adds 30ms import overhead |
| Threading | QRunnable + QThreadPool | One-shot batch jobs; cleaner than QThread subclass |
| Layout | QSplitter (controls | results) | Standard two-panel pattern; user-resizable |
| Scroll | QScrollArea with setWidgetResizable(True) | Required for dynamic N-image list |
| Slider | LabeledSlider wrapping QSlider | Live value display; QSpinBox for BLUR_STRENGTH (odd-step enforcement) |
| DPI | PassThrough policy before QApplication | Prevents 150% Windows scaling layout gaps |

---

## Sources

- [Qt for Python — QGraphicsView](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGraphicsView.html)
- [Qt for Python — QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html)
- [Qt for Python — QFileDialog](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFileDialog.html)
- [Qt for Python — QSlider](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSlider.html)
- [Qt for Python — QScrollArea](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollArea.html)
- [pythonguis.com — Multithreading PySide6 with QThreadPool](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/)
- [pythonguis.com — Adding images to PySide6](https://www.pythonguis.com/faq/adding-images-to-pyside6-applications/)
- [pythonguis.com — PyQt6 vs PySide6 differences](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/)
- [pythonguis.com — PyQt vs PySide licensing](https://www.pythonguis.com/faq/pyqt-vs-pyside/)
- [Qt Forum — Maintaining aspect ratio of QLabel](https://forum.qt.io/topic/108068/maintaining-aspect-ratio-of-qlabel)
- [Qt Forum — Windows DPI scaling Fusion vs Native style](https://forum.qt.io/topic/164286/native-windows-style-ignores-designer-button-size-fusion-style-ignores-dpi-scaling)
- [Stack Overflow — Convert OpenCV numpy array to QPixmap](https://kiwix.ounapuu.ee/content/stackoverflow.com_en_all_2023-11/questions/34232632/convert-python-opencv-image-numpy-array-to-pyqt-qpixmap-image)
