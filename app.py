"""Cell Counter Desktop Application - Entry Point."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    if sys.platform == "win32":
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    app = QApplication(sys.argv)
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
