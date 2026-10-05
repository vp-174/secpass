import sys
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.dialogs.vault_creation_dialog import VaultCreationDialog
from gui.views.vault_page import VaultPage
from storage import (
    InvalidPasswordError,
    KeyfileError,
    Storage,
    StorageError,
    TamperError,
    VaultExistsError,
    VaultNotFoundError,
)

IDLE_LOCK_MS = 5 * 60 * 1000

TABS_STYLE = """
    QTabWidget::pane { border: 0; }
    QTabBar::close-button { margin: 0; padding: 0; }
    QTabBar { spacing: 0; padding: 0; }
    QTabBar::tab { padding: 4px 8px; }
"""


def _resource_dir() -> Path:
    """Папка ресурсов: временная распаковка PyInstaller (_MEIPASS)
    или корень проекта при запуске из исходников."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).parent.parent


class MainWindow(QMainWindow):
    """Главное окно приложения: строка входа, вкладки хранилищ, меню,
    автоблокировка по бездействию и блокировка при закрытии."""

    def __init__(self):
        super().__init__()
        icon_path = _resource_dir() / "secpass.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowTitle("SecPass")
        self.resize(1000, 650)

        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(IDLE_LOCK_MS)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

        self._init_ui()
        self._create_menu()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._idle_timer.start()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(False)
        self.tabs.tabCloseRequested.connect(self._on_close_tab)
        self.tabs.currentChanged.connect(self._update_window_title)
        self.tabs.setStyleSheet(TABS_STYLE)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(36, 24)
        new_tab_btn.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0; margin: 0;")
        new_tab_btn.clicked.connect(self._on_new_tab)

        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 2, 8, 2)
        corner_layout.addWidget(new_tab_btn)
        self.tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)

        self._create_login_page()

        self.stack = QStackedWidget()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.tabs)
        self.stack.setCurrentIndex(0)

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        new_vault_action = QAction("New Vault", self)
        new_vault_action.triggered.connect(self._on_new_vault)
        file_menu.addAction(new_vault_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _on_about(self):
        QMessageBox.about(
            self,
            "About SecPass",
            "<b>SecPass</b><br><br>"
            "Version: 2.0.0<br>"
            "Developer: Vladislav Panov<br>"
            "Contact: abasecode@gmail.com<br>"
            "<a href='https://fr-space.ru'>https://fr-space.ru</a>",
        )

    def _create_login_page(self):
        self.login_page = QWidget()
        self.login_page.setObjectName("login_page")
        layout = QVBoxLayout(self.login_page)
        layout.setSpacing(15)
        layout.setContentsMargins(100, 80, 100, 80)

        title = QLabel("SecPass")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Secure Password Manager")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #888;")
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        form = QFormLayout()
        form.setSpacing(10)

        self.vault_path_input = QLineEdit()
        self.vault_path_input.setObjectName("vault_path")
        self.vault_path_input.setPlaceholderText("Choose vault...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.vault_path_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_vault)
        path_layout.addWidget(browse_btn)
        form.addRow("Vault Path:", path_layout)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self._on_unlock)
        self.password_input.setPlaceholderText("Write your strong password...")
        password_row = QHBoxLayout()
        password_row.addWidget(self.password_input, 1)
        self.use_keyfile_cb = QCheckBox("Use key file")
        self.use_keyfile_cb.toggled.connect(self._on_keyfile_toggled)
        password_row.addWidget(self.use_keyfile_cb)
        form.addRow("Password:", password_row)

        self.keyfile_input = QLineEdit()
        self.keyfile_input.setPlaceholderText("Key file path...")
        self.keyfile_input.setEnabled(False)
        keyfile_layout = QHBoxLayout()
        keyfile_layout.addWidget(self.keyfile_input)
        self.keyfile_btn = QPushButton("Browse...")
        self.keyfile_btn.setEnabled(False)
        self.keyfile_btn.clicked.connect(self._on_browse_keyfile)
        keyfile_layout.addWidget(self.keyfile_btn)
        form.addRow("", keyfile_layout)

        layout.addLayout(form)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setMinimumHeight(45)
        self.unlock_btn.clicked.connect(self._on_unlock)
        btn_layout.addWidget(self.unlock_btn)
        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #cc0000;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    # --- автоблокировка ---

    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.KeyPress,
            QEvent.MouseButtonPress,
            QEvent.MouseMove,
            QEvent.Wheel,
        ):
            self._idle_timer.start()
        return super().eventFilter(obj, event)

    def _on_idle_timeout(self):
        if self.tabs.count():
            self._lock_all()
            self.status_label.setText("Vault locked due to inactivity.")
        self._idle_timer.start()

    def _lock_all(self):
        for i in range(self.tabs.count() - 1, -1, -1):
            page = self.tabs.widget(i)
            if isinstance(page, VaultPage):
                page.storage.lock()
                page.deleteLater()
            self.tabs.removeTab(i)
        self.stack.setCurrentIndex(0)
        self.password_input.clear()
        self._update_window_title()

    def closeEvent(self, event):
        self._lock_all()
        super().closeEvent(event)

    # --- вкладки и хранилища ---

    def _create_vault_page(self, storage: Storage) -> VaultPage:
        page = VaultPage(storage, self)
        page.lock_requested.connect(lambda p=page: self._lock_page(p))
        page.changed.connect(self._update_window_title)
        return page

    def _lock_page(self, page: VaultPage):
        page.storage.lock()
        index = self.tabs.indexOf(page)
        if index >= 0:
            self.tabs.removeTab(index)
        page.deleteLater()
        if self.tabs.count() == 0:
            self.stack.setCurrentIndex(0)
            self.setWindowTitle("SecPass")

    def _on_close_tab(self, index):
        page = self.tabs.widget(index)
        if isinstance(page, VaultPage):
            page.storage.lock()
            page.deleteLater()
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.stack.setCurrentIndex(0)
            self.setWindowTitle("SecPass")

    def _update_window_title(self):
        if self.stack.currentIndex() == 0:
            self.setWindowTitle("SecPass")
            return
        page = self.tabs.currentWidget()
        if isinstance(page, VaultPage) and page.storage.is_unlocked():
            storage = page.storage
            groups_count = len(storage.list_groups())
            entries_count = len(storage.list_entries())
            self.setWindowTitle(
                f"SecPass :: {storage.name} | groups: {groups_count} | entries: {entries_count}"
            )
        else:
            self.setWindowTitle("SecPass")

    # --- вход / создание ---

    def _on_browse_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Vault Folder")
        if folder:
            self.vault_path_input.setText(folder)

    def _on_keyfile_toggled(self, checked):
        self.keyfile_input.setEnabled(checked)
        self.keyfile_btn.setEnabled(checked)

    def _on_browse_keyfile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Key File", "", "All Files (*)")
        if file:
            self.keyfile_input.setText(file)

    def _on_new_vault(self):
        dialog = VaultCreationDialog(self)
        if not dialog.exec():
            return
        data = dialog.get_data()
        vault = Storage(data["path"])
        try:
            vault.create(data["password"], data.get("keyfile"), data.get("name"))
        except VaultExistsError:
            QMessageBox.warning(
                self,
                "Vault Exists",
                "A vault already exists at this location. Existing vaults are never overwritten.",
            )
            return
        except KeyfileError as e:
            QMessageBox.warning(self, "Key File Error", str(e))
            return
        except StorageError as e:
            QMessageBox.critical(self, "Error", f"Failed to create vault: {e}")
            return

        self.vault_path_input.clear()
        self.keyfile_input.clear()
        self.password_input.setFocus()
        QMessageBox.information(
            self, "Success", f"Vault created at: {data['path']}\nNow unlock it."
        )

    def _on_unlock(self):
        vault_path = Path(self.vault_path_input.text())
        keyfile_text = self.keyfile_input.text()
        keyfile = Path(keyfile_text) if keyfile_text else None

        vault = Storage(vault_path)
        try:
            vault.unlock(self.password_input.text(), keyfile)
        except VaultNotFoundError:
            self.status_label.setText("Vault does not exist. Create it first.")
        except InvalidPasswordError:
            self.status_label.setText("Invalid password or key file.")
        except KeyfileError as e:
            self.status_label.setText(str(e))
        except TamperError:
            self.status_label.setText("Vault is corrupted or was tampered with.")
        except StorageError as e:
            self.status_label.setText(f"Failed to unlock: {e}")
        else:
            page = self._create_vault_page(vault)
            self.stack.setCurrentIndex(1)
            tab_index = self.tabs.addTab(page, vault.name)
            self.tabs.setCurrentIndex(tab_index)
            self.status_label.setText("")
            self.vault_path_input.clear()
            self.keyfile_input.clear()
            self._update_window_title()
        finally:
            self.password_input.clear()

    def _on_new_tab(self):
        self.stack.setCurrentIndex(0)
        self.vault_path_input.setFocus()
        self._update_window_title()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
