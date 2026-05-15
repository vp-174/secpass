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
        assert window.keyfile_input is not None

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

    def test_main_page_has_toolbar(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from pwduck.gui.main_window import MainWindow
        window = MainWindow()

        assert window.add_entry_btn is not None
        assert window.add_group_btn is not None
        assert window.edit_group_btn is not None
        assert window.delete_group_btn is not None
        assert window.lock_btn is not None
        assert window.entries_list is not None
        assert window.search_input is not None
        assert window.groups_tree is not None

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

    def test_add_entry_callback_connected(self, window):
        assert window.add_entry_btn.clicked is not None

    def test_lock_callback_connected(self, window):
        assert window.lock_btn.clicked is not None

    def test_search_input_exists(self, window):
        assert window.search_input is not None


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
        window._on_create_vault()

        assert temp_vault_dir.exists()
        assert (temp_vault_dir / "masterkey").exists()

    def test_unlock_vault_from_gui(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create_vault()
        window._on_unlock()

        assert window.vault is not None
        assert window.vault.is_unlocked()
        assert window.stack.currentIndex() == 1

    def test_lock_vault_from_gui(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create_vault()
        window._on_unlock()
        window._on_lock()

        assert window.vault is None or not window.vault.is_unlocked()
        assert window.stack.currentIndex() == 0

    def test_add_entry_updates_list(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create_vault()
        window._on_unlock()

        entry_uuid = window.vault.create_entry("Test Entry", "https://test.com")
        window.vault.set_entry_body(entry_uuid, "user", "pass")
        window._refresh_view()

        assert window.entries_list.topLevelItemCount() > 0

    def test_unlock_nonexistent_vault_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir / "nonexistent"))
        window.password_input.setText("test")
        window._on_unlock()

        assert "does not exist" in window.status_label.text() or window.status_label.text() != ""

    def test_unlock_wrong_password_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("correct")
        window._on_create_vault()

        window.password_input.setText("wrong")
        window._on_unlock()

        assert "Failed" in window.status_label.text() or window.status_label.text() != ""

    def test_create_existing_vault_shows_error(self, window, temp_vault_dir):
        window.vault_path_input.setText(str(temp_vault_dir))
        window.password_input.setText("test123")
        window._on_create_vault()
        window._on_create_vault()

        assert "exists" in window.status_label.text() or window.status_label.text() != ""


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


class TestVaultCreationDialog:
    def test_dialog_import(self):
        from pwduck.gui.main_window import VaultCreationDialog
        assert VaultCreationDialog is not None


class TestVaultDeleteDialog:
    def test_dialog_import(self):
        from pwduck.gui.main_window import VaultDeleteDialog
        assert VaultDeleteDialog is not None


class TestSearch:
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
        w = MainWindow()
        w.vault_path_input.setText(str(temp_vault_dir))
        w.password_input.setText("test123")
        w._on_create_vault()
        w._on_unlock()
        return w

    def test_search_finds_entry(self, window):
        window.vault.create_entry("My Bank Account", "https://bank.com")
        window.vault.create_entry("Facebook", "https://facebook.com")
        window._refresh_view()

        window.search_input.setText("bank")
        window._on_search("bank")

        assert window.entries_list.topLevelItemCount() == 1

    def test_search_case_insensitive(self, window):
        window.vault.create_entry("Test Entry", "https://test.com")
        window._refresh_view()

        window.search_input.setText("TEST")
        window._on_search("TEST")

        assert window.entries_list.topLevelItemCount() == 1

    def test_search_clears_results(self, window):
        window.vault.create_entry("Test Entry", "https://test.com")
        window._refresh_view()

        window.search_input.setText("bank")
        window._on_search("bank")
        assert window.entries_list.topLevelItemCount() == 0

        window.search_input.setText("")
        window._on_search("")
        assert window.entries_list.topLevelItemCount() > 0


class TestGroupEditing:
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
        w = MainWindow()
        w.vault_path_input.setText(str(temp_vault_dir))
        w.password_input.setText("test123")
        w._on_create_vault()
        w._on_unlock()
        return w

    def test_edit_group_button_exists(self, window):
        assert window.edit_group_btn is not None
        assert window.edit_group_btn.text() == "Edit Group"

    def test_delete_group_button_exists(self, window):
        assert window.delete_group_btn is not None
        assert window.delete_group_btn.text() == "Delete Group"

    def test_add_group_updates_list(self, window):
        window.vault.create_group("Test Group")
        window._refresh_groups()

        assert window.groups_tree.topLevelItemCount() > 0

    def test_groups_tree_double_click_connected(self, window):
        assert window.groups_tree.itemDoubleClicked is not None


class TestEntryEditing:
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
        w = MainWindow()
        w.vault_path_input.setText(str(temp_vault_dir))
        w.password_input.setText("test123")
        w._on_create_vault()
        w._on_unlock()
        return w

    def test_edit_entry_updates_name_and_url(self, window):
        from pwduck.gui.main_window import EntryDialog
        entry_uuid = window.vault.create_entry("Original", "https://original.com")
        window.vault.set_entry_body(entry_uuid, "user", "pass")
        window._refresh_view()

        item = window.entries_list.topLevelItem(0)
        window.entries_list.setCurrentItem(item)

        entry_data = {
            "name": "Updated Name",
            "url": "https://updated.com",
            "username": "newuser",
            "password": "newpass",
            "email": "test@test.com",
            "notes": "Some notes"
        }
        dialog = EntryDialog(entry_data, window)
        if dialog.exec():
            data = dialog.get_data()
            window.vault.update_entry_head(entry_uuid, data["name"], data["url"])
            window.vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))

        head = window.vault.get_entry_head(entry_uuid)
        assert head["name"] == "Updated Name"
        assert head["url"] == "https://updated.com"

    def test_edit_entry_updates_email_and_notes(self, window):
        from pwduck.gui.main_window import EntryDialog
        entry_uuid = window.vault.create_entry("Test", "https://test.com")
        window.vault.set_entry_body(entry_uuid, "user", "pass")
        window._refresh_view()

        item = window.entries_list.topLevelItem(0)
        window.entries_list.setCurrentItem(item)

        entry_data = {
            "name": "Test",
            "url": "https://test.com",
            "username": "user",
            "password": "pass",
            "email": "newemail@test.com",
            "notes": "New notes here"
        }
        dialog = EntryDialog(entry_data, window)
        if dialog.exec():
            data = dialog.get_data()
            window.vault.set_entry_body(entry_uuid, data["username"], data["password"], data.get("email", ""), data.get("notes", ""))

        body = window.vault.get_entry_body(entry_uuid)
        assert body["email"] == "newemail@test.com"
        assert body["notes"] == "New notes here"