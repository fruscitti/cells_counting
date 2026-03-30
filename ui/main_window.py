import os
import cv2

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QDialog, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThreadPool
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
        self.save_batch_btn.clicked.connect(self._on_save_batch)
        self.open_batch_btn.clicked.connect(self._on_open_batch)
        self.add_images_btn.clicked.connect(self._on_add_images)
        self.remove_image_btn.clicked.connect(self._on_remove_image)
        self.re_analyze_btn.clicked.connect(self._on_re_analyze)
        self.export_csv_btn.clicked.connect(self._on_export_csv)

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

    def _on_reanalyze_image_done(self, filename: str, annotated_rgb, count: int):
        """Handle completion of a single image during re-analysis."""
        self._images[filename]["annotated_rgb"] = annotated_rgb
        self._images[filename]["algo_count"] = count
        # Restore manual marks from backup (BMGR-06)
        self._images[filename]["manual_marks"] = self._marks_backup.get(filename, [])
        if filename == self._current_file:
            self._redraw_annotated()
        total = count + len(self._images[filename]["manual_marks"])
        self._update_results_row(filename, total)

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
