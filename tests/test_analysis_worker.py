import pytest
import numpy as np


def test_background_thread(qtbot):
    """ANAL-02: AnalysisWorker runs in background and emits signals."""
    from workers.analysis_worker import AnalysisWorker
    from PySide6.QtCore import QThreadPool

    # Create a simple test image
    img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    img_bgr[40:60, 40:60, 1] = 255  # green square

    images = {"test.png": {"original_bgr": img_bgr}}
    params = {
        "brightness_threshold": 120, "min_cell_area": 25,
        "blur_strength": 9, "use_cleaning": True,
        "max_cell_area": 500, "use_tophat": False,
        "tophat_kernel": 50, "adaptive_block": 99, "adaptive_c": -5,
    }

    worker = AnalysisWorker(images, params)
    results = []
    worker.signals.image_done.connect(lambda fn, arr, c: results.append((fn, c)))

    with qtbot.waitSignal(worker.signals.finished, timeout=10000):
        QThreadPool.globalInstance().start(worker)

    assert len(results) == 1
    assert results[0][0] == "test.png"
    assert isinstance(results[0][1], int)


def test_progress_emitted(qtbot):
    """ANAL-03: AnalysisWorker emits progress signal with (current, total)."""
    from workers.analysis_worker import AnalysisWorker
    from PySide6.QtCore import QThreadPool

    img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    img_bgr[40:60, 40:60, 1] = 255

    images = {
        "a.png": {"original_bgr": img_bgr},
        "b.png": {"original_bgr": img_bgr.copy()},
    }
    params = {
        "brightness_threshold": 120, "min_cell_area": 25,
        "blur_strength": 9, "use_cleaning": True,
        "max_cell_area": 500, "use_tophat": False,
        "tophat_kernel": 50, "adaptive_block": 99, "adaptive_c": -5,
    }

    worker = AnalysisWorker(images, params)
    progress_values = []
    worker.signals.progress.connect(lambda cur, tot: progress_values.append((cur, tot)))

    with qtbot.waitSignal(worker.signals.finished, timeout=10000):
        QThreadPool.globalInstance().start(worker)

    # Should have emitted progress for each image: (1, 2) and (2, 2)
    assert len(progress_values) == 2
    assert progress_values[-1] == (2, 2)


def test_worker_error_signal(qtbot):
    """ANAL-02: AnalysisWorker emits error for invalid images."""
    from workers.analysis_worker import AnalysisWorker
    from PySide6.QtCore import QThreadPool

    # Empty image should cause an error in process_image
    images = {"bad.png": {"original_bgr": np.zeros((0, 0, 3), dtype=np.uint8)}}
    params = {
        "brightness_threshold": 120, "min_cell_area": 25,
        "blur_strength": 9, "use_cleaning": True,
        "max_cell_area": 500, "use_tophat": False,
        "tophat_kernel": 50, "adaptive_block": 99, "adaptive_c": -5,
    }

    worker = AnalysisWorker(images, params)
    errors = []
    worker.signals.error.connect(lambda fn, msg: errors.append(fn))

    with qtbot.waitSignal(worker.signals.finished, timeout=10000):
        QThreadPool.globalInstance().start(worker)

    assert len(errors) == 1
    assert errors[0] == "bad.png"
