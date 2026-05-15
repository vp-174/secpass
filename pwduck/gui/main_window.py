import sys
import uuid
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QListWidget, QStackedWidget, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QTreeWidget, QTreeWidgetItem, QScrollArea,
    QWidget as QWidgetBase, QGridLayout, QGroupBox, QCheckBox, QSlider,
    QSpinBox, QTextEdit, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QAction


class PasswordGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setMinimumSize(400, 300)
        self._init_ui()
        self._generate()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setStyleSheet("font-size: 16px; font-family: monospace;")
        layout.addWidget(self.password_display)

        regenerate_btn = QPushButton("Generate New")
        regenerate_btn.clicked.connect(self._generate)
        layout.addWidget(regenerate_btn)

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

    def get_password(self):
        return self.password_display.text()


class PasswordStrengthIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)

    def set_score(self, score):
        self._score = max(0, min(100, score))
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        colors = [QColor("#ff0000"), QColor("#ff4400"), QColor("#ff8800"), QColor("#ffff00"), QColor("#88ff00"), QColor("#00ff00")]
        color = colors[min(self._score // 20, 5)]

        painter.fillRect(0, 0, w, h, QColor("#333333"))
        fill_width = int(w * self._score / 100)
        if fill_width > 0:
            painter.fillRect(0, 0, fill_width, h, color)

        painter.setPen(QColor("#ffffff"))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self._score}%")

    def calculate_strength(self, password):
        if not password:
            self.set_score(0)
            return

        score = 0

        if len(password) >= 8:
            score += 10
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10

        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if has_lower:
            score += 15
        if has_upper:
            score += 15
        if has_digit:
            score += 15
        if has_special:
            score += 25

        common_passwords = ["password", "123456", "qwerty", "admin", "letmein", "welcome"]
        if password.lower() in common_passwords:
            score = max(score - 50, 5)

        self.set_score(score)


class EntryDialog(QDialog):
    def __init__(self, entry_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Entry" if not entry_data else "Edit Entry")
        self.setMinimumSize(500, 400)
        self.entry_data = entry_data or {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.title_input = QLineEdit(self.entry_data.get("name", ""))
        form.addRow("Title:", self.title_input)

        username_layout = QHBoxLayout()
        self.username_input = QLineEdit(self.entry_data.get("username", ""))
        self.username_input.textChanged.connect(self._on_username_changed)
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

        self.strength_indicator = PasswordStrengthIndicator()
        form.addRow("Strength:", self.strength_indicator)

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
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_password_changed(self, text):
        self.strength_indicator.calculate_strength(text)

    def _on_username_changed(self, text):
        pass

    def _toggle_password(self, checked):
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def _copy_username(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.username_input.text())

    def _copy_password(self):
        from PySide6.QtWidgets import QApplication
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
        self.resize(900, 600)
        self.vault = None
        self._init_ui()
        self._create_menu()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self._create_login_page()
        self._create_main_page()

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
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(100, 100, 100, 100)

        title = QLabel("PWDuck")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Password Manager")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Master Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_unlock)
        layout.addWidget(self.password_input)

        self.vault_path_input = QLineEdit()
        self.vault_path_input.setPlaceholderText("Vault Path")
        self.vault_path_input.setText(str(Path.cwd() / "vault"))
        layout.addWidget(self.vault_path_input)

        self.keyfile_input = QLineEdit()
        self.keyfile_input.setPlaceholderText("Key File (optional)")
        layout.addWidget(self.keyfile_input)

        keyfile_btn = QPushButton("Browse...")
        keyfile_btn.clicked.connect(self._on_browse_keyfile)
        keyfile_layout = QHBoxLayout()
        keyfile_layout.addWidget(self.keyfile_input)
        keyfile_layout.addWidget(keyfile_btn)
        layout.addLayout(keyfile_layout)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setMinimumHeight(40)
        self.unlock_btn.clicked.connect(self._on_unlock)
        self.create_btn = QPushButton("Create Vault")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.create_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #cc0000;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.stack.addWidget(page)

    def _create_main_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        toolbar = QHBoxLayout()

        self.add_entry_btn = QPushButton("Add Entry")
        self.add_entry_btn.clicked.connect(self._on_add_entry)
        toolbar.addWidget(self.add_entry_btn)

        self.add_group_btn = QPushButton("Add Group")
        self.add_group_btn.clicked.connect(self._on_add_group)
        toolbar.addWidget(self.add_group_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit_entry)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_entry)
        toolbar.addWidget(self.delete_btn)

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
        splitter.addWidget(self.groups_tree)

        self.entries_list = QTreeWidget()
        self.entries_list.setHeaderLabel("Entries")
        self.entries_list.setColumnCount(2)
        self.entries_list.setHeaderLabels(["Name", "URL"])
        self.entries_list.itemDoubleClicked.connect(self._on_entry_double_click)
        splitter.addWidget(self.entries_list)

        splitter.setSizes([250, 450])

        layout.addWidget(splitter)

        self.stack.addWidget(page)

    def _on_browse_keyfile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Key File", "", "All Files (*)")
        if file:
            self.keyfile_input.setText(file)

    def _on_new_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Location")
        if folder:
            self.vault_path_input.setText(folder)
            self.password_input.setFocus()

    def _on_open_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Folder")
        if folder:
            self.vault_path_input.setText(folder)
            self._on_unlock()

    def _on_unlock(self):
        from pwduck.vault import Vault
        vault_path = Path(self.vault_path_input.text())
        self.vault = Vault(vault_path)

        if not self.vault.exists():
            self.status_label.setText("Vault does not exist. Create it first.")
            return

        try:
            keyfile = Path(self.keyfile_input.text()) if self.keyfile_input.text() else None
            self.vault.unlock(self.password_input.text(), keyfile)
            self._refresh_view()
            self.stack.setCurrentIndex(1)
            self.status_label.setText("")
        except Exception as e:
            self.status_label.setText(f"Failed to unlock: {e}")

    def _on_create(self):
        from pwduck.vault import Vault
        vault_path = Path(self.vault_path_input.text())
        self.vault = Vault(vault_path)

        if self.vault.exists():
            self.status_label.setText("Vault already exists.")
            return

        if not self.password_input.text():
            self.status_label.setText("Password cannot be empty.")
            return

        try:
            keyfile = Path(self.keyfile_input.text()) if self.keyfile_input.text() else None
            self.vault.create(self.password_input.text(), keyfile)
            self.status_label.setText("Vault created! Now unlock it.")
        except Exception as e:
            self.status_label.setText(f"Failed to create: {e}")

    def _on_lock(self):
        if self.vault:
            self.vault.lock()
            self.vault = None
            self.stack.setCurrentIndex(0)
            self.password_input.clear()

    def _refresh_view(self):
        self._refresh_groups()
        self._refresh_entries()

    def _refresh_groups(self):
        self.groups_tree.clear()

        root_item = QTreeWidgetItem(["All Entries"])
        root_item.setData(0, Qt.UserRole, None)
        self.groups_tree.addTopLevelItem(root_item)

        if self.vault:
            for group in self.vault.list_groups():
                item = QTreeWidgetItem([group["name"]])
                item.setData(0, Qt.UserRole, group["uuid"])
                self.groups_tree.addTopLevelItem(item)

        self.groups_tree.expandAll()

    def _refresh_entries(self, group_uuid=None):
        self.entries_list.clear()

        if not self.vault:
            return

        for entry in self.vault.list_entries():
            if group_uuid and entry.get("group") != group_uuid:
                continue

            item = QTreeWidgetItem([entry["name"], entry.get("url", "")])
            item.setData(0, Qt.UserRole, entry["uuid"])
            self.entries_list.addTopLevelItem(item)

    def _on_group_clicked(self, item, column):
        group_uuid = item.data(0, Qt.UserRole)
        self._refresh_entries(group_uuid)

    def _on_add_entry(self):
        if not self.vault:
            return

        selected = self.groups_tree.currentItem()
        group_uuid = selected.data(0, Qt.UserRole) if selected else None

        dialog = EntryDialog(self)
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

    def _on_edit_entry(self):
        self._edit_selected_entry()

    def _on_entry_double_click(self, item, column):
        self._edit_selected_entry()

    def _edit_selected_entry(self):
        selected = self.entries_list.currentItem()
        if not selected:
            return

        entry_uuid = selected.data(0, Qt.UserRole)
        if not entry_uuid:
            return

        head = self.vault.get_entry_head(uuid.UUID(entry_uuid))
        body = self.vault.get_entry_body(uuid.UUID(entry_uuid))

        entry_data = {
            "name": head.get("name", ""),
            "url": head.get("url", ""),
            "username": body.get("username", "") if body else "",
            "password": body.get("password", "") if body else "",
        }

        dialog = EntryDialog(entry_data, self)
        if dialog.exec():
            data = dialog.get_data()
            self.vault.set_entry_body(uuid.UUID(entry_uuid), data["username"], data["password"])
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
            pass

    def _on_copy_username(self):
        selected = self.entries_list.currentItem()
        if not selected:
            return

        entry_uuid = selected.data(0, Qt.UserRole)
        if entry_uuid:
            body = self.vault.get_entry_body(uuid.UUID(entry_uuid))
            if body:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(body.get("username", ""))

    def _on_copy_password(self):
        selected = self.entries_list.currentItem()
        if not selected:
            return

        entry_uuid = selected.data(0, Qt.UserRole)
        if entry_uuid:
            body = self.vault.get_entry_body(uuid.UUID(entry_uuid))
            if body:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(body.get("password", ""))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()