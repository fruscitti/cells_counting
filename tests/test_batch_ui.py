"""Qt integration tests for Save/Open Batch buttons and dialogs."""
import numpy as np
import pytest
from pathlib import Path


def test_save_batch_button_exists(main_window):
    """BATCH-01: Save Batch button exists in MainWindow with correct text."""
    assert hasattr(main_window, "save_batch_btn"), "save_batch_btn should exist"
    assert main_window.save_batch_btn.text() == "Save Batch"


def test_open_batch_button_exists(main_window):
    """BMGR-01: Open Batch button exists in MainWindow with correct text."""
    assert hasattr(main_window, "open_batch_btn"), "open_batch_btn should exist"
    assert main_window.open_batch_btn.text() == "Open Batch"


def test_save_batch_btn_disabled_when_no_images(main_window):
    """Save Batch button is disabled when no images are loaded."""
    assert not main_window.save_batch_btn.isEnabled(), \
        "save_batch_btn should be disabled when no images loaded"


def test_open_batch_dialog_creation(qtbot):
    """OpenBatchDialog shows correct number of batches in the list."""
    from ui.batch_dialogs import OpenBatchDialog
    batches = [
        {"name": "batch-a", "path": Path("/tmp/batch-a"), "created_at": "2026-03-30T10:00:00+00:00", "image_count": 3},
        {"name": "batch-b", "path": Path("/tmp/batch-b"), "created_at": "2026-03-29T10:00:00+00:00", "image_count": 5},
    ]
    dlg = OpenBatchDialog(batches)
    qtbot.addWidget(dlg)
    assert dlg._list.count() == 2, "dialog list should have 2 items"
    # Verify item text format
    item_text = dlg._list.item(0).text()
    assert "batch-a" in item_text
    assert "2026-03-30" in item_text
    assert "3 images" in item_text


def test_open_batch_dialog_selected_path(qtbot):
    """OpenBatchDialog.selected_path() returns the Path of the selected item."""
    from ui.batch_dialogs import OpenBatchDialog
    path_a = Path("/tmp/batch-a")
    batches = [
        {"name": "batch-a", "path": path_a, "created_at": "2026-03-30T10:00:00+00:00", "image_count": 2},
    ]
    dlg = OpenBatchDialog(batches)
    qtbot.addWidget(dlg)
    # Nothing selected initially
    assert dlg.selected_path() is None
    # Select first item
    dlg._list.setCurrentRow(0)
    assert dlg.selected_path() == path_a, "selected_path() should return path from item data"


def test_save_batch_btn_enabled_after_load(qtbot, tmp_path):
    """Save Batch button becomes enabled after images are loaded."""
    import cv2
    from ui.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)

    assert not w.save_batch_btn.isEnabled(), "button should start disabled"

    img_bgr = np.zeros((50, 50, 3), dtype=np.uint8)
    img_path = str(tmp_path / "test.png")
    cv2.imwrite(img_path, img_bgr)
    w.load_images([img_path])

    assert w.save_batch_btn.isEnabled(), "button should be enabled after loading images"


# ---- New tests for Plan 02 batch mutation buttons ----

def test_add_images_btn_disabled_no_batch(main_window):
    """Add Images button is disabled when no batch is open."""
    assert hasattr(main_window, "add_images_btn"), "add_images_btn should exist"
    assert not main_window.add_images_btn.isEnabled(), \
        "add_images_btn should be disabled when no batch is open"


def test_remove_image_btn_disabled_no_batch(main_window):
    """Remove Image button is disabled when no batch is open."""
    assert hasattr(main_window, "remove_image_btn"), "remove_image_btn should exist"
    assert not main_window.remove_image_btn.isEnabled(), \
        "remove_image_btn should be disabled when no batch is open"


def test_re_analyze_btn_disabled_no_batch(main_window):
    """Re-Analyze button is disabled when no batch is open."""
    assert hasattr(main_window, "re_analyze_btn"), "re_analyze_btn should exist"
    assert not main_window.re_analyze_btn.isEnabled(), \
        "re_analyze_btn should be disabled when no batch is open"


def test_export_csv_btn_disabled_no_batch(main_window):
    """Export CSV button is disabled when no batch is open."""
    assert hasattr(main_window, "export_csv_btn"), "export_csv_btn should exist"
    assert not main_window.export_csv_btn.isEnabled(), \
        "export_csv_btn should be disabled when no batch is open"


def test_reanalyze_preserves_marks(qtbot, tmp_path):
    """Re-Analyze re-runs analysis but preserves existing manual marks."""
    import cv2
    from pathlib import Path
    from ui.main_window import MainWindow
    from batch_manager import BatchManager
    from workers.analysis_worker import AnalysisWorker

    PARAMS = {
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

    # Set up a tmp batch
    BatchManager.BATCHES_ROOT = tmp_path / "batches"

    # Create a test image file
    img_bgr = np.zeros((50, 50, 3), dtype=np.uint8)
    img_path = str(tmp_path / "test_img.png")
    cv2.imwrite(img_path, img_bgr)

    w = MainWindow()
    qtbot.addWidget(w)

    # Load the image
    w.load_images([img_path])
    # Add manual marks
    w._images["test_img.png"]["manual_marks"] = [(10, 20), (30, 40)]
    # Simulate an annotated image so redraw doesn't fail
    w._images["test_img.png"]["annotated_rgb"] = np.zeros((50, 50, 3), dtype=np.uint8)

    # Save batch so _current_batch_dir is set
    batch_dir = BatchManager.save_batch("test-reanalyze", w._images, PARAMS)
    w._current_batch_dir = batch_dir
    w._update_batch_buttons()

    # Verify re_analyze_btn is enabled
    assert w.re_analyze_btn.isEnabled(), "re_analyze_btn should be enabled when batch is open"

    original_marks = list(w._images["test_img.png"]["manual_marks"])

    # Intercept _on_reanalyze_finished by capturing when _marks_backup is reset
    # We start re-analyze and use qtbot.waitUntil to poll state
    w._on_re_analyze()

    # Wait until re-analyze has finished (is_analyzing goes back to False)
    qtbot.waitUntil(lambda: not getattr(w, '_is_analyzing', True), timeout=10000)

    marks_after = w._images["test_img.png"]["manual_marks"]
    assert marks_after == original_marks, \
        f"manual marks should be preserved after re-analyze, got {marks_after}"
