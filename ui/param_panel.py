from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QSpinBox,
    QCheckBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal


class OddSpinBox(QSpinBox):
    """Spinbox that enforces odd values (for OpenCV kernel sizes)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(1)
        self.setMaximum(31)
        self.setSingleStep(2)
        self.setValue(9)

    def stepBy(self, steps):
        super().stepBy(steps)
        if self.value() % 2 == 0:
            self.setValue(self.value() + 1)


class ParamPanel(QWidget):
    params_changed = Signal()  # emitted when any parameter changes

    # Default values (used by Clear/Reset)
    DEFAULTS = {
        "brightness_threshold": 120,
        "min_cell_area": 25,
        "blur_strength": 9,
        "max_cell_area": 500,
        "use_cleaning": True,
        "use_tophat": False,
        "tophat_kernel": 50,
        "adaptive_block": 99,
        "adaptive_c": -5,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # --- Brightness Threshold ---
        layout.addWidget(QLabel("Brightness Threshold"))
        row = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(255)
        self.brightness_slider.setSingleStep(1)
        self.brightness_slider.setValue(120)
        self.brightness_value = QLabel("120")
        self.brightness_value.setFixedWidth(35)
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_value.setText(str(v))
        )
        row.addWidget(self.brightness_slider)
        row.addWidget(self.brightness_value)
        layout.addLayout(row)

        # --- Min Cell Area ---
        layout.addWidget(QLabel("Min Cell Area (px)"))
        row = QHBoxLayout()
        self.min_area_slider = QSlider(Qt.Horizontal)
        self.min_area_slider.setMinimum(1)
        self.min_area_slider.setMaximum(500)
        self.min_area_slider.setSingleStep(1)
        self.min_area_slider.setValue(25)
        self.min_area_value = QLabel("25")
        self.min_area_value.setFixedWidth(35)
        self.min_area_slider.valueChanged.connect(
            lambda v: self.min_area_value.setText(str(v))
        )
        row.addWidget(self.min_area_slider)
        row.addWidget(self.min_area_value)
        layout.addLayout(row)

        # --- Blur Strength ---
        layout.addWidget(QLabel("Blur Strength (odd)"))
        self.blur_spinbox = OddSpinBox()
        layout.addWidget(self.blur_spinbox)

        # --- Max Cell Area ---
        layout.addWidget(QLabel("Max Cell Area (px)"))
        row = QHBoxLayout()
        self.max_area_spinbox = QSpinBox()
        self.max_area_spinbox.setMinimum(50)
        self.max_area_spinbox.setMaximum(5000)
        self.max_area_spinbox.setSingleStep(10)
        self.max_area_spinbox.setValue(500)
        self.max_area_value = QLabel("500")
        self.max_area_value.setFixedWidth(40)
        self.max_area_spinbox.valueChanged.connect(
            lambda v: self.max_area_value.setText(str(v))
        )
        row.addWidget(self.max_area_spinbox)
        row.addWidget(self.max_area_value)
        layout.addLayout(row)

        # --- Use Cleaning ---
        self.cleaning_checkbox = QCheckBox("Use Cleaning")
        self.cleaning_checkbox.setChecked(True)
        layout.addWidget(self.cleaning_checkbox)

        # --- Use Top-Hat ---
        self.tophat_checkbox = QCheckBox("Use Top-Hat")
        self.tophat_checkbox.setChecked(False)
        layout.addWidget(self.tophat_checkbox)

        # Top-Hat sub-controls container
        self.tophat_container = QWidget()
        tophat_layout = QVBoxLayout(self.tophat_container)
        tophat_layout.setContentsMargins(12, 0, 0, 0)
        tophat_layout.setSpacing(4)

        # Top-Hat Kernel
        tophat_layout.addWidget(QLabel("Top-Hat Kernel Size"))
        row = QHBoxLayout()
        self.tophat_kernel_slider = QSlider(Qt.Horizontal)
        self.tophat_kernel_slider.setMinimum(10)
        self.tophat_kernel_slider.setMaximum(200)
        self.tophat_kernel_slider.setSingleStep(5)
        self.tophat_kernel_slider.setValue(50)
        self.tophat_kernel_value = QLabel("50")
        self.tophat_kernel_value.setFixedWidth(35)
        self.tophat_kernel_slider.valueChanged.connect(
            lambda v: self.tophat_kernel_value.setText(str(v))
        )
        row.addWidget(self.tophat_kernel_slider)
        row.addWidget(self.tophat_kernel_value)
        tophat_layout.addLayout(row)

        # Adaptive Block Size
        tophat_layout.addWidget(QLabel("Adaptive Block Size (odd)"))
        self.adaptive_block_spinbox = OddSpinBox()
        self.adaptive_block_spinbox.setMinimum(3)
        self.adaptive_block_spinbox.setMaximum(199)
        self.adaptive_block_spinbox.setValue(99)
        tophat_layout.addWidget(self.adaptive_block_spinbox)

        # Adaptive C
        tophat_layout.addWidget(QLabel("Adaptive C"))
        row = QHBoxLayout()
        self.adaptive_c_slider = QSlider(Qt.Horizontal)
        self.adaptive_c_slider.setMinimum(-50)
        self.adaptive_c_slider.setMaximum(50)
        self.adaptive_c_slider.setSingleStep(1)
        self.adaptive_c_slider.setValue(-5)
        self.adaptive_c_value = QLabel("-5")
        self.adaptive_c_value.setFixedWidth(35)
        self.adaptive_c_slider.valueChanged.connect(
            lambda v: self.adaptive_c_value.setText(str(v))
        )
        row.addWidget(self.adaptive_c_slider)
        row.addWidget(self.adaptive_c_value)
        tophat_layout.addLayout(row)

        layout.addWidget(self.tophat_container)
        self.tophat_container.setVisible(False)
        self.tophat_checkbox.toggled.connect(self.tophat_container.setVisible)

    def get_params(self) -> dict:
        """Return current parameter values as a dict matching process_image kwargs."""
        blur = self.blur_spinbox.value()
        # Ensure blur is odd (in case direct setValue was called with even number)
        if blur % 2 == 0:
            blur += 1
        return {
            "brightness_threshold": self.brightness_slider.value(),
            "min_cell_area": self.min_area_slider.value(),
            "blur_strength": blur,
            "max_cell_area": self.max_area_spinbox.value(),
            "use_cleaning": self.cleaning_checkbox.isChecked(),
            "use_tophat": self.tophat_checkbox.isChecked(),
            "tophat_kernel": self.tophat_kernel_slider.value(),
            "adaptive_block": self.adaptive_block_spinbox.value(),
            "adaptive_c": self.adaptive_c_slider.value(),
        }

    def set_params(self, params: dict):
        """Set controls from a dict. Supports partial dicts — only updates keys present."""
        if "brightness_threshold" in params:
            self.brightness_slider.setValue(params["brightness_threshold"])
        if "min_cell_area" in params:
            self.min_area_slider.setValue(params["min_cell_area"])
        if "blur_strength" in params:
            self.blur_spinbox.setValue(params["blur_strength"])
        if "max_cell_area" in params:
            self.max_area_spinbox.setValue(params["max_cell_area"])
        if "use_cleaning" in params:
            self.cleaning_checkbox.setChecked(params["use_cleaning"])
        if "use_tophat" in params:
            self.tophat_checkbox.setChecked(params["use_tophat"])
        if "tophat_kernel" in params:
            self.tophat_kernel_slider.setValue(params["tophat_kernel"])
        if "adaptive_block" in params:
            self.adaptive_block_spinbox.setValue(params["adaptive_block"])
        if "adaptive_c" in params:
            self.adaptive_c_slider.setValue(params["adaptive_c"])

    def reset_defaults(self):
        """Reset all controls to default values."""
        self.set_params(self.DEFAULTS)
