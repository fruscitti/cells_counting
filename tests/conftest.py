import numpy as np
import pytest
import os
import sys

# Ensure offscreen rendering for CI/headless
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

@pytest.fixture
def sample_rgb_array():
    """200x300 RGB uint8 test image with some bright spots."""
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    img[50:60, 50:60] = [0, 255, 0]  # green spot
    img[100:110, 150:160] = [0, 200, 0]  # another green spot
    return img

@pytest.fixture
def sample_bgr_array(sample_rgb_array):
    """BGR version of the sample image."""
    import cv2
    return cv2.cvtColor(sample_rgb_array, cv2.COLOR_RGB2BGR)

@pytest.fixture
def main_window(qtbot):
    from ui.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    return w
