import os
import cv2

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog
)
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QFont

from ui.scaled_image_label import ScaledImageLabel
from ui.image_utils import numpy_rgb_to_pixmap
from ui.param_panel import ParamPanel


class MainWindow(QMainWindow):
    """Main application window for Cell Counter desktop app."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Internal state
        self._file_paths = []       # list of absolute paths to loaded images
        self._images = {}           # {filename: {"original_bgr": ndarray, "original_rgb": ndarray, "annotated_rgb": ndarray | None, "algo_count": 0, "manual_marks": []}}
        self._current_file = None   # currently selected filename

        self.setWindowTitle("Cell Counter")
        self.setMinimumSize(1024, 700)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --- Left panel (fixed 280px) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.open_btn = QPushButton("Open Images")
        left_layout.addWidget(self.open_btn)

        self.image_list = QListWidget()
        left_layout.addWidget(self.image_list)

        # Parameter control panel
        self.param_panel = ParamPanel()
        left_layout.addWidget(self.param_panel)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setEnabled(False)
        left_layout.addWidget(self.analyze_btn)

        self.auto_optimize_btn = QPushButton("Auto-Optimize")
        self.auto_optimize_btn.setEnabled(False)
        left_layout.addWidget(self.auto_optimize_btn)

        self.clear_btn = QPushButton("Clear")
        left_layout.addWidget(self.clear_btn)

        self.undo_mark_btn = QPushButton("Undo Mark")
        self.undo_mark_btn.setEnabled(False)
        left_layout.addWidget(self.undo_mark_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        left_layout.addWidget(self.status_label)

        # Cell count display
        self.count_label = QLabel("Cell Count: 0")
        count_font = QFont()
        count_font.setPointSize(14)
        count_font.setBold(True)
        self.count_label.setFont(count_font)
        self.count_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.count_label)

        left_layout.addStretch()
        main_layout.addWidget(left_panel)

        # --- Right side (splitter) ---
        right_splitter = QSplitter(Qt.Vertical)

        # Top: side-by-side image display
        images_widget = QWidget()
        images_layout = QHBoxLayout(images_widget)
        images_layout.setContentsMargins(0, 0, 0, 0)
        images_layout.setSpacing(4)

        self.original_label = ScaledImageLabel(click_enabled=False)
        self.original_label.setStyleSheet("border: 1px solid #aaa;")
        self.original_label.setText("Original")
        self.original_label.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(self.original_label)

        self.annotated_label = ScaledImageLabel(click_enabled=True)
        self.annotated_label.setStyleSheet("border: 1px solid #aaa;")
        self.annotated_label.setText("Annotated")
        self.annotated_label.setAlignment(Qt.AlignCenter)
        images_layout.addWidget(self.annotated_label)

        right_splitter.addWidget(images_widget)

        # Bottom: results table
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["File", "Cell Count"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        right_splitter.addWidget(self.results_table)

        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(right_splitter, stretch=1)

    def _connect_signals(self):
        """Wire up signals to slots."""
        self.open_btn.clicked.connect(self._on_open_images)
        self.image_list.currentItemChanged.connect(self._on_image_selected)
        self.clear_btn.clicked.connect(self._on_clear)
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.auto_optimize_btn.clicked.connect(self._on_auto_optimize)
        self.annotated_label.clicked.connect(self._on_annotated_click)
        self.undo_mark_btn.clicked.connect(self._on_undo_mark)

    # ---- Public API ----

    def get_file_filter(self) -> str:
        """Return file dialog filter string for supported image types."""
        return "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp);;All Files (*)"

    def load_images(self, paths: list):
        """Load images from a list of file paths into the app."""
        for path in paths:
            img_bgr = cv2.imread(path)
            if img_bgr is None:
                continue
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            basename = os.path.basename(path)
            self._images[basename] = {
                "original_bgr": img_bgr,
                "original_rgb": img_rgb,
                "annotated_rgb": None,
                "algo_count": 0,
                "manual_marks": [],
            }
            self.image_list.addItem(basename)
            self._file_paths.append(path)

        if self._file_paths:
            self.analyze_btn.setEnabled(True)
            self.auto_optimize_btn.setEnabled(True)
            # Select first item if nothing selected
            if self.image_list.currentRow() < 0:
                self.image_list.setCurrentRow(0)

    # ---- Private slots ----

    def _on_open_images(self):
        """Open file dialog for selecting images."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Images", "", self.get_file_filter()
        )
        if paths:
            self.load_images(paths)

    def _on_image_selected(self, current, previous):
        """Update display when a different image is selected in the list."""
        if current is None:
            return
        filename = current.text()
        self._current_file = filename
        entry = self._images.get(filename)
        if entry is None:
            return

        # Show original image
        self.original_label.setPixmap(numpy_rgb_to_pixmap(entry["original_rgb"]))
        self.original_label.setText("")

        # Show annotated image if available (with manual marks), otherwise clear
        if entry["annotated_rgb"] is not None:
            self._redraw_annotated()
        else:
            self.annotated_label.clearPixmap()
            self.annotated_label.setText("Annotated")
            # Update count label (no annotated image yet)
            total = entry["algo_count"] + len(entry["manual_marks"])
            self.count_label.setText(f"Cell Count: {total}")

        # Update undo button state
        self.undo_mark_btn.setEnabled(len(entry["manual_marks"]) > 0)

    def _on_annotated_click(self, orig_x: int, orig_y: int):
        """MARK-01: Add a manual mark at the clicked position on the annotated image."""
        if self._current_file is None:
            return
        entry = self._images.get(self._current_file)
        if entry is None or entry["annotated_rgb"] is None:
            return
        entry["manual_marks"].append((orig_x, orig_y))
        self._redraw_annotated()
        self.undo_mark_btn.setEnabled(True)

    def _on_undo_mark(self):
        """MARK-02: Remove the last manual mark and redraw."""
        if self._current_file is None:
            return
        entry = self._images.get(self._current_file)
        if entry is None:
            return
        marks = entry["manual_marks"]
        if not marks:
            return
        marks.pop()
        self._redraw_annotated()
        if not marks:
            self.undo_mark_btn.setEnabled(False)

    def _redraw_annotated(self):
        """Redraw the annotated image with current manual marks on top."""
        if self._current_file is None:
            return
        entry = self._images.get(self._current_file)
        if entry is None:
            return
        base_rgb = entry["annotated_rgb"]
        if base_rgb is None:
            return
        from analysis_core import draw_manual_marks
        display_rgb = draw_manual_marks(base_rgb, entry["manual_marks"])
        self.annotated_label.setPixmap(numpy_rgb_to_pixmap(display_rgb))
        self.annotated_label.setText("")
        total = entry["algo_count"] + len(entry["manual_marks"])
        self.count_label.setText(f"Cell Count: {total}")

    def _on_clear(self):
        """CLR-01: Reset all state to defaults."""
        # Clear image data
        self._images.clear()
        self._file_paths.clear()
        self._current_file = None

        # Clear UI widgets
        self.image_list.clear()
        self.results_table.setRowCount(0)
        self.original_label.clearPixmap()
        self.original_label.setText("Original")
        self.annotated_label.clearPixmap()
        self.annotated_label.setText("Annotated")
        self.count_label.setText("Cell Count: 0")
        self.status_label.setText("Ready")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        # Reset parameters to defaults
        self.param_panel.reset_defaults()

        # Disable action buttons
        self.analyze_btn.setEnabled(False)
        self.auto_optimize_btn.setEnabled(False)
        self.undo_mark_btn.setEnabled(False)

        # Reset window title (no batch context in Phase 2)
        self.setWindowTitle("Cell Counter")

    # ---- Analysis worker slots ----

    def _collect_params(self) -> dict:
        """Return current parameter values from the param panel."""
        return self.param_panel.get_params()

    def _on_analyze(self):
        """Start background analysis of all loaded images."""
        if not self._images:
            return
        from workers.analysis_worker import AnalysisWorker
        self.analyze_btn.setEnabled(False)
        self.auto_optimize_btn.setEnabled(False)
        self.progress_bar.setMaximum(len(self._images))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Analyzing...")

        worker = AnalysisWorker(self._images, self._collect_params())
        worker.signals.image_done.connect(self._on_image_done)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.error.connect(self._on_image_error)
        worker.signals.finished.connect(self._on_analysis_finished)
        QThreadPool.globalInstance().start(worker)

    def _on_image_done(self, filename: str, annotated_rgb, count: int):
        """Handle completion of a single image analysis."""
        self._images[filename]["annotated_rgb"] = annotated_rgb
        self._images[filename]["algo_count"] = count
        self._update_results_row(filename, count)
        if filename == self._current_file:
            self._redraw_annotated()

    def _on_image_error(self, filename: str, error_msg: str):
        """Handle analysis error for a single image."""
        self._images[filename]["algo_count"] = 0
        self._update_results_row(filename, 0, is_error=True)
        self.status_label.setText(f"Error processing {filename}")

    def _on_progress(self, current: int, total: int):
        """Update progress bar and status label."""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processing {current}/{total}...")

    def _on_analysis_finished(self):
        """Re-enable buttons and hide progress bar when analysis completes."""
        self.analyze_btn.setEnabled(True)
        self.auto_optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis complete")

    def _update_results_row(self, filename: str, count: int, is_error: bool = False):
        """Update or insert a row in the results table for the given filename."""
        count_text = "0 (warning)" if is_error else str(count)
        # Search for existing row
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.text() == filename:
                self.results_table.setItem(row, 1, QTableWidgetItem(count_text))
                return
        # Insert new row
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(filename))
        self.results_table.setItem(row, 1, QTableWidgetItem(count_text))

    # ---- Auto-optimize worker slots ----

    def _on_auto_optimize(self):
        """Start background parameter optimization on the current image."""
        if not self._current_file:
            return
        from workers.optimize_worker import OptimizeWorker
        img_bgr = self._images[self._current_file]["original_bgr"]
        self.auto_optimize_btn.setEnabled(False)
        self.status_label.setText("Optimizing...")

        worker = OptimizeWorker(img_bgr, self.param_panel.get_params()["use_cleaning"])
        worker.signals.result.connect(self._on_optimize_result)
        worker.signals.error.connect(
            lambda msg: self.status_label.setText(f"Optimize error: {msg}")
        )
        worker.signals.finished.connect(
            lambda: self.auto_optimize_btn.setEnabled(True)
        )
        QThreadPool.globalInstance().start(worker)

    def _on_optimize_result(self, brightness: int, min_area: int, blur: int, count: int):
        """Apply optimized parameters to the param panel."""
        self.param_panel.set_params({
            "brightness_threshold": brightness,
            "min_cell_area": min_area,
            "blur_strength": blur,
        })
        self.status_label.setText(
            f"Optimized: brightness={brightness}, area={min_area}, blur={blur} ({count} cells)"
        )
