import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
)

from gui.helpers.password_utils import MIN_ENTROPY_BITS, calculate_entropy
from gui.views.password_input import PasswordInput, copy_to_clipboard


class EntryDialog(QDialog):
    """Диалог создания/редактирования записи: название, URL, логин, пароль, email, заметки."""

    def __init__(self, entry_data=None, parent=None):
        super().__init__(parent)
        name = entry_data.get("name", "") if entry_data else ""
        self.setWindowTitle(f"Edit Entry ({name})" if entry_data else "Entry")
        self.setMinimumSize(640, 0)
        self.resize(640, 240)
        self.entry_data = entry_data or {}
        self._init_ui()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.layout().setSizeConstraint(QLayout.SetMinAndMaxSize)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignRight)

        self.title_input = QLineEdit(self.entry_data.get("name", ""))
        form.addRow("Title:", self.title_input)

        username_layout = QHBoxLayout()
        self.username_input = QLineEdit(self.entry_data.get("username", ""))
        username_layout.addWidget(self.username_input)
        self.copy_username_btn = QPushButton("📋")
        self.copy_username_btn.setFixedWidth(35)
        self.copy_username_btn.setToolTip("Copy username (auto-clears in 30 s)")
        self.copy_username_btn.clicked.connect(
            lambda: copy_to_clipboard(self.username_input.text())
        )
        username_layout.addWidget(self.copy_username_btn)
        form.addRow("Username:", username_layout)

        self.password_input = PasswordInput(show_strength=True)
        self.password_input.setText(self.entry_data.get("password", ""))
        form.addRow("Password:", self.password_input)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Re-enter password to confirm changes")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.textChanged.connect(self._on_confirm_changed)
        form.addRow("Confirm:", self.confirm_password)

        self.confirm_label = QLabel("")
        form.addRow("", self.confirm_label)

        self.url_input = QLineEdit(self.entry_data.get("url", ""))
        form.addRow("URL:", self.url_input)

        self.email_input = QLineEdit(self.entry_data.get("email", ""))
        form.addRow("Email:", self.email_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlainText(self.entry_data.get("notes", ""))
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setFont(self.font())
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok_clicked)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok_clicked(self):
        if not self.title_input.text():
            QMessageBox.warning(self, "Error", "Please enter a title.")
            return
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Error", "Please enter a password.")
            return
        entropy = calculate_entropy(password)
        if entropy < MIN_ENTROPY_BITS:
            QMessageBox.warning(
                self,
                "Weak Password",
                f"Password entropy is only {int(entropy)} bits. "
                f"Minimum required is {MIN_ENTROPY_BITS} bits for security.",
            )
            return

        if password != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        url = self.url_input.text()
        if url and not url.startswith(("http://", "https://", "ftp://", "file://")):
            QMessageBox.warning(
                self,
                "Invalid URL",
                "URL must start with http://, https://, ftp:// or file://",
            )
            return

        email = self.email_input.text()
        if email:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                QMessageBox.warning(
                    self,
                    "Invalid Email",
                    "Please enter a valid email address (e.g., user@example.com)",
                )
                return

        if self.entry_data:
            reply = QMessageBox.question(
                self,
                "Confirm Save",
                "Are you sure you want to save the changes to this entry?",
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if reply != QMessageBox.Yes:
                self.reject()
                return

        self.accept()

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

    def get_data(self):
        return {
            "name": self.title_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "url": self.url_input.text(),
            "email": self.email_input.text(),
            "notes": self.notes_input.toPlainText(),
        }
