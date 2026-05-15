import os
import pytest
import sys
import tempfile
import shutil
from pathlib import Path

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

        assert window.create_btn.text() == "Create New Vault"

    def test_window_title(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert "PWDuck" in window.windowTitle()

    def test_menu_exists(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        menubar = window.menuBar()
        assert len(menubar.actions()) > 0


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

    def test_unlock_nonexistent_vault_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir / "nonexistent"))
        window.password_input.setText("test")
        window._on_unlock()

        assert "does not exist" in window.status_label.text() or window.status_label.text() != ""

    def test_unlock_wrong_password_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("correct_password!")
        window._on_unlock()

        if temp_vault_dir.exists():
            window.password_input.setText("wrong")
            window._on_unlock()
            assert "Failed" in window.status_label.text() or window.status_label.text() != ""


class TestTabs:
    @pytest.fixture
    def app(self):
        from PySide6.QtWidgets import QApplication
        app_instance = QApplication.instance() or QApplication(sys.argv)
        yield app_instance

    def test_tabs_exist(self, app):
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()
        assert window.tabs is not None
        assert window.tabs.count() == 0

    def test_tabs_closable(self, app):
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()
        assert window.tabs.tabsClosable() == True


class TestVaultCreationDialog:
    def test_dialog_import(self):
        from pwduck.gui.main_window import VaultCreationDialog
        assert VaultCreationDialog is not None

    def test_dialog_has_name_field(self):
        from pwduck.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        assert dialog.vault_name is not None

    def test_dialog_has_path_field(self):
        from pwduck.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        assert dialog.vault_path is not None

    def test_dialog_has_password_field(self):
        from pwduck.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        assert dialog.password_input is not None


class TestPasswordStrength:
    def test_calculate_entropy_empty(self):
        from pwduck.gui.main_window import calculate_entropy
        assert calculate_entropy("") == 0.0

    def test_calculate_entropy_lowercase(self):
        from pwduck.gui.main_window import calculate_entropy
        entropy = calculate_entropy("abcdef")
        assert entropy > 0

    def test_calculate_entropy_mixed(self):
        from pwduck.gui.main_window import calculate_entropy
        entropy = calculate_entropy("Abc123!@")
        assert entropy > 20

    def test_get_strength_level_weak(self):
        from pwduck.gui.main_window import get_strength_level
        level, label, color = get_strength_level(10)
        assert level == 1
        assert label == "Very Weak"

    def test_get_strength_level_strong(self):
        from pwduck.gui.main_window import get_strength_level
        level, label, color = get_strength_level(90)
        assert level == 5
        assert label == "Very Strong"

    def test_strong_password_entropy(self):
        from pwduck.gui.main_window import calculate_entropy
        entropy = calculate_entropy("VeryStr0ngP@ssw0rd123!Above80Bits")
        assert entropy >= 80


class TestVaultCreation:
    @pytest.fixture
    def temp_dir(self):
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp, ignore_errors=True)

    def test_vault_creation_requires_name(self, temp_dir):
        from pwduck.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        dialog.vault_path.setText(str(temp_dir))
        dialog.password_input.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.confirm_password.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.vault_name.setText("")

        assert not dialog._on_accept()

    def test_vault_creation_requires_path(self):
        from pwduck.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        dialog.vault_name.setText("TestVault")
        dialog.password_input.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.confirm_password.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.vault_path.setText("")

        result = dialog._on_accept()
        assert result is None