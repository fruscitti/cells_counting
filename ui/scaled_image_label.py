from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter


class ScaledImageLabel(QLabel):
    """QLabel subclass that scales pixmap preserving aspect ratio on resize."""
    clicked = Signal(int, int)  # original image x, y coordinates

    def __init__(self, parent=None, click_enabled=False):
        super().__init__(parent)
        self._pixmap = None
        self._click_enabled = click_enabled
        self.setMinimumSize(1, 1)
        self.setAlignment(Qt.AlignCenter)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def clearPixmap(self):
        self._pixmap = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter = QPainter(self)
        painter.drawPixmap(x, y, scaled)

    def mousePressEvent(self, event):
        if self._pixmap is None or not self._click_enabled:
            return
        scaled = self._pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x_offset = (self.width() - scaled.width()) // 2
        y_offset = (self.height() - scaled.height()) // 2
        img_x = event.position().x() - x_offset
        img_y = event.position().y() - y_offset
        if img_x < 0 or img_y < 0 or img_x >= scaled.width() or img_y >= scaled.height():
            return
        orig_x = int(img_x * self._pixmap.width() / scaled.width())
        orig_y = int(img_y * self._pixmap.height() / scaled.height())
        self.clicked.emit(orig_x, orig_y)
