import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PWDuck - Password Manager")
        self.resize(800, 600)
        self.vault = None
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self._create_login_page()
        self._create_main_page()

    def _create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(100, 100, 100, 100)

        title = QLabel("PWDuck")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Master Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.vault_path_input = QLineEdit()
        self.vault_path_input.setPlaceholderText("Vault Path")
        self.vault_path_input.setText(str(Path.cwd() / "vault"))
        layout.addWidget(self.vault_path_input)

        btn_layout = QHBoxLayout()
        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.clicked.connect(self._on_unlock)
        self.create_btn = QPushButton("Create Vault")
        self.create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.create_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.stack.addWidget(page)

    def _create_main_page(self):
        from pwduck.vault import Vault
        page = QWidget()
        layout = QVBoxLayout(page)

        toolbar = QHBoxLayout()
        self.add_entry_btn = QPushButton("Add Entry")
        self.add_entry_btn.clicked.connect(self._on_add_entry)
        self.lock_btn = QPushButton("Lock")
        self.lock_btn.clicked.connect(self._on_lock)
        toolbar.addWidget(self.add_entry_btn)
        toolbar.addWidget(self.lock_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.entries_list = QListWidget()
        self.entries_list.itemDoubleClicked.connect(self._on_entry_click)
        layout.addWidget(self.entries_list)

        self.stack.addWidget(page)

    def _on_unlock(self):
        from pwduck.vault import Vault
        vault_path = Path(self.vault_path_input.text())
        self.vault = Vault(vault_path)

        if not self.vault.exists():
            self.status_label.setText("Vault does not exist. Create it first.")
            return

        try:
            self.vault.unlock(self.password_input.text())
            self._refresh_entries()
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

        try:
            self.vault.create(self.password_input.text())
            self.status_label.setText("Vault created! Now unlock it.")
        except Exception as e:
            self.status_label.setText(f"Failed to create: {e}")

    def _on_lock(self):
        if self.vault:
            self.vault.lock()
            self.vault = None
            self.stack.setCurrentIndex(0)

    def _refresh_entries(self):
        if not self.vault:
            return
        self.entries_list.clear()
        for entry in self.vault.list_entries():
            self.entries_list.addItem(f"{entry['name']} - {entry.get('url', '')}")

    def _on_add_entry(self):
        if not self.vault:
            return
        name, url = "New Entry", "https://example.com"
        username, password = "user", "pass123"
        entry_uuid = self.vault.create_entry(name, url)
        self.vault.set_entry_body(entry_uuid, username, password)
        self._refresh_entries()

    def _on_entry_click(self, item):
        pass


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()