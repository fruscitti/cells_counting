from PySide6.QtWidgets import QLabel, QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter


class ScaledImageLabel(QLabel):
    """QLabel subclass that scales pixmap preserving aspect ratio on resize.

    Supports mouse-wheel zoom (1x to 8x). When wrapped in a QScrollArea,
    scrollbars appear automatically when the zoomed image exceeds the viewport.
    """
    clicked = Signal(int, int)  # original image x, y coordinates

    def __init__(self, parent=None, click_enabled=False):
        super().__init__(parent)
        self._pixmap = None
        self._click_enabled = click_enabled
        self._zoom = 1.0
        self._fit_size = None  # cached QSize of fit-to-widget scale
        self.setMinimumSize(1, 1)
        self.setAlignment(Qt.AlignCenter)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def clearPixmap(self):
        self._pixmap = None
        self.zoom_reset()
        self.update()

    # ---- Zoom public API ----

    def zoom_in(self):
        """Increase zoom by factor 1.25, capped at 8.0."""
        self._zoom = min(self._zoom * 1.25, 8.0)
        self._apply_zoom()

    def zoom_out(self):
        """Decrease zoom by factor 1.25, floored at 1.0."""
        self._zoom = max(self._zoom / 1.25, 1.0)
        self._apply_zoom()

    def zoom_reset(self):
        """Reset zoom to fit-to-widget (1.0)."""
        self._zoom = 1.0
        self._apply_zoom()

    def _apply_zoom(self):
        """Apply current zoom level: adjust widget size and toggle QScrollArea resizable flag."""
        if self._pixmap is None:
            # Restore flexible sizing when no image is loaded
            self.setMinimumSize(1, 1)
            self.setMaximumSize(16777215, 16777215)
            parent = self.parent()
            if isinstance(parent, QScrollArea):
                parent.setWidgetResizable(True)
            self.update()
            return

        parent = self.parent()

        if self._zoom == 1.0:
            # Fit-to-widget: restore flexible sizing, let scroll area resize label
            self.setMinimumSize(1, 1)
            self.setMaximumSize(16777215, 16777215)
            if isinstance(parent, QScrollArea):
                parent.setWidgetResizable(True)
        else:
            # Zoomed: compute fit-size then scale it by _zoom, fix label size so scrollbars activate
            viewport = parent.viewport().size() if isinstance(parent, QScrollArea) else self.size()
            fit_pixmap = self._pixmap.scaled(viewport, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            fit_w = fit_pixmap.width()
            fit_h = fit_pixmap.height()
            zoomed_w = int(fit_w * self._zoom)
            zoomed_h = int(fit_h * self._zoom)
            if isinstance(parent, QScrollArea):
                parent.setWidgetResizable(False)
            self.setFixedSize(zoomed_w, zoomed_h)

        self.update()

    # ---- Qt event overrides ----

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        elif delta < 0:
            self.zoom_out()
        event.accept()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap is None:
            return
        if self._zoom > 1.0:
            # Fill the entire fixed-size label with the zoomed pixmap
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            # Fit-to-widget: scale to current widget size
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
        # Use same scaling logic as paintEvent so coordinate mapping stays accurate
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
