import json
from PySide6.QtWidgets import QTreeView
from PySide6.QtCore import Qt, QMimeData, QModelIndex


class GroupsDropTreeView(QTreeView):
    """Виджет групп: древовидная структура, нередактируемые имена,
    приём записей через drop."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drop_callback = None
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

    def set_drop_callback(self, callback):
        self._drop_callback = callback

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-secpass-entry"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-secpass-entry"):
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            self.setCurrentIndex(index if index.isValid() else QModelIndex())
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.setCurrentIndex(QModelIndex())
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-secpass-entry"):
            if self._drop_callback:
                data = bytes(event.mimeData().data("application/x-secpass-entry")).decode()
                uuids = json.loads(data)
                pos = event.position().toPoint()
                index = self.indexAt(pos)
                group_uuid = None
                if index.isValid():
                    item = self.model().itemFromIndex(index)
                    group_uuid = item.data(Qt.UserRole)
                self._drop_callback(uuids, group_uuid)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
