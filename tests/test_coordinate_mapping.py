import numpy as np
import pytest


def test_click_mapping(qtbot):
    """MARK-01: Click coordinates map correctly from label space to original image space."""
    from ui.scaled_image_label import ScaledImageLabel
    from PySide6.QtGui import QPixmap

    label = ScaledImageLabel(click_enabled=True)
    qtbot.addWidget(label)

    # Create a 400x200 pixmap (2:1 ratio)
    pixmap = QPixmap(400, 200)
    pixmap.fill()
    label.setPixmap(pixmap)
    label.resize(200, 200)  # Square label, image will be letterboxed

    # The scaled image in a 200x200 label: scaled to 200x100, centered vertically
    # y_offset = (200 - 100) / 2 = 50
    # A click at label (100, 100) = image (100, 50) in scaled space
    # Scale back: orig_x = 100 * 400/200 = 200, orig_y = 50 * 200/100 = 100

    coords = []
    label.clicked.connect(lambda x, y: coords.append((x, y)))

    # Simulate click at center of label
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QEvent, Qt
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(100, 100),
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier
    )
    label.mousePressEvent(event)

    assert len(coords) == 1
    orig_x, orig_y = coords[0]
    # With 400x200 pixmap in 200x200 label:
    # scaled size = 200x100, offset_y = 50
    # click (100, 100) -> image_x=100, image_y=100-50=50
    # orig_x = 100 * 400/200 = 200, orig_y = 50 * 200/100 = 100
    assert orig_x == 200
    assert orig_y == 100


def test_click_outside_image_rejected(qtbot):
    """MARK-01: Clicks outside letterboxed image area are rejected."""
    from ui.scaled_image_label import ScaledImageLabel
    from PySide6.QtGui import QPixmap

    label = ScaledImageLabel(click_enabled=True)
    qtbot.addWidget(label)

    pixmap = QPixmap(400, 200)
    pixmap.fill()
    label.setPixmap(pixmap)
    label.resize(200, 200)

    coords = []
    label.clicked.connect(lambda x, y: coords.append((x, y)))

    # Click in the letterbox area (top padding, y < 50)
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QEvent, Qt
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(100, 10),  # y=10 is in the letterbox padding
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier
    )
    label.mousePressEvent(event)

    assert len(coords) == 0  # Click rejected


def test_undo_mark(qtbot):
    """MARK-02: Undo removes last manual mark."""
    from ui.main_window import MainWindow
    import cv2

    w = MainWindow()
    qtbot.addWidget(w)

    # Create a simple test image and load it
    img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    img_bgr[40:60, 40:60, 1] = 255

    # Manually populate state (simulating analysis done)
    filename = "test.png"
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    from analysis_core import process_image
    ann_bgr, count = process_image(img_bgr, 120, 25, 9, True)
    ann_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)

    w._images[filename] = {
        "original_bgr": img_bgr,
        "original_rgb": img_rgb,
        "annotated_rgb": ann_rgb,
        "algo_count": count,
        "manual_marks": [(50, 50), (60, 60)]
    }
    w._current_file = filename

    # Undo should remove last mark
    w._on_undo_mark()
    assert len(w._images[filename]["manual_marks"]) == 1
    assert w._images[filename]["manual_marks"][0] == (50, 50)

    # Undo again
    w._on_undo_mark()
    assert len(w._images[filename]["manual_marks"]) == 0
