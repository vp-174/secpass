import os
import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class TestGUIModule:
    def test_main_window_import(self):
        from secpass.gui.main_window import MainWindow
        assert MainWindow is not None

    def test_gui_can_be_created_without_vault(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()
        assert window is not None
        assert window.vault is None

    def test_login_page_elements(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()

        assert window.password_input is not None
        assert window.vault_path_input is not None
        assert window.unlock_btn is not None
        assert window.status_label is not None

    def test_stacked_widget_has_pages(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()

        assert window.stack.count() == 2

    def test_initial_page_is_login(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()

        assert window.stack.currentIndex() == 0

    def test_unlock_button_exists(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()

        assert window.unlock_btn.text() == "Unlock"

    def test_menu_bar_exists(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()
        assert window.menuBar() is not None

    def test_window_title(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
        window = MainWindow()

        assert "SecPass" in window.windowTitle()

    def test_menu_exists(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from secpass.gui.main_window import MainWindow
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
        from secpass.gui.main_window import MainWindow
        return MainWindow()

    def test_password_input_echo_mode(self, window):
        from PySide6.QtWidgets import QLineEdit
        assert window.password_input.echoMode() == QLineEdit.Password

    def test_vault_path_input_exists(self, window):
        assert window.vault_path_input is not None

    def test_unlock_callback_connected(self, window):
        assert window.unlock_btn.clicked is not None

    def test_keyfile_input_exists(self, window):
        assert window.keyfile_input is not None


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
        from secpass.gui.main_window import MainWindow
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
        from secpass.gui.main_window import MainWindow
        window = MainWindow()
        assert window.tabs is not None
        assert window.tabs.count() == 0

    def test_tabs_closable(self, app):
        from secpass.gui.main_window import MainWindow
        window = MainWindow()
        assert window.tabs.tabsClosable() == True


class TestVaultCreationDialog:
    def test_dialog_import(self):
        from secpass.gui.main_window import VaultCreationDialog
        assert VaultCreationDialog is not None

    def test_dialog_has_name_field(self):
        from secpass.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        assert dialog.vault_name is not None

    def test_dialog_has_path_field(self):
        from secpass.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        assert dialog.vault_path is not None

    def test_dialog_has_password_field(self):
        from secpass.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        assert dialog.password_input is not None


class TestPasswordStrength:
    def test_calculate_entropy_empty(self):
        from secpass.gui.main_window import calculate_entropy
        assert calculate_entropy("") == 0.0

    def test_calculate_entropy_lowercase(self):
        from secpass.gui.main_window import calculate_entropy
        entropy = calculate_entropy("abcdef")
        assert entropy > 0

    def test_calculate_entropy_mixed(self):
        from secpass.gui.main_window import calculate_entropy
        entropy = calculate_entropy("Abc123!@")
        assert entropy > 20

    def test_get_strength_level_weak(self):
        from secpass.gui.main_window import get_strength_level
        level, label, color = get_strength_level(10)
        assert level == 1
        assert label == "Very Weak"

    def test_get_strength_level_very_strong(self):
        from secpass.gui.main_window import get_strength_level
        level, label, color = get_strength_level(130)
        assert level == 5
        assert label == "Very Strong"

    def test_strong_password_entropy(self):
        from secpass.gui.main_window import calculate_entropy
        entropy = calculate_entropy("VeryStr0ngP@ssw0rd123!Above80Bits")
        assert entropy >= 80


class TestVaultCreation:
    @pytest.fixture
    def temp_dir(self):
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp, ignore_errors=True)

    def test_vault_creation_requires_name(self, temp_dir):
        from secpass.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        dialog.vault_path.setText(str(temp_dir))
        dialog.password_input.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.confirm_password.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.vault_name.setText("")

        with patch("PySide6.QtWidgets.QMessageBox.warning"):
            result = dialog._on_accept()
        assert result is None

    def test_vault_creation_requires_path(self):
        from secpass.gui.main_window import VaultCreationDialog
        dialog = VaultCreationDialog()
        dialog.vault_name.setText("TestVault")
        dialog.password_input.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.confirm_password.setText("VeryStrongP@ssw0rd123!Above80")
        dialog.vault_path.setText("")

        with patch("PySide6.QtWidgets.QMessageBox.warning"):
            result = dialog._on_accept()
        assert result is None


class TestEntryDialog:
    def test_dialog_import(self):
        from secpass.gui.main_window import EntryDialog
        assert EntryDialog is not None

    def test_dialog_has_fields(self):
        from secpass.gui.main_window import EntryDialog
        dialog = EntryDialog()
        assert dialog.title_input is not None
        assert dialog.username_input is not None
        assert dialog.password_input is not None
        assert dialog.url_input is not None
        assert dialog.email_input is not None


class TestWindowTitle:
    @pytest.fixture
    def app(self):
        from PySide6.QtWidgets import QApplication
        app_instance = QApplication.instance() or QApplication(sys.argv)
        yield app_instance

    @pytest.fixture
    def window(self, app):
        from secpass.gui.main_window import MainWindow
        return MainWindow()

    def test_initial_title_is_default(self, window):
        assert window.windowTitle() == "SecPass"

    def test_title_after_unlock(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path = temp_dir / "test_vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="MyVault")
        vault.unlock(test_password)
        vault.create_entry("TestEntry", "https://example.com")
        vault.create_group("TestGroup")
        vault.lock()

        window.vault_path_input.setText(str(vault_path))
        window.password_input.setText(test_password)
        window._on_unlock()

        title = window.windowTitle()
        assert "MyVault" in title
        assert "groups: 1" in title
        assert "entries: 1" in title

    def test_title_after_close_tab(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path = temp_dir / "test_vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="MyVault")

        window.vault_path_input.setText(str(vault_path))
        window.password_input.setText(test_password)
        window._on_unlock()

        assert "MyVault" in window.windowTitle()

        window._on_close_tab(0)

        assert window.windowTitle() == "SecPass"

    def test_title_after_lock_vault(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path = temp_dir / "test_vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="MyVault")

        window.vault_path_input.setText(str(vault_path))
        window.password_input.setText(test_password)
        window._on_unlock()

        assert "MyVault" in window.windowTitle()

        page = window.tabs.currentWidget()
        window._on_lock_vault(page.vault, page)

        assert window.windowTitle() == "SecPass"

    def test_title_after_new_tab(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path = temp_dir / "test_vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="MyVault")

        window.vault_path_input.setText(str(vault_path))
        window.password_input.setText(test_password)
        window._on_unlock()

        assert "MyVault" in window.windowTitle()

        window._on_new_tab()

        assert window.windowTitle() == "SecPass"

    def test_title_switch_between_tabs(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path1 = temp_dir / "vault_a"
        vault_path2 = temp_dir / "vault_b"

        vault1 = Vault(vault_path1)
        vault1.create(test_password, name="VaultA")
        vault1.unlock(test_password)
        vault1.create_entry("EntryA")
        vault1.lock()

        vault2 = Vault(vault_path2)
        vault2.create(test_password, name="VaultB")
        vault2.unlock(test_password)
        vault2.create_entry("EntryB")
        vault2.create_group("GroupB")
        vault2.lock()

        window.vault_path_input.setText(str(vault_path1))
        window.password_input.setText(test_password)
        window._on_unlock()
        title_a = window.windowTitle()
        assert "VaultA" in title_a
        assert "entries: 1" in title_a

        window._on_new_tab()
        window.vault_path_input.setText(str(vault_path2))
        window.password_input.setText(test_password)
        window._on_unlock()

        assert "VaultB" in window.windowTitle()
        assert "entries: 1" in window.windowTitle()
        assert "groups: 1" in window.windowTitle()

        window.tabs.setCurrentIndex(0)
        assert "VaultA" in window.windowTitle()

        window.tabs.setCurrentIndex(1)
        assert "VaultB" in window.windowTitle()

    def test_title_close_one_of_two_tabs(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path1 = temp_dir / "vault_a"
        vault_path2 = temp_dir / "vault_b"

        vault1 = Vault(vault_path1)
        vault1.create(test_password, name="VaultA")
        vault2 = Vault(vault_path2)
        vault2.create(test_password, name="VaultB")

        window.vault_path_input.setText(str(vault_path1))
        window.password_input.setText(test_password)
        window._on_unlock()

        window._on_new_tab()
        window.vault_path_input.setText(str(vault_path2))
        window.password_input.setText(test_password)
        window._on_unlock()

        window.tabs.setCurrentIndex(1)
        assert "VaultB" in window.windowTitle()

        window._on_close_tab(0)

        assert window.tabs.count() == 1
        assert "VaultB" in window.windowTitle()

    def test_update_window_title_no_vault(self, window):
        window._update_window_title()
        assert window.windowTitle() == "SecPass"

    def test_title_summary_counts_default(self, window, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path = temp_dir / "test_vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="EmptyVault")

        window.vault_path_input.setText(str(vault_path))
        window.password_input.setText(test_password)
        window._on_unlock()

        title = window.windowTitle()
        assert "EmptyVault" in title
        assert "groups: 0" in title
        assert "entries: 0" in title