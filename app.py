"""Cell Counter Desktop Application - Entry Point."""
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


def main():
    if sys.platform == "win32":
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    app = QApplication(sys.argv)
    app.setApplicationName("Cell Counter")
    if sys.platform == "darwin":
        try:
            from Foundation import NSBundle
            info = NSBundle.mainBundle().infoDictionary()
            info["CFBundleName"] = "Cell Counter"
        except Exception:
            pass
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
