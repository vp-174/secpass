from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from gui.helpers.password_utils import get_strength_level


class PasswordStrengthBar(QWidget):
    """Виджет индикатора надёжности пароля: цветовая шкала от красного до зелёного."""
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
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, QColor("#222222"))

        colors = ["#ff0000", "#ff6600", "#ffcc00", "#88ff00", "#00cc00"]
        bar_width = w // 5
        for i in range(5):
            color = colors[i] if i < self._level else "#444444"
            painter.fillRect(i * bar_width + 1, 1, bar_width - 2, h - 2, QColor(color))
