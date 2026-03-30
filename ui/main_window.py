import os
import cv2

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QDialog, QInputDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QThreadPool, QTimer, QSettings
from PySide6.QtGui import QFont

from ui.scaled_image_label import ScaledImageLabel
from ui.image_utils import numpy_rgb_to_pixmap
from ui.param_panel import ParamPanel
from batch_manager import BatchManager
from ui.batch_dialogs import OpenBatchDialog


class MainWindow(QMainWindow):
    """Main application window for Cell Counter desktop app."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Internal state
        self._file_paths = []       # list of absolute paths to loaded images
        self._images = {}           # {filename: {"original_bgr": ndarray, "original_rgb": ndarray, "annotated_rgb": ndarray | None, "algo_count": 0, "manual_marks": []}}
        self._current_file = None   # currently selected filename
        self._current_batch_dir = None  # Path to currently open batch directory, or None

        self.setWindowTitle("Cell Counter")
        self.setMinimumSize(1024, 700)

        self._build_ui()
        self._connect_signals()
        self._update_status_bar()
        QTimer.singleShot(0, self._restore_splitter_state)

    def _build_ui(self):
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --- Left panel (scrollable sidebar) ---
        left_panel = QWidget()
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

        self.save_batch_btn = QPushButton("Save Batch")
        self.save_batch_btn.setEnabled(False)
        left_layout.addWidget(self.save_batch_btn)

        self.open_batch_btn = QPushButton("Open Batch")
        left_layout.addWidget(self.open_batch_btn)

        self.add_images_btn = QPushButton("Add Images")
        self.add_images_btn.setEnabled(False)  # only when batch is open
        left_layout.addWidget(self.add_images_btn)

        self.remove_image_btn = QPushButton("Remove Image")
        self.remove_image_btn.setEnabled(False)
        left_layout.addWidget(self.remove_image_btn)

        self.re_analyze_btn = QPushButton("Re-Analyze")
        self.re_analyze_btn.setEnabled(False)
        left_layout.addWidget(self.re_analyze_btn)

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.setEnabled(False)
        left_layout.addWidget(self.export_csv_btn)

        self.undo_mark_btn = QPushButton("Undo Mark")
        self.undo_mark_btn.setEnabled(False)
        left_layout.addWidget(self.undo_mark_btn)

        # Hide sidebar buttons — they will be re-surfaced by the toolbar in Phase 5 (per SIDE-03)
        for _btn in [
            self.open_btn, self.analyze_btn, self.auto_optimize_btn, self.clear_btn,
            self.save_batch_btn, self.open_batch_btn, self.add_images_btn,
            self.remove_image_btn, self.re_analyze_btn, self.export_csv_btn,
            self.undo_mark_btn,
        ]:
            _btn.setVisible(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        # progress_bar will be added to the status bar in _setup_status_bar()

        # Keep status_label as attribute (referenced by some existing code paths)
        # but do NOT add to any layout — status bar replaces it
        self.status_label = QLabel("Ready")

        # Cell count display
        self.count_label = QLabel("Cell Count: 0")
        count_font = QFont()
        count_font.setPointSize(14)
        count_font.setBold(True)
        self.count_label.setFont(count_font)
        self.count_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.count_label)

        left_layout.addStretch()

        self.left_scroll = QScrollArea()
        self.left_scroll.setMinimumWidth(220)
        self.left_scroll.setMaximumWidth(500)
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.left_scroll.setFrameShape(self.left_scroll.Shape.NoFrame)
        self.left_scroll.setWidget(left_panel)

        # --- Right side (splitter) ---
        right_splitter = QSplitter(Qt.Vertical)

        # Top: side-by-side image display
        images_widget = QWidget()
        images_layout = QHBoxLayout(images_widget)
        images_layout.setContentsMargins(0, 0, 0, 0)
        images_layout.setSpacing(4)

        # --- Original image panel ---
        orig_panel = QWidget()
        orig_panel_layout = QVBoxLayout(orig_panel)
        orig_panel_layout.setContentsMargins(0, 0, 0, 0)
        orig_panel_layout.setSpacing(2)

        orig_zoom_bar = QWidget()
        orig_zoom_layout = QHBoxLayout(orig_zoom_bar)
        orig_zoom_layout.setContentsMargins(0, 0, 0, 0)
        orig_zoom_layout.setSpacing(2)
        orig_zoom_layout.addWidget(QLabel("Original"))
        orig_zoom_layout.addStretch()
        self.orig_zoom_out_btn = QPushButton("−")
        self.orig_zoom_out_btn.setFixedWidth(28)
        self.orig_zoom_out_btn.setToolTip("Zoom out")
        self.orig_zoom_reset_btn = QPushButton("1:1")
        self.orig_zoom_reset_btn.setFixedWidth(36)
        self.orig_zoom_reset_btn.setToolTip("Reset zoom")
        self.orig_zoom_in_btn = QPushButton("+")
        self.orig_zoom_in_btn.setFixedWidth(28)
        self.orig_zoom_in_btn.setToolTip("Zoom in")
        orig_zoom_layout.addWidget(self.orig_zoom_out_btn)
        orig_zoom_layout.addWidget(self.orig_zoom_reset_btn)
        orig_zoom_layout.addWidget(self.orig_zoom_in_btn)

        self.original_label = ScaledImageLabel(click_enabled=False)
        self.original_label.setStyleSheet("border: 1px solid #aaa;")
        self.original_label.setText("Original")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_scroll = QScrollArea()
        self.original_scroll.setWidgetResizable(True)
        self.original_scroll.setWidget(self.original_label)

        orig_panel_layout.addWidget(orig_zoom_bar)
        orig_panel_layout.addWidget(self.original_scroll)
        images_layout.addWidget(orig_panel)

        # --- Annotated image panel ---
        ann_panel = QWidget()
        ann_panel_layout = QVBoxLayout(ann_panel)
        ann_panel_layout.setContentsMargins(0, 0, 0, 0)
        ann_panel_layout.setSpacing(2)

        ann_zoom_bar = QWidget()
        ann_zoom_layout = QHBoxLayout(ann_zoom_bar)
        ann_zoom_layout.setContentsMargins(0, 0, 0, 0)
        ann_zoom_layout.setSpacing(2)
        ann_zoom_layout.addWidget(QLabel("Annotated"))
        ann_zoom_layout.addStretch()
        self.ann_zoom_out_btn = QPushButton("−")
        self.ann_zoom_out_btn.setFixedWidth(28)
        self.ann_zoom_out_btn.setToolTip("Zoom out")
        self.ann_zoom_reset_btn = QPushButton("1:1")
        self.ann_zoom_reset_btn.setFixedWidth(36)
        self.ann_zoom_reset_btn.setToolTip("Reset zoom")
        self.ann_zoom_in_btn = QPushButton("+")
        self.ann_zoom_in_btn.setFixedWidth(28)
        self.ann_zoom_in_btn.setToolTip("Zoom in")
        ann_zoom_layout.addWidget(self.ann_zoom_out_btn)
        ann_zoom_layout.addWidget(self.ann_zoom_reset_btn)
        ann_zoom_layout.addWidget(self.ann_zoom_in_btn)

        self.annotated_label = ScaledImageLabel(click_enabled=True)
        self.annotated_label.setStyleSheet("border: 1px solid #aaa;")
        self.annotated_label.setText("Annotated")
        self.annotated_label.setAlignment(Qt.AlignCenter)
        self.annotated_scroll = QScrollArea()
        self.annotated_scroll.setWidgetResizable(True)
        self.annotated_scroll.setWidget(self.annotated_label)

        ann_panel_layout.addWidget(ann_zoom_bar)
        ann_panel_layout.addWidget(self.annotated_scroll)
        images_layout.addWidget(ann_panel)

        right_splitter.addWidget(images_widget)

        # Bottom: results table
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["File", "Cell Count"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        right_splitter.addWidget(self.results_table)

        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)

        self.outer_splitter = QSplitter(Qt.Horizontal)
        self.outer_splitter.addWidget(self.left_scroll)   # index 0: sidebar
        self.outer_splitter.addWidget(right_splitter)      # index 1: image area
        self.outer_splitter.setStretchFactor(0, 0)
        self.outer_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.outer_splitter)

        self._setup_status_bar()

    def _setup_status_bar(self):
        """Add permanent labels and progress bar to the status bar (STAT-01-04)."""
        self._status_batch_lbl = QLabel("No batch")
        self._status_count_lbl = QLabel("0 images")
        self._status_cells_lbl = QLabel("0 cells")

        bar = self.statusBar()
        bar.addWidget(self.progress_bar)          # left side, hidden by default
        bar.addPermanentWidget(QLabel("|"))
        bar.addPermanentWidget(self._status_batch_lbl)
        bar.addPermanentWidget(QLabel("|"))
        bar.addPermanentWidget(self._status_count_lbl)
        bar.addPermanentWidget(QLabel("|"))
        bar.addPermanentWidget(self._status_cells_lbl)

    def _update_status_bar(self):
        """Refresh permanent status bar labels from canonical state (self._images, self._current_batch_dir)."""
        batch_name = "No batch"
        if self._current_batch_dir is not None:
            batch_name = self._current_batch_dir.name
        image_count = len(self._images)
        total_cells = sum(
            e["algo_count"] + len(e["manual_marks"])
            for e in self._images.values()
            if e is not None
        )
        self._status_batch_lbl.setText(batch_name)
        n = image_count
        self._status_count_lbl.setText(f"{n} image{'s' if n != 1 else ''}")
        c = total_cells
        self._status_cells_lbl.setText(f"{c} cell{'s' if c != 1 else ''}")

    def _restore_splitter_state(self):
        """Restore sidebar splitter position after window geometry is resolved."""
        settings = QSettings("CellCounter", "Layout")
        state = settings.value("sidebar_splitter")
        if state:
            self.outer_splitter.restoreState(state)

    def closeEvent(self, event):
        settings = QSettings("CellCounter", "Layout")
        settings.setValue("sidebar_splitter", self.outer_splitter.saveState())
        super().closeEvent(event)

    def _connect_signals(self):
        """Wire up signals to slots."""
        self.open_btn.clicked.connect(self._on_open_images)
        self.image_list.currentItemChanged.connect(self._on_image_selected)
        self.clear_btn.clicked.connect(self._on_clear)
        self.analyze_btn.clicked.connect(self._on_analyze)
        self.auto_optimize_btn.clicked.connect(self._on_auto_optimize)
        self.annotated_label.clicked.connect(self._on_annotated_click)
        self.undo_mark_btn.clicked.connect(self._on_undo_mark)
        self.save_batch_btn.clicked.connect(self._on_save_batch)
        self.open_batch_btn.clicked.connect(self._on_open_batch)
        self.add_images_btn.clicked.connect(self._on_add_images)
        self.remove_image_btn.clicked.connect(self._on_remove_image)
        self.re_analyze_btn.clicked.connect(self._on_re_analyze)
        self.export_csv_btn.clicked.connect(self._on_export_csv)
        self.orig_zoom_in_btn.clicked.connect(self.original_label.zoom_in)
        self.orig_zoom_out_btn.clicked.connect(self.original_label.zoom_out)
        self.orig_zoom_reset_btn.clicked.connect(self.original_label.zoom_reset)
        self.ann_zoom_in_btn.clicked.connect(self.annotated_label.zoom_in)
        self.ann_zoom_out_btn.clicked.connect(self.annotated_label.zoom_out)
        self.ann_zoom_reset_btn.clicked.connect(self.annotated_label.zoom_reset)

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
        self._update_batch_buttons()
        self._update_status_bar()

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

        # Reset zoom before showing new image
        self.original_label.zoom_reset()
        self.annotated_label.zoom_reset()

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
        """MARK-01: Toggle algo marks or add manual marks at the clicked position."""
        if self._current_file is None:
            return
        entry = self._images.get(self._current_file)
        if entry is None or entry["annotated_rgb"] is None:
            return

        # 1. Check algo centroids — toggle remove/restore
        removed = set(entry.get("removed_indices", []))
        for i, (cx, cy) in enumerate(entry.get("algo_centroids", [])):
            if (orig_x - cx) ** 2 + (orig_y - cy) ** 2 <= self.CIRCLE_RADIUS ** 2:
                if i in removed:
                    removed.discard(i)    # re-mark
                else:
                    removed.add(i)        # unmark
                entry["removed_indices"] = list(removed)
                self._redraw_annotated()
                return

        # 2. Check manual marks — remove on click
        for i, (mx, my) in enumerate(entry["manual_marks"]):
            if (orig_x - mx) ** 2 + (orig_y - my) ** 2 <= self.CIRCLE_RADIUS ** 2:
                entry["manual_marks"].pop(i)
                self._redraw_annotated()
                self.undo_mark_btn.setEnabled(bool(entry["manual_marks"]))
                return

        # 3. No hit — add new manual mark
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

    CIRCLE_RADIUS = 18

    def _redraw_annotated(self):
        """Redraw the annotated image from original_rgb using centroids state and manual marks."""
        if self._current_file is None:
            return
        entry = self._images.get(self._current_file)
        if entry is None or entry.get("annotated_rgb") is None:
            return
        base = entry["original_rgb"].copy()
        removed = set(entry.get("removed_indices", []))
        active = [(i, c) for i, c in enumerate(entry.get("algo_centroids", [])) if i not in removed]
        for n, (i, (cx, cy)) in enumerate(active, 1):
            cv2.circle(base, (cx, cy), self.CIRCLE_RADIUS, (0, 0, 255), 2)
            cv2.putText(base, str(n), (cx - 10, cy - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        from analysis_core import draw_manual_marks
        display = draw_manual_marks(base, entry["manual_marks"])
        self.annotated_label.setPixmap(numpy_rgb_to_pixmap(display))
        self.annotated_label.setText("")
        total = len(active) + len(entry["manual_marks"])
        self.count_label.setText(f"Cell Count: {total}")
        self._update_results_row(self._current_file, total)
        self._update_status_bar()

    def _on_clear(self):
        """CLR-01: Reset all state to defaults."""
        # Clear image data
        self._images.clear()
        self._file_paths.clear()
        self._current_file = None
        self._current_batch_dir = None

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

        # Reset window title
        self.setWindowTitle("Cell Counter")
        self._update_batch_buttons()
        self._update_status_bar()

    # ---- Analysis worker slots ----

    def _collect_params(self) -> dict:
        """Return current parameter values from the param panel."""
        return self.param_panel.get_params()

    def _on_analyze(self):
        """Start background analysis of all loaded images."""
        if not self._images:
            return
        from workers.analysis_worker import AnalysisWorker
        self._is_analyzing = True
        self._disable_batch_buttons_during_analysis()
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

    def _on_image_done(self, filename: str, annotated_rgb, count: int, centroids):
        """Handle completion of a single image analysis."""
        self._images[filename]["annotated_rgb"] = annotated_rgb
        self._images[filename]["algo_count"] = count
        self._images[filename]["algo_centroids"] = list(centroids) if centroids else []
        self._images[filename]["removed_indices"] = []   # reset on fresh analysis
        self._update_results_row(filename, count)
        if filename == self._current_file:
            self._redraw_annotated()
        self._update_status_bar()

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
        self._is_analyzing = False
        self.analyze_btn.setEnabled(True)
        self.auto_optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis complete")
        self._update_batch_buttons()

    def _update_results_row(self, filename: str, count: int, is_error: bool = False):
        """Update or insert a row in the results table for the given filename."""
        count_text = "0 (warning)" if is_error else str(count)
        # Search for existing row (skip Total row)
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item and item.text() == filename:
                self.results_table.setItem(row, 1, QTableWidgetItem(count_text))
                self._refresh_total_row()
                return
        # Insert new row
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(filename))
        self.results_table.setItem(row, 1, QTableWidgetItem(count_text))
        self._refresh_total_row()

    def _refresh_total_row(self):
        """Remove any existing Total row, sum all image rows, re-append Total at the end."""
        # Remove existing Total row first
        for row in range(self.results_table.rowCount() - 1, -1, -1):
            item = self.results_table.item(row, 0)
            if item and item.text() == "Total":
                self.results_table.removeRow(row)
                break

        # Sum remaining (image) rows
        total = 0
        for row in range(self.results_table.rowCount()):
            count_item = self.results_table.item(row, 1)
            if count_item:
                text = count_item.text().split()[0]
                try:
                    total += int(text)
                except ValueError:
                    pass

        bold_font = QFont()
        bold_font.setBold(True)

        last = self.results_table.rowCount()
        self.results_table.insertRow(last)
        label_item = QTableWidgetItem("Total")
        label_item.setFont(bold_font)
        count_item = QTableWidgetItem(str(total))
        count_item.setFont(bold_font)
        self.results_table.setItem(last, 0, label_item)
        self.results_table.setItem(last, 1, count_item)

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

    # ---- Batch management slots ----

    def _update_batch_buttons(self):
        """Enable/disable batch buttons based on state."""
        has_images = bool(self._images)
        is_open = self._current_batch_dir is not None
        is_analyzing = getattr(self, '_is_analyzing', False)
        self.save_batch_btn.setEnabled(has_images and not is_analyzing)
        self.add_images_btn.setEnabled(is_open and not is_analyzing)
        self.remove_image_btn.setEnabled(is_open and self._current_file is not None and not is_analyzing)
        self.re_analyze_btn.setEnabled(is_open and has_images and not is_analyzing)
        self.export_csv_btn.setEnabled(is_open and not is_analyzing)

    def _disable_batch_buttons_during_analysis(self):
        """Disable all batch mutation buttons while analysis is running."""
        self.save_batch_btn.setEnabled(False)
        self.add_images_btn.setEnabled(False)
        self.remove_image_btn.setEnabled(False)
        self.re_analyze_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(False)

    def _on_save_batch(self):
        """Save current session as a named batch.

        If a batch is already open, overwrites it in-place without prompting.
        Otherwise, prompts for a batch name and saves to a new directory.
        """
        params = self.param_panel.get_params()
        if self._current_batch_dir is not None:
            BatchManager.update_manifest(self._current_batch_dir, self._images, params)
            self.statusBar().showMessage("Batch saved", 2500)
            return
        name, ok = QInputDialog.getText(self, "Save Batch", "Batch name:")
        if not ok or not name.strip():
            return
        batch_dir = BatchManager.save_batch(name.strip(), self._images, params)
        self._current_batch_dir = batch_dir
        self.setWindowTitle(f"Cell Counter — {name.strip()}")
        self.status_label.setText(f"Batch saved: {batch_dir.name}")

    def _on_open_batch(self):
        """Show dialog to open a saved batch."""
        batches = BatchManager.list_batches()
        if not batches:
            QMessageBox.information(self, "Open Batch", "No saved batches found.")
            return
        dlg = OpenBatchDialog(batches, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        batch_path = dlg.selected_path()
        if batch_path is None:
            return
        self._load_batch_from_path(batch_path)

    def _load_batch_from_path(self, batch_dir):
        """Restore application state from a saved batch directory.

        Clears current state, then loads images, parameters, annotated results,
        and manual marks from the batch. Warns if any images are missing.
        """
        from pathlib import Path
        batch_dir = Path(batch_dir)

        # Reset current state first
        self._on_clear()

        manifest = BatchManager.load_batch(batch_dir)
        self._current_batch_dir = batch_dir
        self.param_panel.set_params(manifest["parameters"])

        missing_count = 0
        for entry in manifest["images"]:
            if entry["status"] == "missing":
                missing_count += 1
                continue

            filename = entry["filename"]
            orig_bgr = cv2.imread(str(batch_dir / filename))
            if orig_bgr is None:
                missing_count += 1
                continue

            orig_rgb = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2RGB)

            # Load annotated image if it exists
            annotated_rgb = None
            if entry.get("annotated_filename"):
                ann_path = batch_dir / entry["annotated_filename"]
                if ann_path.exists():
                    ann_bgr = cv2.imread(str(ann_path))
                    if ann_bgr is not None:
                        annotated_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)

            self._images[filename] = {
                "original_bgr": orig_bgr,
                "original_rgb": orig_rgb,
                "annotated_rgb": annotated_rgb,
                "algo_count": entry.get("cell_count", 0),
                "manual_marks": list(entry.get("manual_marks", [])),
                "algo_centroids": [tuple(c) for c in entry.get("algo_centroids", [])],
                "removed_indices": list(entry.get("removed_indices", [])),
            }
            self._file_paths.append(str(batch_dir / filename))
            self.image_list.addItem(filename)
            total = entry.get("cell_count", 0) + len(entry.get("manual_marks", []))
            self._update_results_row(filename, total)

        if self._images:
            self.analyze_btn.setEnabled(True)
            self.auto_optimize_btn.setEnabled(True)
            if self.image_list.currentRow() < 0:
                self.image_list.setCurrentRow(0)

        if missing_count > 0:
            QMessageBox.warning(
                self,
                "Missing Images",
                f"{missing_count} image(s) could not be found and were skipped."
            )

        batch_name = manifest.get("name", batch_dir.name)
        self.setWindowTitle(f"Cell Counter — {batch_name}")
        self.status_label.setText(f"Batch opened: {batch_name}")
        self._update_batch_buttons()
        self._update_status_bar()

    def _on_add_images(self):
        """Add new images to the currently open batch."""
        if self._current_batch_dir is None:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Images", "", self.get_file_filter())
        if not paths:
            return
        from pathlib import Path as _Path
        added = BatchManager.add_images(self._current_batch_dir, paths)
        # Load each added image into self._images
        for fn in added:
            img_path = self._current_batch_dir / fn
            bgr = cv2.imread(str(img_path))
            if bgr is None:
                continue
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            self._images[fn] = {
                "original_bgr": bgr, "original_rgb": rgb,
                "annotated_rgb": None, "algo_count": 0, "manual_marks": [],
            }
            self.image_list.addItem(fn)
        if added:
            self.analyze_btn.setEnabled(True)
            self.auto_optimize_btn.setEnabled(True)
        self._update_batch_buttons()

    def _on_remove_image(self):
        """Remove the currently selected image from the batch manifest (file stays on disk)."""
        if self._current_batch_dir is None or self._current_file is None:
            return
        fn = self._current_file
        BatchManager.remove_image(self._current_batch_dir, fn)
        # Remove from _images dict
        self._images.pop(fn, None)
        # Remove from image_list widget
        for i in range(self.image_list.count()):
            if self.image_list.item(i).text() == fn:
                self.image_list.takeItem(i)
                break
        self._current_file = None
        # Clear display
        self.original_label.clearPixmap()
        self.original_label.setText("Original")
        self.annotated_label.clearPixmap()
        self.annotated_label.setText("Annotated")
        self.count_label.setText("Cell Count: 0")
        self._update_batch_buttons()
        self._update_status_bar()

    def _on_re_analyze(self):
        """Re-analyze all batch images with current parameters, preserving manual marks."""
        if self._current_batch_dir is None or not self._images:
            return
        from workers.analysis_worker import AnalysisWorker
        # Back up manual marks BEFORE re-analysis (BMGR-06: marks preserved)
        self._marks_backup = {fn: list(entry["manual_marks"]) for fn, entry in self._images.items()}
        params = self._collect_params()
        self._is_analyzing = True
        self._disable_batch_buttons_during_analysis()
        self.analyze_btn.setEnabled(False)
        self.auto_optimize_btn.setEnabled(False)
        self.progress_bar.setMaximum(len(self._images))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Re-analyzing...")
        worker = AnalysisWorker(self._images, params)
        worker.signals.image_done.connect(self._on_reanalyze_image_done)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_reanalyze_finished)
        worker.signals.error.connect(self._on_image_error)
        QThreadPool.globalInstance().start(worker)

    def _on_reanalyze_image_done(self, filename: str, annotated_rgb, count: int, centroids):
        """Handle completion of a single image during re-analysis."""
        self._images[filename]["annotated_rgb"] = annotated_rgb
        self._images[filename]["algo_count"] = count
        self._images[filename]["algo_centroids"] = list(centroids) if centroids else []
        self._images[filename]["removed_indices"] = []   # reset: old indices are stale
        # Restore manual marks from backup (BMGR-06)
        self._images[filename]["manual_marks"] = self._marks_backup.get(filename, [])
        if filename == self._current_file:
            self._redraw_annotated()
        active_algo = len(self._images[filename]["algo_centroids"])
        total = active_algo + len(self._images[filename]["manual_marks"])
        self._update_results_row(filename, total)
        self._update_status_bar()

    def _on_reanalyze_finished(self):
        """Handle re-analysis completion: update manifest and restore button state."""
        self._is_analyzing = False
        self._marks_backup = {}
        self.analyze_btn.setEnabled(True)
        self.auto_optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        # Update manifest with new results
        BatchManager.update_manifest(self._current_batch_dir, self._images, self._collect_params())
        self._update_batch_buttons()
        self.statusBar().showMessage("Re-analysis complete", 3000)
        self.status_label.setText("Re-analysis complete")

    def _on_export_csv(self):
        """Export batch results to a CSV file."""
        if self._current_batch_dir is None:
            return
        from pathlib import Path as _Path
        manifest = BatchManager.load_batch(self._current_batch_dir)
        default_name = f"{manifest['name']}_results.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", default_name, "CSV files (*.csv)")
        if not path:
            return
        BatchManager.export_csv(manifest, _Path(path))
        self.statusBar().showMessage(f"Exported to {path}", 3000)
        self.status_label.setText(f"Exported: {default_name}")
