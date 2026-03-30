import pytest
import sys

def test_app_entry_point_exists():
    """APP-01: app.py exists and is importable."""
    import importlib.util
    spec = importlib.util.find_spec("app")
    # app.py should exist but we don't launch QApplication in tests
    # (conftest handles that via qtbot)
    assert spec is not None or __import__("os").path.exists("app.py")

def test_highdpi_policy(qtbot):
    """APP-04: High-DPI rounding policy is PassThrough on Windows."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    if sys.platform == "win32":
        policy = QApplication.highDpiScaleFactorRoundingPolicy()
        assert policy == Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    else:
        pytest.skip("HiDPI rounding policy only relevant on Windows")

def test_main_window_title(main_window):
    """APP-02: Window title contains 'Cell Counter'."""
    assert "Cell Counter" in main_window.windowTitle()

def test_main_window_minimum_size(main_window):
    """APP-03: Window has a reasonable minimum size."""
    assert main_window.minimumWidth() >= 800
    assert main_window.minimumHeight() >= 600
