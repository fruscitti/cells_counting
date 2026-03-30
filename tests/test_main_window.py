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

@pytest.mark.skip(reason="Implemented in Plan 03")
def test_total_count(main_window):
    """MARK-03: Total count = algo + manual."""
    pass

@pytest.mark.skip(reason="Implemented in Plan 03")
def test_clear_resets(main_window):
    """CLR-01: Clear resets all state to defaults."""
    pass
