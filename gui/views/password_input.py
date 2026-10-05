from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.helpers.password_utils import (
    _generate_password_for,
    calculate_entropy,
    get_strength_level,
)
from gui.views.password_strength_bar import PasswordStrengthBar

CLIPBOARD_CLEAR_MS = 30_000


def copy_to_clipboard(text: str) -> None:
    """Копирует текст и автоматически очищает буфер обмена через 30 секунд
    (только если содержимое не успело измениться)."""
    if not text:
        return
    clipboard = QApplication.clipboard()
    clipboard.setText(text)

    def _clear():
        if clipboard.text() == text:
            clipboard.clear()

    QTimer.singleShot(CLIPBOARD_CLEAR_MS, _clear)


class PasswordInput(QWidget):
    """Поле пароля с кнопками показа/копирования/генерации
    и (опционально) индикатором надёжности."""

    def __init__(self, show_strength: bool = True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.line_edit = QLineEdit()
        self.line_edit.setEchoMode(QLineEdit.Password)
        self.line_edit.textChanged.connect(self._on_changed)
        row.addWidget(self.line_edit, 1)

        self.show_btn = QPushButton("👁")
        self.show_btn.setFixedWidth(35)
        self.show_btn.setCheckable(True)
        self.show_btn.setToolTip("Show/Hide password")
        self.show_btn.toggled.connect(self._toggle)
        row.addWidget(self.show_btn)

        self.copy_btn = QPushButton("📋")
        self.copy_btn.setFixedWidth(35)
        self.copy_btn.setToolTip("Copy password (auto-clears in 30 s)")
        self.copy_btn.clicked.connect(lambda: copy_to_clipboard(self.line_edit.text()))
        row.addWidget(self.copy_btn)

        self.gen_btn = QPushButton("🎲")
        self.gen_btn.setFixedWidth(35)
        self.gen_btn.setToolTip("Generate password")
        self.gen_btn.clicked.connect(self._generate)
        row.addWidget(self.gen_btn)

        layout.addLayout(row)

        self.strength_bar = None
        self.strength_label = None
        if show_strength:
            self.strength_bar = PasswordStrengthBar()
            self.strength_bar.set_entropy(0.0)
            layout.addWidget(self.strength_bar)
            self.strength_label = QLabel("")
            self.strength_label.setStyleSheet("font-size: 11px; color: #888;")
            layout.addWidget(self.strength_label)
            self._on_changed("")

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, value: str) -> None:
        self.line_edit.setText(value)

    def _toggle(self, checked: bool) -> None:
        self.line_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_btn.setText("🔒" if checked else "👁")

    def _generate(self) -> None:
        _generate_password_for(self.line_edit, self)

    def _on_changed(self, text: str) -> None:
        if self.strength_bar is None:
            return
        entropy = calculate_entropy(text)
        self.strength_bar.set_entropy(entropy)
        _, label = get_strength_level(entropy)
        self.strength_label.setText(f"{label} - {int(entropy)} bits entropy")
