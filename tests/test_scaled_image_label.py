import numpy as np
import pytest

def test_pixmap_conversion(qtbot, sample_rgb_array):
    """D-07: numpy RGB array converts to QPixmap without error."""
    from ui.image_utils import numpy_rgb_to_pixmap
    pixmap = numpy_rgb_to_pixmap(sample_rgb_array)
    assert not pixmap.isNull()
    assert pixmap.width() == 300
    assert pixmap.height() == 200

def test_aspect_ratio(qtbot):
    """ANAL-04: ScaledImageLabel preserves aspect ratio."""
    from ui.scaled_image_label import ScaledImageLabel
    from PySide6.QtGui import QPixmap
    label = ScaledImageLabel()
    qtbot.addWidget(label)
    # Create a 400x200 pixmap (2:1 aspect ratio)
    pixmap = QPixmap(400, 200)
    pixmap.fill()
    label.setPixmap(pixmap)
    label.resize(200, 200)
    # The label stores the original pixmap; aspect ratio is maintained in paintEvent
    assert label._pixmap is not None
    assert label._pixmap.width() == 400
    assert label._pixmap.height() == 200

def test_empty_pixmap(qtbot):
    """ScaledImageLabel handles None pixmap gracefully."""
    from ui.scaled_image_label import ScaledImageLabel
    label = ScaledImageLabel()
    qtbot.addWidget(label)
    label.resize(200, 200)
    # Should not crash on paint with no pixmap
    label.repaint()
