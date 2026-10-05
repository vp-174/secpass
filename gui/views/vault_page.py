import uuid
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.dialogs.entry_dialog import EntryDialog
from gui.views.entries_tree_widget import EntriesDragTreeWidget
from gui.views.group_dialog import GroupDialog
from gui.views.groups_tree_view import GroupsDropTreeView
from gui.views.password_input import copy_to_clipboard
from gui.views.tree_lines_delegate import TreeLinesDelegate
from storage import (
    DuplicateNameError,
    GroupNotEmptyError,
    Storage,
    StorageError,
)

GROUPS_STYLE = """
    QTreeView {
        border: 1px solid #ccc;
        background: #fafafa;
        show-decoration-selected: 1;
    }
    QTreeView::item {
        padding: 4px;
        min-height: 22px;
    }
    QTreeView::item:hover {
        background: #e5f3ff;
    }
    QTreeView::item:selected {
        background: #0078d7;
        color: white;
    }
"""

ENTRIES_STYLE = """
    QTreeWidget {
        border: 1px solid #ccc;
        background: #fff;
    }
    QTreeWidget::item {
        padding: 6px 8px 6px 0px;
        border-bottom: 1px solid #eee;
    }
    QTreeWidget::item:hover {
        background: #e5f3ff;
    }
    QTreeWidget::item:selected {
        background: #0078d7;
        color: white;
    }
"""


class VaultPage(QWidget):
    """Вкладка разблокированного хранилища: дерево групп, список записей,
    поиск, операции над записями и группами."""

    lock_requested = Signal()
    changed = Signal()

    def __init__(self, storage: Storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)

        add_group_btn = QPushButton("Add Group")
        add_group_btn.clicked.connect(self._on_add_group)
        toolbar.addWidget(add_group_btn)

        delete_group_btn = QPushButton("Delete Group")
        delete_group_btn.clicked.connect(self._on_delete_group)
        toolbar.addWidget(delete_group_btn)

        toolbar.addStretch()

        add_entry_btn = QPushButton("Add Entry")
        add_entry_btn.clicked.connect(self._on_add_entry)
        toolbar.addWidget(add_entry_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete_entry)
        toolbar.addWidget(delete_btn)

        copy_username_btn = QPushButton("Copy Username")
        copy_username_btn.clicked.connect(self._on_copy_username)
        toolbar.addWidget(copy_username_btn)

        copy_password_btn = QPushButton("Copy Password")
        copy_password_btn.clicked.connect(self._on_copy_password)
        toolbar.addWidget(copy_password_btn)

        lock_btn = QPushButton("Lock")
        lock_btn.setStyleSheet("background-color: lightgreen;")
        lock_btn.clicked.connect(self.lock_requested.emit)
        toolbar.addWidget(lock_btn)

        layout.addLayout(toolbar)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search entries...")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        splitter = QSplitter(Qt.Horizontal)

        self.groups_tree = GroupsDropTreeView()
        self.groups_tree.setItemDelegate(TreeLinesDelegate(self.groups_tree))
        self.groups_tree.setModel(QStandardItemModel())
        self.groups_tree.setHeaderHidden(True)
        self.groups_tree.setRootIsDecorated(True)
        self.groups_tree.setItemsExpandable(True)
        self.groups_tree.setIndentation(20)
        self.groups_tree.setProperty("showTreeLines", True)
        self.groups_tree.setStyleSheet(GROUPS_STYLE)
        self.groups_tree.set_drop_callback(self._move_entries_to_group)
        self.groups_tree.clicked.connect(self._on_group_clicked)
        self.groups_tree.doubleClicked.connect(self._on_group_double_clicked)
        splitter.addWidget(self.groups_tree)

        self.entries_list = EntriesDragTreeWidget()
        self.entries_list.setHeaderLabels(["List entries"])
        self.entries_list.setColumnCount(1)
        self.entries_list.setDragEnabled(True)
        self.entries_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.entries_list.setStyleSheet(ENTRIES_STYLE)
        self.entries_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entries_list.customContextMenuRequested.connect(self._on_entries_context_menu)
        self.entries_list.itemDoubleClicked.connect(lambda item, _column: self._edit_entry(item))
        splitter.addWidget(self.entries_list)

        splitter.setSizes([250, 500])
        layout.addWidget(splitter)

    # --- refresh ---

    def refresh(self, search_query: Optional[str] = None):
        model = self.groups_tree.model()
        model.clear()

        root_item = QStandardItem("All Entries")
        root_item.setData(None, Qt.UserRole)
        model.appendRow(root_item)

        for group in sorted(self.storage.list_groups(), key=lambda g: g["name"].lower()):
            item = QStandardItem(group["name"])
            item.setData(group["uuid"], Qt.UserRole)
            root_item.appendRow(item)

        self.groups_tree.setExpanded(root_item.index(), True)
        self.groups_tree.setCurrentIndex(root_item.index())

        self._refresh_entries(search_query=search_query)
        self.changed.emit()

    def _refresh_entries(self, group_uuid: Optional[str] = None, search_query: Optional[str] = None):
        self.entries_list.clear()
        query = search_query.lower() if search_query else None

        for entry in sorted(self.storage.list_entries(), key=lambda e: e["name"].lower()):
            if group_uuid and entry.get("group") != group_uuid:
                continue
            if query:
                name = entry.get("name", "").lower()
                url = entry.get("url", "").lower()
                if query not in name and query not in url:
                    continue

            item = QTreeWidgetItem([entry["name"]])
            item.setData(0, Qt.UserRole, entry["uuid"])
            self.entries_list.addTopLevelItem(item)

    def _on_search(self, text: str):
        self._refresh_entries(search_query=text or None)

    def _selected_group_uuid(self) -> Optional[str]:
        index = self.groups_tree.currentIndex()
        if not index.isValid():
            return None
        item = self.groups_tree.model().itemFromIndex(index)
        return item.data(Qt.UserRole) if item else None

    def _selected_entry_uuid(self) -> Optional[str]:
        item = self.entries_list.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    # --- groups ---

    def _on_add_group(self):
        dialog = GroupDialog("New Group", parent=self)
        if dialog.exec() and dialog.get_name():
            try:
                self.storage.create_group(dialog.get_name())
                self.refresh()
            except DuplicateNameError as e:
                QMessageBox.warning(self, "Duplicate Group", str(e))
            except StorageError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_group_double_clicked(self, index):
        item = self.groups_tree.model().itemFromIndex(index)
        if not item:
            return
        group_uuid = item.data(Qt.UserRole)
        if not group_uuid:
            return
        group = self.storage.get_group(uuid.UUID(group_uuid))
        if not group:
            return

        dialog = GroupDialog("Edit Group", group["name"], parent=self)
        if dialog.exec() and dialog.get_name():
            try:
                self.storage.update_group(uuid.UUID(group_uuid), dialog.get_name())
                self.refresh()
            except DuplicateNameError as e:
                QMessageBox.warning(self, "Duplicate Group", str(e))
            except StorageError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_group_clicked(self, index):
        item = self.groups_tree.model().itemFromIndex(index)
        if not item:
            return
        self._refresh_entries(
            group_uuid=item.data(Qt.UserRole),
            search_query=self.search_input.text() or None,
        )

    def _on_delete_group(self):
        group_uuid = self._selected_group_uuid()
        if not group_uuid:
            return
        reply = QMessageBox.question(
            self,
            "Delete Group",
            "Are you sure you want to delete this group?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.storage.delete_group(uuid.UUID(group_uuid))
            self.refresh()
        except GroupNotEmptyError:
            QMessageBox.warning(
                self,
                "Group Not Empty",
                "This group contains entries or subgroups. Move or delete them first.",
            )
        except StorageError as e:
            QMessageBox.critical(self, "Error", str(e))

    # --- entries ---

    def _on_add_entry(self):
        group_uuid = self._selected_group_uuid()
        if group_uuid is None:
            if not self.storage.list_groups():
                QMessageBox.warning(
                    self, "No Groups", "Please create at least one group before adding entries."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Select Group",
                    "Please select a specific group in the tree before adding an entry.",
                )
            return

        dialog = EntryDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                entry_uuid = self.storage.create_entry(data["name"], data["url"], uuid.UUID(group_uuid))
                self.storage.set_entry_body(
                    entry_uuid,
                    data["username"],
                    data["password"],
                    data.get("email", ""),
                    data.get("notes", ""),
                )
                self.refresh()
            except DuplicateNameError as e:
                QMessageBox.warning(self, "Duplicate Entry", str(e))
            except StorageError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_entry(self, item):
        entry_uuid_str = item.data(0, Qt.UserRole)
        if not entry_uuid_str:
            return
        entry_uuid = uuid.UUID(entry_uuid_str)
        head = self.storage.get_entry_head(entry_uuid) or {}
        body = self.storage.get_entry_body(entry_uuid) or {}

        entry_data = {
            "name": head.get("name", ""),
            "url": head.get("url", ""),
            "username": body.get("username", ""),
            "password": body.get("password", ""),
            "email": body.get("email", ""),
            "notes": body.get("notes", ""),
        }

        dialog = EntryDialog(entry_data, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.storage.update_entry_head(entry_uuid, data["name"], data["url"])
                self.storage.set_entry_body(
                    entry_uuid,
                    data["username"],
                    data["password"],
                    data.get("email", ""),
                    data.get("notes", ""),
                )
                self.refresh()
            except DuplicateNameError as e:
                QMessageBox.warning(self, "Duplicate Entry", str(e))
            except StorageError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _on_delete_entry(self):
        entry_uuid = self._selected_entry_uuid()
        if not entry_uuid:
            return
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Are you sure you want to delete this entry?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.storage.delete_entry(uuid.UUID(entry_uuid))
            self.refresh()

    # --- copy ---

    def _on_copy_username(self):
        entry_uuid = self._selected_entry_uuid()
        if not entry_uuid:
            return
        body = self.storage.get_entry_body(uuid.UUID(entry_uuid))
        if body:
            copy_to_clipboard(body.get("username", ""))

    def _on_copy_password(self):
        entry_uuid = self._selected_entry_uuid()
        if not entry_uuid:
            return
        body = self.storage.get_entry_body(uuid.UUID(entry_uuid))
        if body:
            copy_to_clipboard(body.get("password", ""))

    # --- move entries ---

    def _on_entries_context_menu(self, pos):
        item = self.entries_list.itemAt(pos)
        if not item:
            return
        selected_items = self.entries_list.selectedItems()
        if not selected_items:
            return
        menu = QMenu()
        move_menu = menu.addMenu("Move to Group")
        for group in self.storage.list_groups():
            action = move_menu.addAction(group["name"])
            action.setData(group["uuid"])
        action = menu.exec(self.entries_list.viewport().mapToGlobal(pos))
        if action:
            uuids = [it.data(0, Qt.UserRole) for it in selected_items if it.data(0, Qt.UserRole)]
            self._move_entries_to_group(uuids, action.data())

    def _move_entries_to_group(self, entry_uuids, group_uuid):
        if group_uuid is None:
            QMessageBox.warning(
                self, "Cannot Move", "Entries must be moved to a specific group, not to the root."
            )
            return
        group_name = None
        for g in self.storage.list_groups():
            if g["uuid"] == group_uuid:
                group_name = g["name"]
                break
        reply = QMessageBox.question(
            self,
            "Confirm Move",
            f"Are you sure you want to move {len(entry_uuids)} "
            f"entr{'y' if len(entry_uuids) == 1 else 'ies'} to '{group_name}'?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            for uuid_str in entry_uuids:
                self.storage.move_entry(uuid.UUID(uuid_str), uuid.UUID(group_uuid))
            self.refresh()
            self._select_group(group_uuid)
            self._refresh_entries(group_uuid=group_uuid)
        except StorageError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _select_group(self, group_uuid: str):
        model = self.groups_tree.model()
        for i in range(model.rowCount()):
            root = model.item(i)
            for j in range(root.rowCount()):
                child = root.child(j)
                if child.data(Qt.UserRole) == group_uuid:
                    self.groups_tree.setCurrentIndex(child.index())
                    return
