import secrets
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from gui.helpers.password_utils import (
    MIN_ENTROPY_BITS,
    MIN_MASTER_LENGTH,
    calculate_entropy,
)
from gui.views.password_input import PasswordInput

KEYFILE_SIZE = 32


class VaultCreationDialog(QDialog):
    """Диалог создания нового хранилища: имя, путь, пароль, подтверждение, ключ-файл."""

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

        self.password_input = PasswordInput(show_strength=True)
        form.addRow("Password:", self.password_input)

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
        keyfile_btn = QPushButton("Create...")
        keyfile_btn.clicked.connect(self._on_create_keyfile)
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

    def _on_create_keyfile(self):
        file, _ = QFileDialog.getSaveFileName(self, "Create Key File", "", "All Files (*)")
        if not file:
            return
        path = Path(file)
        if path.exists():
            QMessageBox.warning(
                self,
                "Key File Exists",
                "This file already exists. Choose a new file name — "
                "existing files are never overwritten.",
            )
            return
        try:
            with open(path, "wb") as f:
                f.write(secrets.token_bytes(KEYFILE_SIZE))
            try:
                path.chmod(0o600)
            except OSError:
                pass
        except OSError as e:
            QMessageBox.critical(self, "Key File Error", f"Could not create key file: {e}")
            return
        self.keyfile_path.setText(file)

    def _on_accept(self):
        if not self.vault_name.text():
            QMessageBox.warning(self, "Error", "Please enter a vault name.")
            return
        if not self.vault_path.text():
            QMessageBox.warning(self, "Error", "Please select a vault location.")
            return

        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Error", "Please enter a password.")
            return
        if password != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        if len(password) < MIN_MASTER_LENGTH:
            QMessageBox.warning(
                self,
                "Password Too Short",
                f"Master password must be at least {MIN_MASTER_LENGTH} characters long.",
            )
            return

        entropy = calculate_entropy(password)
        if entropy < MIN_ENTROPY_BITS:
            QMessageBox.warning(
                self,
                "Weak Password",
                f"Password entropy is only {int(entropy)} bits. "
                f"Minimum required is {MIN_ENTROPY_BITS} bits.",
            )
            return

        if self.use_keyfile.isChecked() and not self.keyfile_path.text():
            QMessageBox.warning(
                self,
                "Key File Required",
                "Please create or select a key file, or uncheck the key file option.",
            )
            return

        self.accept()

    def get_data(self):
        vault_path = Path(self.vault_path.text())
        keyfile = None
        if self.use_keyfile.isChecked() and self.keyfile_path.text():
            keyfile = Path(self.keyfile_path.text())
        return {
            "name": self.vault_name.text(),
            "path": vault_path,
            "password": self.password_input.text(),
            "keyfile": keyfile,
        }
