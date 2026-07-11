import math
import random
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QCheckBox, QSpinBox, QGroupBox, QFormLayout, QGridLayout, QDialogButtonBox)
from PySide6.QtCore import Qt
from gui.helpers.password_utils import calculate_entropy, get_strength_level
from gui.views.password_strength_bar import PasswordStrengthBar


class PasswordGeneratorDialog(QDialog):
    """Диалог генератора паролей: длина, символы, исключение повторов,
    отображение энтропии."""
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
