import os
import cv2

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog
)
from PySide6.QtCore import Qt
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

        self.annotated_label = ScaledImageLabel(click_enabled=False)
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

        # Show annotated image if available, otherwise clear
        if entry["annotated_rgb"] is not None:
            self.annotated_label.setPixmap(numpy_rgb_to_pixmap(entry["annotated_rgb"]))
            self.annotated_label.setText("")
        else:
            self.annotated_label.clearPixmap()
            self.annotated_label.setText("Annotated")

        # Update count label
        total = entry["algo_count"] + len(entry["manual_marks"])
        self.count_label.setText(f"Cell Count: {total}")

    def _on_clear(self):
        """Clear all loaded images and reset the UI."""
        self._images.clear()
        self._file_paths.clear()
        self._current_file = None
        self.image_list.clear()
        self.original_label.clearPixmap()
        self.original_label.setText("Original")
        self.annotated_label.clearPixmap()
        self.annotated_label.setText("Annotated")
        self.count_label.setText("Cell Count: 0")
        self.analyze_btn.setEnabled(False)
        self.auto_optimize_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        self.status_label.setText("Ready")
