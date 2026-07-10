import re
import math
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QFormLayout, QTextEdit, QMessageBox, QLayout, QSizePolicy, QDialogButtonBox,
    QApplication)
from PySide6.QtCore import Qt
from gui.helpers.password_utils import calculate_entropy, get_strength_level, _generate_password_for
from gui.views.password_strength_bar import PasswordStrengthBar


class EntryDialog(QDialog):
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
        self.copy_username_btn.setToolTip("Copy username")
        self.copy_username_btn.clicked.connect(self._copy_username)
        username_layout.addWidget(self.copy_username_btn)
        form.addRow("Username:", username_layout)

        password_layout = QHBoxLayout()
        self.password_input = QLineEdit(self.entry_data.get("password", ""))
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
        form.addRow("Strength:", self.strength_bar)

        self.strength_label = QLabel("")
        self.strength_label.setText(f"{get_strength_level(0.0)[1]} - {int(0.0)} bits entropy")
        self.strength_label.setStyleSheet("font-size: 11px; color: #888;")
        form.addRow("", self.strength_label)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Re-enter password to confirm changes")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.textChanged.connect(self._on_confirm_changed)
        form.addRow("Confirm:", self.confirm_password)

        self.confirm_label = QLabel("")
        form.addRow("", self.confirm_label)

        if self.entry_data.get("password"):
            self._on_password_changed(self.entry_data.get("password"))

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
        if entropy < 80:
            QMessageBox.warning(
                self, "Weak Password",
                f"Password entropy is only {int(entropy)} bits. Minimum required is 80 bits for security."
            )
            return

        if self.password_input.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        url = self.url_input.text()
        if url:
            if not url.startswith(("http://", "https://", "ftp://", "file://")):
                QMessageBox.warning(
                    self, "Invalid URL",
                    "URL must start with http://, https://, ftp:// or file://"
                )
                return

        email = self.email_input.text()
        if email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                QMessageBox.warning(
                    self, "Invalid Email",
                    "Please enter a valid email address (e.g., user@example.com)"
                )
                return

        if self.entry_data:
            reply = QMessageBox.question(
                self, "Confirm Save",
                "Are you sure you want to save the changes to this entry?",
                QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel
            )
            if reply != QMessageBox.Yes:
                self.reject()
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
        self.show_password_btn.setText("🔒" if checked else "👁")

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

    def _copy_username(self):
        QApplication.clipboard().setText(self.username_input.text())

    def _copy_password(self):
        QApplication.clipboard().setText(self.password_input.text())

    def _generate_password(self):
        _generate_password_for(self.password_input, self)

    def get_data(self):
        return {
            "name": self.title_input.text(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "url": self.url_input.text(),
            "email": self.email_input.text(),
            "notes": self.notes_input.toPlainText(),
        }
