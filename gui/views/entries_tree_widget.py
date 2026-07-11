import json
from PySide6.QtWidgets import QTreeWidget
from PySide6.QtCore import Qt, QMimeData


class EntriesDragTreeWidget(QTreeWidget):
    """Виджет записей с поддержкой drag-and-drop между группами."""
    def mimeData(self, items):
        mime_data = QMimeData()
        uuids = [item.data(0, Qt.UserRole) for item in items if item.data(0, Qt.UserRole)]
        mime_data.setData("application/x-secpass-entry", json.dumps(uuids).encode())
        return mime_data
