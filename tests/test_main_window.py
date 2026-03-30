import pytest
from PySide6.QtWidgets import QToolBar
from PySide6.QtCore import Qt

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


# --- Phase 5: Actions Surface ---

def test_menu_bar_exists(window):
    """MENU-01/02/03: Menu bar has File, Batch, Analysis menus."""
    menu_bar = window.menuBar()
    menu_titles = [a.text() for a in menu_bar.actions()]
    assert "File" in menu_titles
    assert "Batch" in menu_titles
    assert "Analysis" in menu_titles

def test_file_menu_actions(window):
    """MENU-01: File menu contains correct actions in order."""
    menu_bar = window.menuBar()
    file_menu = None
    for action in menu_bar.actions():
        if action.text() == "File":
            file_menu = action.menu()
            break
    action_texts = [a.text() for a in file_menu.actions() if not a.isSeparator()]
    assert action_texts == ["Open Images", "Open Batch", "Save Batch", "Export CSV", "Exit"]

def test_batch_menu_actions(window):
    """MENU-02: Batch menu contains correct actions in order."""
    menu_bar = window.menuBar()
    batch_menu = None
    for action in menu_bar.actions():
        if action.text() == "Batch":
            batch_menu = action.menu()
            break
    action_texts = [a.text() for a in batch_menu.actions() if not a.isSeparator()]
    assert action_texts == ["Add Images", "Remove Image", "Re-Analyze"]

def test_analysis_menu_actions(window):
    """MENU-03: Analysis menu contains correct actions in order."""
    menu_bar = window.menuBar()
    analysis_menu = None
    for action in menu_bar.actions():
        if action.text() == "Analysis":
            analysis_menu = action.menu()
            break
    action_texts = [a.text() for a in analysis_menu.actions() if not a.isSeparator()]
    assert action_texts == ["Analyze", "Auto-Optimize", "Undo Mark", "Clear All"]

def test_toolbar_exists_and_locked(window):
    """TOOL-02: Toolbar is non-movable and context menu disabled."""
    toolbar = window.findChild(QToolBar)
    assert toolbar is not None
    assert toolbar.isMovable() is False
    assert toolbar.contextMenuPolicy() == Qt.PreventContextMenu

def test_toolbar_actions(window):
    """TOOL-01: Toolbar has Analyze, Auto-Optimize, Undo Mark, Clear All."""
    toolbar = window.findChild(QToolBar)
    action_texts = [a.text() for a in toolbar.actions() if not a.isSeparator()]
    assert action_texts == ["Analyze", "Auto-Optimize", "Undo Mark", "Clear All"]

def test_menu_toolbar_same_action(window):
    """TOOL-03: Menu and toolbar share the same QAction instance."""
    toolbar = window.findChild(QToolBar)
    toolbar_analyze = [a for a in toolbar.actions() if a.text() == "Analyze"][0]
    assert toolbar_analyze is window.act_analyze

def test_action_enable_disable_sync(window):
    """MENU-04: Disabling action affects both menu and toolbar."""
    window.act_analyze.setEnabled(False)
    assert window.act_analyze.isEnabled() is False
    window.act_analyze.setEnabled(True)
    assert window.act_analyze.isEnabled() is True
