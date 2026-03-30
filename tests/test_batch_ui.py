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
