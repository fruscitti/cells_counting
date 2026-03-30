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
