import sys
import uuid
import math
import re
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QListWidget, QStackedWidget, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QTreeWidget, QTreeWidgetItem, QScrollArea,
    QWidget as QWidgetBase, QGridLayout, QGroupBox, QCheckBox, QSlider,
    QSpinBox, QTextEdit, QFileDialog, QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QAction


def calculate_entropy(password: str) -> float:
    if not password:
        return 0.0

    char_sets = 0
    if re.search(r'[a-z]', password):
        char_sets += 1
    if re.search(r'[A-Z]', password):
        char_sets += 1
    if re.search(r'[0-9]', password):
        char_sets += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        char_sets += 1

    pool_size = 0
    if char_sets == 0:
        return 0.0

    if re.search(r'[a-z]', password):
        pool_size += 26
    if re.search(r'[A-Z]', password):
        pool_size += 26
    if re.search(r'[0-9]', password):
        pool_size += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        pool_size += 32

    if pool_size == 0:
        pool_size = 26

    entropy = len(password) * math.log2(pool_size)
    return entropy


def get_strength_level(entropy: float) -> tuple:
    if entropy < 28:
        return 1, "Very Weak", "#ff0000"
    elif entropy < 50:
        return 2, "Weak", "#ff6600"
    elif entropy < 80:
        return 3, "Fair", "#ffcc00"
    elif entropy < 128:
        return 4, "Strong", "#88ff00"
    else:
        return 5, "Very Strong", "#00cc00"


class PasswordStrengthBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entropy = 0
        self._level = 0
        self._label = ""
        self._color = "#333333"
        self.setMinimumHeight(8)
        self.setMaximumHeight(8)

    def set_entropy(self, entropy: float):
        self._entropy = entropy
        self._level, self._label, self._color = get_strength_level(entropy)
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, QColor("#222222"))

        colors = ["#ff0000", "#ff6600", "#ffcc00", "#88ff00", "#00cc00"]
        bar_width = w // 5
        for i in range(5):
            color = colors[i] if i < self._level else "#444444"
            painter.fillRect(i * bar_width + 1, 1, bar_width - 2, h - 2, QColor(color))


class VaultCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Vault")
        self.setMinimumSize(450, 400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.vault_name = QLineEdit()
        self.vault_name.setPlaceholderText("Internal vault name")
        form.addRow("Name:", self.vault_name)

        self.vault_path = QLineEdit()
        self.vault_path.setPlaceholderText("Vault folder path")
        path_btn = QPushButton("Browse...")
        path_btn.clicked.connect(self._on_browse_vault_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.vault_path)
        path_layout.addWidget(path_btn)
        form.addRow("Location:", path_layout)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self._on_password_changed)
        form.addRow("Password:", self.password_input)

        self.strength_bar = PasswordStrengthBar()
        form.addRow("", self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 11px; color: #888;")
        form.addRow("", self.strength_label)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.textChanged.connect(self._on_confirm_changed)
        form.addRow("Confirm:", self.confirm_password)

        self.confirm_label = QLabel("")
        form.addRow("", self.confirm_label)

        self.use_keyfile = QCheckBox("Use a key file as 2nd factor")
        form.addRow("", self.use_keyfile)

        self.keyfile_path = QLineEdit()
        self.keyfile_path.setPlaceholderText("Key file path (optional)")
        keyfile_btn = QPushButton("Browse...")
        keyfile_btn.clicked.connect(self._on_browse_keyfile)
        keyfile_layout = QHBoxLayout()
        keyfile_layout.addWidget(self.keyfile_path)
        keyfile_layout.addWidget(keyfile_btn)
        form.addRow("", keyfile_layout)

        self.use_keyfile.stateChanged.connect(self._on_keyfile_toggled)
        self._on_keyfile_toggled()

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Create Vault")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse_vault_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Location")
        if folder:
            self.vault_path.setText(folder)

    def _on_password_changed(self, text):
        entropy = calculate_entropy(text)
        self.strength_bar.set_entropy(entropy)
        level, label, color = get_strength_level(entropy)
        self.strength_label.setText(f"{label} - {int(entropy)} bits entropy")
        self.strength_label.setStyleSheet("font-size: 11px;")

    def _on_confirm_changed(self, text):
        if self.password_input.text() and self.confirm_password.text():
            if self.password_input.text() == self.confirm_password.text():
                self.confirm_label.setText("✓ Passwords match")
                self.confirm_label.setStyleSheet("color: green;")
            else:
                self.confirm_label.setText("✗ Passwords do not match")
                self.confirm_label.setStyleSheet("color: red;")
        else:
            self.confirm_label.setText("")

    def _on_keyfile_toggled(self):
        enabled = self.use_keyfile.isChecked()
        self.keyfile_path.setEnabled(enabled)

    def _on_browse_keyfile(self):
        file, _ = QFileDialog.getSaveFileName(self, "Create Key File", "", "All Files (*)")
        if file:
            with open(file, 'wb') as f:
                f.write(b'\x00' * 32)
            self.keyfile_path.setText(file)

    def _on_accept(self):
        if not self.vault_name.text():
            QMessageBox.warning(self, "Error", "Please enter a vault name.")
            return
        if not self.vault_path.text():
            QMessageBox.warning(self, "Error", "Please select a vault location.")
            return
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Please enter a password.")
            return
        if self.password_input.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        entropy = calculate_entropy(self.password_input.text())
        if entropy < 80:
            QMessageBox.warning(
                self, "Weak Password",
                f"Password entropy is only {int(entropy)} bits. Minimum required is 80 bits."
            )
            return

        self.accept()

    def get_data(self):
        vault_path = Path(self.vault_path.text())
        return {
            "name": self.vault_name.text(),
            "path": vault_path,
            "password": self.password_input.text(),
            "keyfile": Path(self.keyfile_path.text()) if self.use_keyfile.isChecked() and self.keyfile_path.text() else None
        }


class PasswordGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setMinimumSize(450, 350)
        self._init_ui()
        self._generate()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setStyleSheet("font-size: 16px; font-family: monospace;")
        layout.addWidget(self.password_display)

        self.strength_bar = PasswordStrengthBar()
        layout.addWidget(self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self.strength_label)

        btn_layout = QHBoxLayout()
        regenerate_btn = QPushButton("Generate New")
        regenerate_btn.clicked.connect(self._generate)
        btn_layout.addWidget(regenerate_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        options_group = QGroupBox("Options")
        options_layout = QGridLayout(options_group)

        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 128)
        self.length_spin.setValue(20)
        self.length_spin.valueChanged.connect(self._generate)
        options_layout.addWidget(QLabel("Length:"), 0, 0)
        options_layout.addWidget(self.length_spin, 0, 1)

        self.use_uppercase = QCheckBox("Uppercase (A-Z)")
        self.use_uppercase.setChecked(True)
        self.use_uppercase.stateChanged.connect(self._generate)
        options_layout.addWidget(self.use_uppercase, 1, 0, 1, 2)

        self.use_lowercase = QCheckBox("Lowercase (a-z)")
        self.use_lowercase.setChecked(True)
        self.use_lowercase.stateChanged.connect(self._generate)
        options_layout.addWidget(self.use_lowercase, 2, 0, 1, 2)

        self.use_digits = QCheckBox("Digits (0-9)")
        self.use_digits.setChecked(True)
        self.use_digits.stateChanged.connect(self._generate)
        options_layout.addWidget(self.use_digits, 3, 0, 1, 2)

        self.use_special = QCheckBox("Special (!@#$%^&*)")
        self.use_special.setChecked(True)
        self.use_special.stateChanged.connect(self._generate)
        options_layout.addWidget(self.use_special, 4, 0, 1, 2)

        layout.addWidget(options_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _generate(self):
        import random
        chars = ""
        if self.use_uppercase.isChecked():
            chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if self.use_lowercase.isChecked():
            chars += "abcdefghijklmnopqrstuvwxyz"
        if self.use_digits.isChecked():
            chars += "0123456789"
        if self.use_special.isChecked():
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not chars:
            chars = "abcdefghijklmnopqrstuvwxyz"

        length = self.length_spin.value()
        password = "".join(random.choice(chars) for _ in range(length))
        self.password_display.setText(password)

        entropy = calculate_entropy(password)
        self.strength_bar.set_entropy(entropy)
        level, label, color = get_strength_level(entropy)
        self.strength_label.setText(f"{label} - {int(entropy)} bits entropy")
        self.strength_label.setStyleSheet("font-size: 11px;")

    def get_password(self):
        return self.password_display.text()


class EntryDialog(QDialog):
    def __init__(self, entry_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Entry" if not entry_data else "Edit Entry")
        self.setMinimumSize(500, 500)
        self.entry_data = entry_data or {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.title_input = QLineEdit(self.entry_data.get("name", ""))
        form.addRow("Title:", self.title_input)

        username_layout = QHBoxLayout()
        self.username_input = QLineEdit(self.entry_data.get("username", ""))
        username_layout.addWidget(self.username_input)

        self.copy_username_btn = QPushButton("Copy")
        self.copy_username_btn.clicked.connect(self._copy_username)
        username_layout.addWidget(self.copy_username_btn)
        form.addRow("Username:", username_layout)

        password_layout = QHBoxLayout()
        self.password_input = QLineEdit(self.entry_data.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self._on_password_changed)
        password_layout.addWidget(self.password_input)

        self.show_password_btn = QPushButton("Show")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.toggled.connect(self._toggle_password)
        password_layout.addWidget(self.show_password_btn)

        self.copy_password_btn = QPushButton("Copy")
        self.copy_password_btn.clicked.connect(self._copy_password)
        password_layout.addWidget(self.copy_password_btn)

        self.gen_password_btn = QPushButton("Generate")
        self.gen_password_btn.clicked.connect(self._generate_password)
        password_layout.addWidget(self.gen_password_btn)
        form.addRow("Password:", password_layout)

        self.strength_bar = PasswordStrengthBar()
        form.addRow("Strength:", self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 11px; color: #888;")
        form.addRow("", self.strength_label)

        if self.entry_data.get("password"):
            self._on_password_changed(self.entry_data.get("password"))

        self.url_input = QLineEdit(self.entry_data.get("url", ""))
        form.addRow("URL:", self.url_input)

        self.email_input = QLineEdit(self.entry_data.get("email", ""))
        form.addRow("Email:", self.email_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlainText(self.entry_data.get("notes", ""))
        self.notes_input.setMaximumHeight(80)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok_clicked)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok_clicked(self):
        password = self.password_input.text()
        if password:
            entropy = calculate_entropy(password)
            if entropy < 80:
                QMessageBox.warning(
                    self, "Weak Password",
                    f"Password entropy is only {int(entropy)} bits. Minimum required is 80 bits for security."
                )
                return
        self.accept()

    def _on_password_changed(self, text):
        entropy = calculate_entropy(text)
        self.strength_bar.set_entropy(entropy)
        level, label, color = get_strength_level(entropy)
        self.strength_label.setText(f"{label} - {int(entropy)} bits entropy")
        self.strength_label.setStyleSheet("font-size: 11px;")

    def _toggle_password(self, checked):
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def _copy_username(self):
        QApplication.clipboard().setText(self.username_input.text())

    def _copy_password(self):
        QApplication.clipboard().setText(self.password_input.text())

    def _generate_password(self):
        dialog = PasswordGeneratorDialog(self)
        if dialog.exec():
            self.password_input.setText(dialog.get_password())

    def get_data(self):
        return {
            "name": self.title_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "url": self.url_input.text(),
            "email": self.email_input.text(),
            "notes": self.notes_input.toPlainText(),
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PWDuck - Password Manager")
        self.resize(1000, 650)
        self.vault = None
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.vaults = {}
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._on_close_tab)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedWidth(30)
        new_tab_btn.clicked.connect(self._on_new_tab)
        self.tabs.setCornerWidget(new_tab_btn, Qt.TopRightCorner)

        self._create_login_page()

        self.stack = QStackedWidget()
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

        open_vault_action = QAction("Open Vault", self)
        open_vault_action.triggered.connect(self._on_open_vault)
        file_menu.addAction(open_vault_action)

        file_menu.addSeparator()

        lock_action = QAction("Lock Vault", self)
        lock_action.triggered.connect(self._on_lock)
        file_menu.addAction(lock_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _create_login_page(self):
        self.login_page = QWidget()
        self.login_page.setObjectName("login_page")
        layout = QVBoxLayout(self.login_page)
        layout.setSpacing(15)
        layout.setContentsMargins(100, 80, 100, 80)

        title = QLabel("PWDuck")
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
        self.vault_path_input.setPlaceholderText("Choose vault folder...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.vault_path_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_vault)
        path_layout.addWidget(browse_btn)
        form.addRow("Vault Path:", path_layout)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_unlock)
        form.addRow("Master Password:", self.password_input)

        self.keyfile_input = QLineEdit()
        self.keyfile_input.setPlaceholderText("Optional key file")
        keyfile_layout = QHBoxLayout()
        keyfile_layout.addWidget(self.keyfile_input)
        keyfile_btn = QPushButton("Browse...")
        keyfile_btn.clicked.connect(self._on_browse_keyfile)
        keyfile_layout.addWidget(keyfile_btn)
        form.addRow("Key File:", keyfile_layout)

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

        add_entry_btn = QPushButton("Add Entry")
        add_entry_btn.clicked.connect(lambda: self._on_add_entry_vault(vault))
        toolbar.addWidget(add_entry_btn)

        add_group_btn = QPushButton("Add Group")
        add_group_btn.clicked.connect(lambda: self._on_add_group_vault(vault))
        toolbar.addWidget(add_group_btn)

        toolbar.addSpacing(10)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self._on_edit_entry_vault(vault))
        toolbar.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self._on_delete_entry_vault(vault))
        toolbar.addWidget(delete_btn)

        toolbar.addSpacing(10)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Search entries...")
        search_input.textChanged.connect(lambda t: self._on_search_vault(vault, t))
        search_input.setMinimumWidth(200)
        toolbar.addWidget(search_input)

        toolbar.addStretch()

        copy_username_btn = QPushButton("Copy Username")
        copy_username_btn.clicked.connect(lambda: self._on_copy_username_vault(vault))
        toolbar.addWidget(copy_username_btn)

        copy_password_btn = QPushButton("Copy Password")
        copy_password_btn.clicked.connect(lambda: self._on_copy_password_vault(vault))
        toolbar.addWidget(copy_password_btn)

        lock_btn = QPushButton("Lock")
        lock_btn.clicked.connect(lambda: self._on_lock_vault(vault, page))
        toolbar.addWidget(lock_btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        groups_tree = QTreeWidget()
        groups_tree.setHeaderLabel("Groups")
        groups_tree.itemClicked.connect(lambda item, col: self._on_group_clicked_vault(vault, item, col, search_input.text()))
        groups_tree.itemDoubleClicked.connect(lambda item, col: self._on_group_double_click_vault(vault, item, col))
        splitter.addWidget(groups_tree)

        entries_list = QTreeWidget()
        entries_list.setHeaderLabels(["Name"])
        entries_list.setColumnCount(1)
        entries_list.itemDoubleClicked.connect(lambda item, col: self._on_entry_double_click_vault(vault, item, col))
        splitter.addWidget(entries_list)

        splitter.setSizes([250, 500])

        layout.addWidget(splitter)

        page.groups_tree = groups_tree
        page.entries_list = entries_list

        self._refresh_vault_view(vault, page)

        return page

    def _on_add_entry_vault(self, vault):
        selected = None
        current_widget = self.current_vault_widget
        if current_widget and hasattr(current_widget, 'groups_tree'):
            selected = current_widget.groups_tree.currentItem()
        group_uuid = selected.data(0, Qt.UserRole) if selected else None

        dialog = EntryDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            entry_uuid = vault.create_entry(data["name"], data["url"], group_uuid)
            vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))
            self._refresh_vault_view(vault, self.current_vault_widget)

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
            vault.create_group(name_input.text())
            self._refresh_vault_view(vault, self.current_vault_widget)

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
            vault.update_entry_head(entry_uuid, data["name"], data["url"])
            vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))
            self._refresh_vault_view(vault, page)

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

    def _on_search_vault(self, vault, text):
        self._refresh_vault_view(vault, self.current_vault_widget, text if text else None)

    def _on_group_clicked_vault(self, vault, item, column, search_text):
        group_uuid = item.data(0, Qt.UserRole)
        self._refresh_entries_vault(vault, self.current_vault_widget, group_uuid, search_text if search_text else None)

    def _on_group_double_click_vault(self, vault, item, column):
        group_uuid = item.data(0, Qt.UserRole)
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
            vault.update_group(uuid.UUID(group_uuid), name_input.text())
            self._refresh_vault_view(vault, self.current_vault_widget)

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
            self.setWindowTitle("PWDuck - Password Manager")

    def _refresh_vault_view(self, vault, page, search_query=None):
        if not page or not hasattr(page, 'groups_tree'):
            return

        page.groups_tree.clear()
        root_item = QTreeWidgetItem(["All Entries"])
        root_item.setData(0, Qt.UserRole, None)
        page.groups_tree.addTopLevelItem(root_item)

        for group in vault.list_groups():
            item = QTreeWidgetItem([group["name"]])
            item.setData(0, Qt.UserRole, group["uuid"])
            page.groups_tree.addTopLevelItem(item)
        page.groups_tree.expandAll()

        self._refresh_entries_vault(vault, page, None, search_query)

    def _refresh_entries_vault(self, vault, page, group_uuid=None, search_query=None):
        if not page or not hasattr(page, 'entries_list'):
            return
        page.entries_list.clear()

        for entry in vault.list_entries():
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

    def _create_main_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)

        self.add_entry_btn = QPushButton("Add Entry")
        self.add_entry_btn.clicked.connect(self._on_add_entry)
        toolbar.addWidget(self.add_entry_btn)

        self.add_group_btn = QPushButton("Add Group")
        self.add_group_btn.clicked.connect(self._on_add_group)
        toolbar.addWidget(self.add_group_btn)

        self.edit_group_btn = QPushButton("Edit Group")
        self.edit_group_btn.clicked.connect(self._on_edit_group)
        toolbar.addWidget(self.edit_group_btn)

        self.delete_group_btn = QPushButton("Delete Group")
        self.delete_group_btn.clicked.connect(self._on_delete_group)
        toolbar.addWidget(self.delete_group_btn)

        toolbar.addSpacing(10)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit_entry)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_entry)
        toolbar.addWidget(self.delete_btn)

        toolbar.addSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search entries...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setMinimumWidth(200)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        self.copy_username_btn = QPushButton("Copy Username")
        self.copy_username_btn.clicked.connect(self._on_copy_username)
        toolbar.addWidget(self.copy_username_btn)

        self.copy_password_btn = QPushButton("Copy Password")
        self.copy_password_btn.clicked.connect(self._on_copy_password)
        toolbar.addWidget(self.copy_password_btn)

        self.lock_btn = QPushButton("Lock")
        self.lock_btn.clicked.connect(self._on_lock)
        toolbar.addWidget(self.lock_btn)

        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabel("Groups")
        self.groups_tree.itemClicked.connect(self._on_group_clicked)
        self.groups_tree.itemDoubleClicked.connect(self._on_group_double_click)
        splitter.addWidget(self.groups_tree)

        self.entries_list = QTreeWidget()
        self.entries_list.setHeaderLabels(["Name"])
        self.entries_list.setColumnCount(1)
        self.entries_list.itemDoubleClicked.connect(self._on_entry_double_click)
        splitter.addWidget(self.entries_list)

        splitter.setSizes([250, 500])

        layout.addWidget(splitter)

    def _on_browse_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Folder")
        if folder:
            self.vault_path_input.setText(folder)

    def _on_browse_keyfile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Key File", "", "All Files (*)")
        if file:
            self.keyfile_input.setText(file)

    def _on_new_vault(self):
        dialog = VaultCreationDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            vault_path = data["path"]

            from pwduck.vault import Vault
            vault = Vault(vault_path)
            vault.create(data["password"], data.get("keyfile"), data.get("name"))

            self.vault_path_input.clear()
            self.keyfile_input.clear()
            self.password_input.setFocus()
            QMessageBox.information(self, "Success", f"Vault created at: {vault_path}\nNow unlock it.")

    def _on_open_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Folder")
        if folder:
            self.vault_path_input.setText(folder)
            self.password_input.setFocus()

    def _on_unlock(self):
        from pwduck.vault import Vault
        vault_path = Path(self.vault_path_input.text())

        if not vault_path.exists() or not (vault_path / "masterkey").exists():
            self.status_label.setText("Vault does not exist. Create it first.")
            return

        try:
            keyfile = Path(self.keyfile_input.text()) if self.keyfile_input.text() else None

            vault = Vault(vault_path)
            vault.unlock(self.password_input.text(), keyfile)

            page = self._create_vault_page(vault)
            tab_index = self.tabs.addTab(page, vault.name)
            self.tabs.setCurrentIndex(tab_index)

            self.vault = vault
            self.stack.setCurrentIndex(1)
            self.status_label.setText("")
            self.setWindowTitle(f"PWDuck - {vault.name}")
            self.password_input.clear()
            self.vault_path_input.clear()
            self.keyfile_input.clear()
        except Exception as e:
            self.status_label.setText(f"Failed to unlock: {e}")

    def _on_create_vault(self):
        from pwduck.vault import Vault
        vault_path = Path(self.vault_path_input.text())
        self.vault = Vault(vault_path)

        if self.vault.exists():
            self.status_label.setText("Vault already exists. Unlock it or choose another location.")
            return

        if not self.password_input.text():
            self.status_label.setText("Please enter a password.")
            return

        try:
            keyfile = Path(self.keyfile_input.text()) if self.keyfile_input.text() else None
            self.vault.create(self.password_input.text(), keyfile)
            self.status_label.setText("Vault created! Now unlock it.")
            self.status_label.setStyleSheet("color: green;")
        except Exception as e:
            self.status_label.setText(f"Failed to create: {e}")

    def _on_lock(self):
        if self.vault:
            self.vault.lock()
            self.vault = None
            self.stack.setCurrentIndex(0)
            self.password_input.clear()
            self.setWindowTitle("PWDuck - Password Manager")

    def _on_close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget and hasattr(widget, 'vault'):
            vault = widget.vault
            if vault and vault.is_unlocked():
                vault.lock()
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.stack.setCurrentIndex(0)
            self.setWindowTitle("PWDuck - Password Manager")

    def _on_new_tab(self):
        self.stack.setCurrentIndex(0)
        self.vault_path_input.setFocus()

    @property
    def current_vault_widget(self):
        return self.tabs.currentWidget()

    def _refresh_view(self):
        self._refresh_groups()
        self._refresh_entries()

    def _refresh_groups(self, search_mode=False):
        self.groups_tree.clear()

        if not search_mode:
            root_item = QTreeWidgetItem(["All Entries"])
            root_item.setData(0, Qt.UserRole, None)
            self.groups_tree.addTopLevelItem(root_item)

        if self.vault:
            for group in self.vault.list_groups():
                item = QTreeWidgetItem([group["name"]])
                item.setData(0, Qt.UserRole, group["uuid"])
                self.groups_tree.addTopLevelItem(item)

        self.groups_tree.expandAll()

    def _refresh_entries(self, group_uuid=None, search_query=None):
        self.entries_list.clear()

        if not self.vault:
            return

        for entry in self.vault.list_entries():
            if group_uuid and entry.get("group") != group_uuid:
                continue

            if search_query:
                name = entry.get("name", "").lower()
                url = entry.get("url", "").lower()
                if search_query.lower() not in name and search_query.lower() not in url:
                    continue

            item = QTreeWidgetItem([entry["name"]])
            item.setData(0, Qt.UserRole, entry["uuid"])
            self.entries_list.addTopLevelItem(item)

    def _on_group_clicked(self, item, column):
        group_uuid = item.data(0, Qt.UserRole)
        search_query = self.search_input.text()
        self._refresh_entries(group_uuid, search_query if search_query else None)

    def _on_search(self, text):
        if text:
            self._refresh_groups(search_mode=True)
            self._refresh_entries(search_query=text)
        else:
            self._refresh_groups()
            self._refresh_entries()

    def _on_add_entry(self):
        if not self.vault:
            return

        selected = self.groups_tree.currentItem()
        group_uuid = selected.data(0, Qt.UserRole) if selected else None

        dialog = EntryDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            entry_uuid = self.vault.create_entry(data["name"], data["url"], group_uuid)
            self.vault.set_entry_body(entry_uuid, data["username"], data["password"])
            self._refresh_view()

    def _on_add_group(self):
        if not self.vault:
            return

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
            self.vault.create_group(name_input.text())
            self._refresh_groups()

    def _on_edit_group(self):
        selected = self.groups_tree.currentItem()
        if not selected:
            return

        group_uuid = selected.data(0, Qt.UserRole)
        if not group_uuid:
            return

        group = self.vault.get_group(uuid.UUID(group_uuid))
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
            self.vault.update_group(uuid.UUID(group_uuid), name_input.text())
            self._refresh_groups()

    def _on_delete_group(self):
        selected = self.groups_tree.currentItem()
        if not selected:
            return

        group_uuid = selected.data(0, Qt.UserRole)
        if not group_uuid:
            return

        reply = QMessageBox.question(
            self, "Delete Group",
            "Are you sure you want to delete this group?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.vault.delete_group(uuid.UUID(group_uuid))
            self._refresh_groups()

    def _on_group_double_click(self, item, column):
        group_uuid = item.data(0, Qt.UserRole)
        if group_uuid:
            self._on_edit_group()

    def _on_edit_entry(self):
        self._edit_selected_entry()

    def _on_entry_double_click(self, item, column):
        self._edit_selected_entry()

    def _edit_selected_entry(self):
        selected = self.entries_list.currentItem()
        if not selected:
            return

        entry_uuid_str = selected.data(0, Qt.UserRole)
        if not entry_uuid_str:
            return

        entry_uuid = uuid.UUID(entry_uuid_str)
        head = self.vault.get_entry_head(entry_uuid)
        body = self.vault.get_entry_body(entry_uuid)

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
            self.vault.update_entry_head(entry_uuid, data["name"], data["url"])
            self.vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))
            self._refresh_view()

    def _on_delete_entry(self):
        selected = self.entries_list.currentItem()
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
                head_file = self.vault.entries_path / f"{self.vault._hash_uuid(uuid.UUID(entry_uuid))}.head"
                body_file = self.vault.entries_path / f"{self.vault._hash_uuid(uuid.UUID(entry_uuid))}.body"
                if head_file.exists():
                    head_file.unlink()
                if body_file.exists():
                    body_file.unlink()
                self._refresh_view()

    def _on_copy_username(self):
        selected = self.entries_list.currentItem()
        if not selected:
            return

        entry_uuid = selected.data(0, Qt.UserRole)
        if entry_uuid:
            body = self.vault.get_entry_body(uuid.UUID(entry_uuid))
            if body:
                QApplication.clipboard().setText(body.get("username", ""))

    def _on_copy_password(self):
        selected = self.entries_list.currentItem()
        if not selected:
            return

        entry_uuid = selected.data(0, Qt.UserRole)
        if entry_uuid:
            body = self.vault.get_entry_body(uuid.UUID(entry_uuid))
            if body:
                QApplication.clipboard().setText(body.get("password", ""))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()