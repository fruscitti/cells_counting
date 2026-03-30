import pytest

def test_file_filter(main_window):
    """IMG-01: File dialog filter includes PNG, JPG, TIFF, BMP."""
    # The filter string is stored as an attribute or method
    filter_str = main_window.get_file_filter()
    for ext in ["png", "jpg", "tif", "bmp"]:
        assert ext.lower() in filter_str.lower()

def test_image_list_exists(main_window):
    """IMG-02: Image list widget exists in the main window."""
    assert main_window.image_list is not None
    assert main_window.image_list.count() == 0

def test_image_selection(main_window, qtbot, tmp_path, sample_rgb_array):
    """IMG-03: Selecting an image from the list updates the display."""
    import cv2
    import numpy as np
    # Create a temp image file
    img_path = str(tmp_path / "test.png")
    bgr = cv2.cvtColor(sample_rgb_array, cv2.COLOR_RGB2BGR)
    cv2.imwrite(img_path, bgr)
    # Load it
    main_window.load_images([img_path])
    assert main_window.image_list.count() == 1
    # Select it
    main_window.image_list.setCurrentRow(0)
    # Original label should have a pixmap set
    assert main_window.original_label._pixmap is not None

def test_count_label_initial(main_window):
    """ANAL-05: Cell count label exists and shows 0 by default."""
    assert main_window.count_label is not None
    assert "0" in main_window.count_label.text()

def test_total_count(qtbot):
    """MARK-03: Total count = algo + manual."""
    import cv2
    import numpy as np
    from ui.main_window import MainWindow

    w = MainWindow()
    qtbot.addWidget(w)

    img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    img_bgr[40:60, 40:60, 1] = 255
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    from analysis_core import process_image
    ann_bgr, count = process_image(img_bgr, 120, 25, 9, True)
    ann_rgb = cv2.cvtColor(ann_bgr, cv2.COLOR_BGR2RGB)

    filename = "test.png"
    w._images[filename] = {
        "original_bgr": img_bgr,
        "original_rgb": img_rgb,
        "annotated_rgb": ann_rgb,
        "algo_count": count,
        "manual_marks": [(50, 50)]
    }
    w._current_file = filename
    w._redraw_annotated()

    expected = count + 1  # algo + 1 manual mark
    assert w.count_label.text() == f"Cell Count: {expected}"


def test_clear_resets(qtbot, tmp_path):
    """CLR-01: Clear resets all state to defaults."""
    import cv2
    import numpy as np
    from ui.main_window import MainWindow

    w = MainWindow()
    qtbot.addWidget(w)

    # Load an image
    img_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
    img_path = str(tmp_path / "test.png")
    cv2.imwrite(img_path, img_bgr)
    w.load_images([img_path])
    assert w.image_list.count() == 1

    # Change a parameter
    w.param_panel.brightness_slider.setValue(50)

    # Clear
    w._on_clear()

    # Verify reset
    assert w.image_list.count() == 0
    assert len(w._images) == 0
    assert w._current_file is None
    assert w.param_panel.brightness_slider.value() == 120  # default
    assert w.count_label.text() == "Cell Count: 0"
    assert w.results_table.rowCount() == 0


# --- Phase 4: Layout Foundation ---

def test_splitter_exists(main_window):
    """SIDE-01: Outer horizontal splitter wraps sidebar and image area."""
    from PySide6.QtCore import Qt
    assert hasattr(main_window, "outer_splitter"), "outer_splitter attribute missing"
    assert main_window.outer_splitter.orientation() == Qt.Horizontal

def test_sidebar_minimum_width(main_window):
    """SIDE-02: Sidebar cannot be collapsed to zero; minimum width >= 220."""
    assert hasattr(main_window, "left_scroll"), "left_scroll attribute missing"
    assert main_window.left_scroll.minimumWidth() >= 220

def test_sidebar_no_buttons(main_window):
    """SIDE-03: No QPushButton is a visible widget inside the sidebar scroll area."""
    from PySide6.QtWidgets import QPushButton
    assert hasattr(main_window, "left_scroll"), "left_scroll attribute missing"
    buttons_in_sidebar = main_window.left_scroll.findChildren(QPushButton)
    visible_buttons = [b for b in buttons_in_sidebar if b.isVisibleTo(main_window.left_scroll)]
    assert visible_buttons == [], f"Found visible buttons in sidebar: {[b.text() for b in visible_buttons]}"

def test_status_bar_initial(main_window):
    """STAT-01/02/03: Status bar shows 'No batch', 0 images, 0 cells on startup."""
    assert hasattr(main_window, "_status_batch_lbl"), "_status_batch_lbl missing"
    assert hasattr(main_window, "_status_count_lbl"), "_status_count_lbl missing"
    assert hasattr(main_window, "_status_cells_lbl"), "_status_cells_lbl missing"
    assert main_window._status_batch_lbl.text() == "No batch"
    assert "0" in main_window._status_count_lbl.text()
    assert "0" in main_window._status_cells_lbl.text()

def test_status_bar_image_count(main_window, qtbot, tmp_path, sample_rgb_array):
    """STAT-02: Image count in status bar updates after load_images."""
    import cv2
    img_path = str(tmp_path / "count_test.png")
    bgr = cv2.cvtColor(sample_rgb_array, cv2.COLOR_RGB2BGR)
    cv2.imwrite(img_path, bgr)
    main_window.load_images([img_path])
    assert "1" in main_window._status_count_lbl.text()

def test_status_bar_cell_count(main_window):
    """STAT-03: Total cell count (algo + manual) shown in status bar."""
    main_window._images["fake.png"] = {
        "original_bgr": None,
        "original_rgb": None,
        "annotated_rgb": None,
        "algo_count": 3,
        "manual_marks": [(1, 1), (2, 2)],
    }
    main_window._update_status_bar()
    assert "5" in main_window._status_cells_lbl.text()

def test_status_bar_transient(main_window):
    """STAT-04: showMessage() does not overwrite permanent status bar labels."""
    main_window.statusBar().showMessage("Analyzing...", 5000)
    assert main_window._status_batch_lbl.text() == "No batch"
