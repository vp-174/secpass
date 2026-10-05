from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QVBoxLayout


class GroupDialog(QDialog):
    """Диалог создания/переименования группы."""

    def __init__(self, title: str = "Group", name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Group Name")
        layout.addWidget(self.name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_name(self) -> str:
        return self.name_input.text().strip()
