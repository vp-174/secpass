import sys
import uuid
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QStackedWidget, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QSplitter, QTabWidget, QMenu, QAbstractItemView,
    QCheckBox
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon
from gui.dialogs.vault_creation_dialog import VaultCreationDialog
from gui.dialogs.entry_dialog import EntryDialog
from gui.views.tree_lines_delegate import TreeLinesDelegate
from gui.views.entries_tree_widget import EntriesDragTreeWidget
from gui.views.groups_tree_view import GroupsDropTreeView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        icon = QIcon(str(Path(__file__).parent.parent / "secpass.ico"))
        self.setWindowIcon(icon)
        self.setWindowTitle("SecPass")
        self.resize(1000, 650)
        self.vault = None
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(False)
        self.tabs.tabCloseRequested.connect(self._on_close_tab)
        self.tabs.currentChanged.connect(self._update_window_title)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::close-button { margin: 0; padding: 0; }
            QTabBar { spacing: 0; padding: 0; }
            QTabBar::tab { padding: 4px 8px; }
        """)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(36, 24)
        new_tab_btn.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0; margin: 0;")
        new_tab_btn.clicked.connect(self._on_new_tab)

        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 2, 8, 2)
        corner_layout.addWidget(new_tab_btn)
        self.tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)

        self._create_login_page()

        self.stack = QStackedWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.tabs)
        self.stack.setCurrentIndex(0)

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        new_vault_action = QAction("New Vault", self)
        new_vault_action.triggered.connect(self._on_new_vault)
        file_menu.addAction(new_vault_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _on_about(self):
        QMessageBox.about(self, "About SecPass",
            "<b>SecPass</b><br><br>"
            "Version: 1.0.0<br>"
            "Developer: Vladislav Panov<br>"
            "Contact: support@secpass.app<br>"
            "<a href='https://fr-space.ru'>https://fr-space.ru</a>"
            )

    def _create_login_page(self):
        self.login_page = QWidget()
        self.login_page.setObjectName("login_page")
        layout = QVBoxLayout(self.login_page)
        layout.setSpacing(15)
        layout.setContentsMargins(100, 80, 100, 80)

        title = QLabel("SecPass")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Secure Password Manager")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #888;")
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        form = QFormLayout()
        form.setSpacing(10)

        self.vault_path_input = QLineEdit()
        self.vault_path_input.setObjectName("vault_path")
        self.vault_path_input.setPlaceholderText("Choose vault...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.vault_path_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_vault)
        path_layout.addWidget(browse_btn)
        form.addRow("Vault Path:", path_layout)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_unlock)
        self.password_input.setPlaceholderText("Write your strong password...")
        password_row = QHBoxLayout()
        password_row.addWidget(self.password_input, 1)
        self.use_keyfile_cb = QCheckBox("Use key file")
        self.use_keyfile_cb.toggled.connect(self._on_keyfile_toggled)
        password_row.addWidget(self.use_keyfile_cb)
        form.addRow("Password:", password_row)

        self.keyfile_input = QLineEdit()
        self.keyfile_input.setPlaceholderText("Key file path...")
        self.keyfile_input.setEnabled(False)
        keyfile_layout = QHBoxLayout()
        keyfile_layout.addWidget(self.keyfile_input)
        self.keyfile_btn = QPushButton("Browse...")
        self.keyfile_btn.setEnabled(False)
        self.keyfile_btn.clicked.connect(self._on_browse_keyfile)
        keyfile_layout.addWidget(self.keyfile_btn)
        form.addRow("", keyfile_layout)

        layout.addLayout(form)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setMinimumHeight(45)
        self.unlock_btn.clicked.connect(self._on_unlock)
        btn_layout.addWidget(self.unlock_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #cc0000;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _create_vault_page(self, vault):
        page = QWidget()
        page.vault = vault
        layout = QVBoxLayout(page)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)

        add_group_btn = QPushButton("Add Group")
        add_group_btn.clicked.connect(lambda: self._on_add_group_vault(vault))
        toolbar.addWidget(add_group_btn)

        delete_group_btn = QPushButton("Delete Group")
        delete_group_btn.clicked.connect(lambda: self._on_delete_group_vault(vault))
        toolbar.addWidget(delete_group_btn)

        toolbar.addStretch()

        add_entry_btn = QPushButton("Add Entry")
        add_entry_btn.clicked.connect(lambda: self._on_add_entry_vault(vault))
        toolbar.addWidget(add_entry_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self._on_delete_entry_vault(vault))
        toolbar.addWidget(delete_btn)

        copy_username_btn = QPushButton("Copy Username")
        copy_username_btn.clicked.connect(lambda: self._on_copy_username_vault(vault))
        toolbar.addWidget(copy_username_btn)

        copy_password_btn = QPushButton("Copy Password")
        copy_password_btn.clicked.connect(lambda: self._on_copy_password_vault(vault))
        toolbar.addWidget(copy_password_btn)

        lock_btn = QPushButton("Lock")
        lock_btn.setStyleSheet("background-color: lightgreen;")
        lock_btn.clicked.connect(lambda: self._on_lock_vault(vault, page))
        toolbar.addWidget(lock_btn)

        layout.addLayout(toolbar)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search entries...")
        search_input.textChanged.connect(lambda t: self._on_search_vault(vault, t))
        layout.addWidget(search_input)

        splitter = QSplitter(Qt.Horizontal)

        groups_tree = GroupsDropTreeView()
        groups_tree.setItemDelegate(TreeLinesDelegate(groups_tree))
        groups_model = QStandardItemModel()
        groups_tree.setModel(groups_model)
        groups_tree.setHeaderHidden(True)
        groups_tree.setRootIsDecorated(True)
        groups_tree.setItemsExpandable(True)
        groups_tree.setIndentation(20)
        groups_tree.setProperty("showTreeLines", True)
        groups_tree.setStyleSheet("""
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
        """)
        groups_tree.set_drop_callback(lambda uuids, group_uuid: self._move_entries_to_group(vault, uuids, group_uuid))
        groups_tree.expanded.connect(lambda idx: groups_tree.setExpanded(idx, True))
        groups_tree.clicked.connect(lambda idx: self._on_group_clicked_vault(vault, groups_model.itemFromIndex(idx), 0, search_input.text()))
        groups_tree.doubleClicked.connect(lambda idx: self._on_group_double_click_vault(vault, groups_model.itemFromIndex(idx), 0))
        splitter.addWidget(groups_tree)

        entries_list = EntriesDragTreeWidget()
        entries_list.setHeaderLabels(["List entries"])
        entries_list.setColumnCount(1)
        entries_list.setDragEnabled(True)
        entries_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        entries_list.setStyleSheet("""
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
        """)
        entries_list.setContextMenuPolicy(Qt.CustomContextMenu)
        entries_list.customContextMenuRequested.connect(lambda pos: self._on_entries_context_menu(vault, pos))
        entries_list.itemDoubleClicked.connect(lambda item, col: self._on_entry_double_click_vault(vault, item, col))
        splitter.addWidget(entries_list)

        splitter.setSizes([250, 500])

        layout.addWidget(splitter)

        page.groups_tree = groups_tree
        page.entries_list = entries_list

        self._refresh_vault_view(vault, page)

        return page

    def _on_add_entry_vault(self, vault):
        if not vault.list_groups():
            QMessageBox.warning(self, "No Groups", "Please create at least one group before adding entries.")
            return
        group_uuid = None
        current_widget = self.current_vault_widget
        if current_widget and hasattr(current_widget, 'groups_tree'):
            current_idx = current_widget.groups_tree.currentIndex()
            if current_idx.isValid():
                selected = current_widget.groups_tree.model().itemFromIndex(current_idx)
                if selected:
                    group_uuid = selected.data(Qt.UserRole)

        if group_uuid is None:
            QMessageBox.warning(self, "Select Group", "Please select a specific group in the tree before adding an entry.")
            return

        dialog = EntryDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                entry_uuid = vault.create_entry(data["name"], data["url"], group_uuid)
                vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))
                self._refresh_vault_view(vault, self.current_vault_widget)
            except ValueError as e:
                QMessageBox.warning(self, "Duplicate Entry", str(e))

    def _on_add_group_vault(self, vault):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Group")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Group Name")
        layout.addWidget(name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() and name_input.text():
            try:
                vault.create_group(name_input.text())
                self._refresh_vault_view(vault, self.current_vault_widget)
            except ValueError as e:
                QMessageBox.warning(self, "Duplicate Group", str(e))

    def _on_edit_entry_vault(self, vault):
        current_widget = self.current_vault_widget
        if not current_widget or not hasattr(current_widget, 'entries_list'):
            return
        selected = current_widget.entries_list.currentItem()
        if not selected:
            return
        self._edit_entry_vault(vault, selected, current_widget)

    def _on_entry_double_click_vault(self, vault, item, column):
        current_widget = self.current_vault_widget
        if current_widget:
            self._edit_entry_vault(vault, item, current_widget)

    def _edit_entry_vault(self, vault, item, page):
        entry_uuid_str = item.data(0, Qt.UserRole)
        if not entry_uuid_str:
            return
        entry_uuid = uuid.UUID(entry_uuid_str)
        head = vault.get_entry_head(entry_uuid)
        body = vault.get_entry_body(entry_uuid)

        entry_data = {
            "name": head.get("name", "") if head else "",
            "url": head.get("url", "") if head else "",
            "username": body.get("username", "") if body else "",
            "password": body.get("password", "") if body else "",
            "email": body.get("email", "") if body else "",
            "notes": body.get("notes", "") if body else "",
        }

        dialog = EntryDialog(entry_data, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                vault.update_entry_head(entry_uuid, data["name"], data["url"])
                vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))
                self._refresh_vault_view(vault, page)
            except ValueError as e:
                QMessageBox.warning(self, "Duplicate Entry", str(e))

    def _on_delete_entry_vault(self, vault):
        current_widget = self.current_vault_widget
        if not current_widget or not hasattr(current_widget, 'entries_list'):
            return
        selected = current_widget.entries_list.currentItem()
        if not selected:
            return

        reply = QMessageBox.question(
            self, "Delete Entry",
            "Are you sure you want to delete this entry?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            entry_uuid = selected.data(0, Qt.UserRole)
            if entry_uuid:
                vault.delete_entry(uuid.UUID(entry_uuid))
                self._refresh_vault_view(vault, current_widget)

    def _on_delete_group_vault(self, vault):
        current_widget = self.current_vault_widget
        if not current_widget or not hasattr(current_widget, 'groups_tree'):
            return
        selected_indexes = current_widget.groups_tree.selectedIndexes()
        if not selected_indexes:
            return
        selected = current_widget.groups_tree.model().itemFromIndex(selected_indexes[0])
        if not selected:
            return

        group_uuid = selected.data(Qt.UserRole)
        if not group_uuid:
            return

        reply = QMessageBox.question(
            self, "Delete Group",
            "Are you sure you want to delete this group?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            vault.delete_group(uuid.UUID(group_uuid))
            self._refresh_vault_view(vault, current_widget)

    def _on_search_vault(self, vault, text):
        self._refresh_vault_view(vault, self.current_vault_widget, text if text else None)

    def _on_group_clicked_vault(self, vault, item, column, search_text):
        group_uuid = item.data(Qt.UserRole)
        self._refresh_entries_vault(vault, self.current_vault_widget, group_uuid, search_text if search_text else None)

    def _on_group_double_click_vault(self, vault, item, column):
        group_uuid = item.data(Qt.UserRole)
        if not group_uuid:
            return
        group = vault.get_group(uuid.UUID(group_uuid))
        if not group:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Group")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit(group["name"])
        name_input.setPlaceholderText("Group Name")
        layout.addWidget(name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() and name_input.text():
            try:
                vault.update_group(uuid.UUID(group_uuid), name_input.text())
                self._refresh_vault_view(vault, self.current_vault_widget)
            except ValueError as e:
                QMessageBox.warning(self, "Duplicate Group", str(e))

    def _on_entries_context_menu(self, vault, pos):
        entries_list = self.current_vault_widget.entries_list
        item = entries_list.itemAt(pos)
        if not item:
            return
        selected_items = entries_list.selectedItems()
        if not selected_items:
            return
        menu = QMenu()
        move_menu = menu.addMenu("Move to Group")
        for group in vault.list_groups():
            action = move_menu.addAction(group["name"])
            action.setData(group["uuid"])
        action = menu.exec(entries_list.viewport().mapToGlobal(pos))
        if action:
            group_uuid = action.data()
            uuids = [it.data(0, Qt.UserRole) for it in selected_items if it.data(0, Qt.UserRole)]
            self._move_entries_to_group(vault, uuids, group_uuid)

    def _move_entries_to_group(self, vault, entry_uuids, group_uuid):
        if group_uuid is None:
            QMessageBox.warning(self, "Cannot Move", "Entries must be moved to a specific group, not to the root.")
            return
        group_name = None
        for g in vault.list_groups():
            if g["uuid"] == group_uuid:
                group_name = g["name"]
                break
        reply = QMessageBox.question(
            self, "Confirm Move",
            f"Are you sure you want to move {len(entry_uuids)} entr{'y' if len(entry_uuids) == 1 else 'ies'} to '{group_name}'?",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes:
            return
        try:
            for uuid_str in entry_uuids:
                vault.move_entry(uuid.UUID(uuid_str), uuid.UUID(group_uuid))
            page = self.current_vault_widget
            current_group = None
            if page and hasattr(page, 'groups_tree'):
                idx = page.groups_tree.currentIndex()
                if idx.isValid():
                    item = page.groups_tree.model().itemFromIndex(idx)
                    current_group = item.data(Qt.UserRole)
            self._refresh_vault_view(vault, page)
            for i in range(page.groups_tree.model().rowCount()):
                root = page.groups_tree.model().item(i)
                for j in range(root.rowCount()):
                    child = root.child(j)
                    if child.data(Qt.UserRole) == group_uuid:
                        page.groups_tree.setCurrentIndex(child.index())
                        break
                else:
                    continue
                break
            self._refresh_entries_vault(vault, page, group_uuid)
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _on_copy_username_vault(self, vault):
        current_widget = self.current_vault_widget
        if not current_widget or not hasattr(current_widget, 'entries_list'):
            return
        selected = current_widget.entries_list.currentItem()
        if not selected:
            return
        entry_uuid = selected.data(0, Qt.UserRole)
        if entry_uuid:
            body = vault.get_entry_body(uuid.UUID(entry_uuid))
            if body:
                QApplication.clipboard().setText(body.get("username", ""))

    def _on_copy_password_vault(self, vault):
        current_widget = self.current_vault_widget
        if not current_widget or not hasattr(current_widget, 'entries_list'):
            return
        selected = current_widget.entries_list.currentItem()
        if not selected:
            return
        entry_uuid = selected.data(0, Qt.UserRole)
        if entry_uuid:
            body = vault.get_entry_body(uuid.UUID(entry_uuid))
            if body:
                QApplication.clipboard().setText(body.get("password", ""))

    def _on_lock_vault(self, vault, page):
        vault.lock()
        index = self.tabs.indexOf(page)
        if index >= 0:
            self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.stack.setCurrentIndex(0)

    def _refresh_vault_view(self, vault, page, search_query=None):
        if not page or not hasattr(page, 'groups_tree'):
            return

        groups_model = page.groups_tree.model()
        groups_model.clear()

        root_item = QStandardItem("All Entries")
        root_item.setData(None, Qt.UserRole)
        groups_model.appendRow(root_item)

        for group in sorted(vault.list_groups(), key=lambda g: g["name"].lower()):
            item = QStandardItem(group["name"])
            item.setData(group["uuid"], Qt.UserRole)
            root_item.appendRow(item)

        page.groups_tree.setExpanded(root_item.index(), True)
        page.groups_tree.setCurrentIndex(root_item.index())

        self._refresh_entries_vault(vault, page, None, search_query)
        if self.tabs.currentWidget() is page:
            self._update_window_title()

    def _refresh_entries_vault(self, vault, page, group_uuid=None, search_query=None):
        if not page or not hasattr(page, 'entries_list'):
            return
        page.entries_list.clear()

        for entry in sorted(vault.list_entries(), key=lambda e: e["name"].lower()):
            if group_uuid and entry.get("group") != group_uuid:
                continue
            if search_query:
                name = entry.get("name", "").lower()
                url = entry.get("url", "").lower()
                if search_query.lower() not in name and search_query.lower() not in url:
                    continue

            item = QTreeWidgetItem([entry["name"]])
            item.setData(0, Qt.UserRole, entry["uuid"])
            page.entries_list.addTopLevelItem(item)

    def _on_browse_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Folder")
        if folder:
            self.vault_path_input.setText(folder)

    def _on_keyfile_toggled(self, checked):
        self.keyfile_input.setEnabled(checked)
        self.keyfile_btn.setEnabled(checked)

    def _on_browse_keyfile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Key File", "", "All Files (*)")
        if file:
            self.keyfile_input.setText(file)

    def _on_new_vault(self):
        dialog = VaultCreationDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            vault_path = data["path"]

            from storage import Storage
            vault = Storage(vault_path)
            vault.create(data["password"], data.get("keyfile"), data.get("name"))

            self.vault_path_input.clear()
            self.keyfile_input.clear()
            self.password_input.setFocus()
            QMessageBox.information(self, "Success", f"Vault created at: {vault_path}\nNow unlock it.")

    def _on_unlock(self):
        from storage import Storage
        vault_path = Path(self.vault_path_input.text())

        if not vault_path.exists() or not (vault_path / "masterkey").exists():
            self.status_label.setText("Vault does not exist. Create it first.")
            return

        try:
            keyfile = Path(self.keyfile_input.text()) if self.keyfile_input.text() else None

            vault = Storage(vault_path)
            vault.unlock(self.password_input.text(), keyfile)

            page = self._create_vault_page(vault)
            self.stack.setCurrentIndex(1)
            tab_index = self.tabs.addTab(page, vault.name)
            self.tabs.setCurrentIndex(tab_index)
            self._update_window_title()

            self.vault = vault
            self.status_label.setText("")
            self.password_input.clear()
            self.vault_path_input.clear()
            self.keyfile_input.clear()
        except Exception as e:
            self.status_label.setText(f"Failed to unlock: {e}")

    def _on_close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget and hasattr(widget, 'vault'):
            vault = widget.vault
            if vault and vault.is_unlocked():
                vault.lock()
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.stack.setCurrentIndex(0)
            self.setWindowTitle("SecPass")

    def _on_new_tab(self):
        self.stack.setCurrentIndex(0)
        self.vault_path_input.setFocus()
        self._update_window_title()

    @property
    def current_vault_widget(self):
        return self.tabs.currentWidget()

    def _update_window_title(self):
        if self.stack.currentIndex() == 0:
            self.setWindowTitle("SecPass")
            return
        widget = self.tabs.currentWidget()
        if widget and hasattr(widget, 'vault') and widget.vault and widget.vault.is_unlocked():
            vault = widget.vault
            groups_count = len(vault.list_groups())
            entries_count = len(vault.list_entries())
            self.setWindowTitle(f"SecPass :: {vault.name} | groups: {groups_count} | entries: {entries_count}")
        else:
            self.setWindowTitle("SecPass")



def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())