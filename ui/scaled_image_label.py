from PySide6.QtWidgets import QLabel, QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter


class ScaledImageLabel(QLabel):
    """QLabel subclass that scales pixmap preserving aspect ratio on resize.

    Supports zoom via zoom_in/zoom_out/zoom_reset (1x to 8x).
    When wrapped in a QScrollArea, scrollbars appear automatically when the
    zoomed image exceeds the viewport. The zoomed pixmap is pre-cached so
    paintEvent is always cheap (no SmoothTransformation on every repaint).
    """
    clicked = Signal(int, int)  # original image x, y coordinates

    def __init__(self, parent=None, click_enabled=False):
        super().__init__(parent)
        self._pixmap = None
        self._display_pixmap = None  # pre-cached scaled pixmap for current zoom
        self._click_enabled = click_enabled
        self._zoom = 1.0
        self.setMinimumSize(1, 1)
        self.setAlignment(Qt.AlignCenter)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        if self._zoom > 1.0 and self._display_pixmap is not None:
            # Already zoomed: just re-render the cache at the same size.
            # Do NOT touch setFixedSize or scroll area — that causes the
            # viewport to jump and the image to flash black on Windows.
            self._display_pixmap = self._pixmap.scaled(
                self._display_pixmap.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.update()
        else:
            self._apply_zoom()

    def clearPixmap(self):
        self._pixmap = None
        self._display_pixmap = None
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
        """Pre-cache scaled pixmap and resize widget so QScrollArea activates scrollbars."""
        if self._pixmap is None:
            self._display_pixmap = None
            self.setMinimumSize(1, 1)
            self.setMaximumSize(16777215, 16777215)
            parent = self.parent()
            if isinstance(parent, QScrollArea):
                parent.setWidgetResizable(True)
            self.update()
            return

        parent = self.parent()

        if self._zoom == 1.0:
            # Fit-to-widget: let the scroll area resize the label freely
            self._display_pixmap = None
            self.setMinimumSize(1, 1)
            self.setMaximumSize(16777215, 16777215)
            if isinstance(parent, QScrollArea):
                parent.setWidgetResizable(True)
        else:
            # Zoomed: compute fit baseline from viewport, then scale by zoom
            viewport = parent.viewport().size() if isinstance(parent, QScrollArea) else self.size()
            fit = self._pixmap.scaled(viewport, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            zoomed_w = int(fit.width() * self._zoom)
            zoomed_h = int(fit.height() * self._zoom)
            # Pre-render once with SmoothTransformation — paintEvent will just blit
            self._display_pixmap = self._pixmap.scaled(
                zoomed_w, zoomed_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            if isinstance(parent, QScrollArea):
                parent.setWidgetResizable(False)
            self.setFixedSize(self._display_pixmap.size())

        self.update()

    # ---- Qt event overrides ----

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._pixmap is None:
            return

        if self._display_pixmap is not None:
            # Zoomed: blit pre-cached pixmap — no scaling, always fast
            scaled = self._display_pixmap
        else:
            # Fit-to-widget: scale with FastTransformation (no hang on scroll)
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.FastTransformation
            )

        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter = QPainter(self)
        painter.drawPixmap(x, y, scaled)

    def mousePressEvent(self, event):
        if self._pixmap is None or not self._click_enabled:
            return

        if self._display_pixmap is not None:
            scaled = self._display_pixmap
        else:
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.FastTransformation
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
