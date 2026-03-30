"""Batch management dialogs for the Cell Counter desktop app."""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel
)


class OpenBatchDialog(QDialog):
    """Dialog for selecting a saved batch to open.

    Shows a list of batches from BatchManager.list_batches() with name,
    creation date, and image count. User selects one and clicks OK.
    """

    def __init__(self, batches: list, parent=None):
        """Create dialog with a list of batch metadata dicts.

        Args:
            batches: list of dicts from BatchManager.list_batches(),
                     each with: name, path, created_at, image_count
            parent: parent QWidget (optional)
        """
        super().__init__(parent)
        self.setWindowTitle("Open Batch")
        self.setMinimumWidth(400)
        self._batches = batches

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a batch to open:"))

        self._list = QListWidget()
        for b in batches:
            date_str = b["created_at"][:10]  # YYYY-MM-DD
            text = f"{b['name']}  |  {date_str}  |  {b['image_count']} images"
            item = QListWidgetItem(text)
            item.setData(256, b["path"])  # Qt.UserRole = 256
            self._list.addItem(item)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_path(self) -> Path | None:
        """Return the Path of the selected batch, or None if nothing selected."""
        item = self._list.currentItem()
        if item:
            return item.data(256)
        return None
