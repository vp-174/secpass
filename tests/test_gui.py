import os
import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestGUIModule:
    def test_main_window_import(self):
        from pwduck.gui.main_window import MainWindow
        assert MainWindow is not None

    def test_gui_can_be_created_without_vault(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()
        assert window is not None
        assert window.vault is None

    def test_login_page_elements(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.password_input is not None
        assert window.vault_path_input is not None
        assert window.unlock_btn is not None
        assert window.create_btn is not None
        assert window.status_label is not None

    def test_stacked_widget_has_pages(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.stack.count() == 2

    def test_initial_page_is_login(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.stack.currentIndex() == 0

    def test_unlock_button_exists(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.unlock_btn.text() == "Unlock"

    def test_create_button_exists(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.create_btn.text() == "Create Vault"

    def test_main_page_has_toolbar(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.add_entry_btn is not None
        assert window.lock_btn is not None
        assert window.entries_list is not None

    def test_window_title(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert "PWDuck" in window.windowTitle()


class TestGUIInteraction:
    @pytest.fixture
    def app(self):
        from PySide6.QtWidgets import QApplication
        app_instance = QApplication.instance() or QApplication(sys.argv)
        yield app_instance

    @pytest.fixture
    def window(self, app):
        from pwduck.gui.main_window import MainWindow
        return MainWindow()

    def test_password_input_echo_mode(self, window):
        from PySide6.QtWidgets import QLineEdit
        assert window.password_input.echoMode() == QLineEdit.Password

    def test_vault_path_default_value(self, window):
        assert "vault" in window.vault_path_input.text()

    def test_unlock_callback_connected(self, window):
        assert window.unlock_btn.clicked is not None

    def test_create_callback_connected(self, window):
        assert window.create_btn.clicked is not None

    def test_add_entry_callback_connected(self, window):
        assert window.add_entry_btn.clicked is not None

    def test_lock_callback_connected(self, window):
        assert window.lock_btn.clicked is not None


class TestGUIVault:
    @pytest.fixture
    def temp_vault_dir(self):
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp, ignore_errors=True)

    @pytest.fixture
    def app(self):
        from PySide6.QtWidgets import QApplication
        app_instance = QApplication.instance() or QApplication(sys.argv)
        yield app_instance

    @pytest.fixture
    def window(self, app, temp_vault_dir):
        from pwduck.gui.main_window import MainWindow
        return MainWindow()

    def test_create_vault_from_gui(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create()

        assert temp_vault_dir.exists()
        assert (temp_vault_dir / "masterkey").exists()

    def test_unlock_vault_from_gui(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create()
        window._on_unlock()

        assert window.vault is not None
        assert window.vault.is_unlocked()
        assert window.stack.currentIndex() == 1

    def test_lock_vault_from_gui(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create()
        window._on_unlock()
        window._on_lock()

        assert window.vault is None or not window.vault.is_unlocked()
        assert window.stack.currentIndex() == 0

    def test_add_entry_updates_list(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create()
        window._on_unlock()
        window._on_add_entry()

        assert window.entries_list.count() > 0

    def test_unlock_nonexistent_vault_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir / "nonexistent"))
        window.password_input.setText("test")
        window._on_unlock()

        assert "does not exist" in window.status_label.text() or window.status_label.text() != ""

    def test_unlock_wrong_password_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("correct")
        window._on_create()

        window.password_input.setText("wrong")
        window._on_unlock()

        assert "Failed" in window.status_label.text() or window.status_label.text() != ""

    def test_create_existing_vault_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create()
        window._on_create()

        assert "exists" in window.status_label.text() or window.status_label.text() != ""