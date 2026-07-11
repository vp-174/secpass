from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QFileDialog, QFormLayout, QMessageBox, QApplication, QCheckBox, QDialogButtonBox)
from PySide6.QtCore import Qt
from gui.helpers.password_utils import calculate_entropy, get_strength_level, _generate_password_for
from gui.views.password_strength_bar import PasswordStrengthBar


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

        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self._on_password_changed)
        password_layout.addWidget(self.password_input)
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedWidth(35)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setToolTip("Show/Hide password")
        self.show_password_btn.toggled.connect(self._toggle_password)
        password_layout.addWidget(self.show_password_btn)
        self.copy_password_btn = QPushButton("📋")
        self.copy_password_btn.setFixedWidth(35)
        self.copy_password_btn.setToolTip("Copy password")
        self.copy_password_btn.clicked.connect(self._copy_password)
        password_layout.addWidget(self.copy_password_btn)
        self.gen_password_btn = QPushButton("🎲")
        self.gen_password_btn.setFixedWidth(35)
        self.gen_password_btn.setToolTip("Generate password")
        self.gen_password_btn.clicked.connect(self._generate_password)
        password_layout.addWidget(self.gen_password_btn)
        form.addRow("Password:", password_layout)

        self.strength_bar = PasswordStrengthBar()
        self.strength_bar.set_entropy(0.0)
        form.addRow("", self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setText(f"{get_strength_level(0.0)[1]} - {int(0.0)} bits entropy")
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

    def _generate_password(self):
        _generate_password_for(self.password_input, self)

    def _toggle_password(self, checked):
        self.password_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_password_btn.setText("🔒" if checked else "👁")

    def _copy_password(self):
        QApplication.clipboard().setText(self.password_input.text())

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
