from PySide6.QtGui import QImage, QPixmap
import numpy as np


def numpy_rgb_to_pixmap(rgb_array: np.ndarray) -> QPixmap:
    """Convert H x W x 3 uint8 RGB array to QPixmap. Thread-safe via .copy()."""
    h, w, ch = rgb_array.shape
    assert ch == 3 and rgb_array.dtype == np.uint8
    bytes_per_line = ch * w
    qimg = QImage(rgb_array.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)
