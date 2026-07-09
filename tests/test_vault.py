import pytest
from pathlib import Path
from secpass.vault import Vault
from secpass.crypto import CipherSuite


class TestVault:
    def test_vault_creation(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")

        assert vault_path.exists()
        assert (vault_path / "entries").exists()
        assert (vault_path / "groups").exists()
        assert (vault_path / "masterkey").exists()

    def test_vault_exists_false_for_new_path(self, temp_dir):
        vault_path = temp_dir / "nonexistent_vault"
        vault = Vault(vault_path)
        assert not vault.exists()

    def test_vault_exists_true_after_create(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        assert vault.exists()

    def test_unlock_vault(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")

        vault2 = Vault(vault_path)
        vault2.unlock(test_password)
        assert vault2.is_unlocked()

    def test_unlock_wrong_password_raises(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")

        vault2 = Vault(vault_path)
        with pytest.raises(Exception):
            vault2.unlock("wrong_password")

    def test_lock_vault(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)
        assert vault.is_unlocked()

        vault.lock()
        assert not vault.is_unlocked()

    def test_create_entry(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("Test Entry", "https://example.com")
        assert entry_uuid is not None

    def test_set_and_get_entry_body(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("Test Entry", "https://example.com")
        vault.set_entry_body(entry_uuid, "user@example.com", "secret_password")

        body = vault.get_entry_body(entry_uuid)
        assert body["username"] == "user@example.com"
        assert body["password"] == "secret_password"

    def test_get_entry_head(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("My Login", "https://google.com")
        head = vault.get_entry_head(entry_uuid)

        assert head["name"] == "My Login"
        assert head["url"] == "https://google.com"
        assert head["uuid"] == str(entry_uuid)

    def test_list_entries(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        vault.create_entry("Entry 1", "https://a.com")
        vault.create_entry("Entry 2", "https://b.com")

        entries = vault.list_entries()
        assert len(entries) == 2
        names = [e["name"] for e in entries]
        assert "Entry 1" in names
        assert "Entry 2" in names

    def test_create_group(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        group_uuid = vault.create_group("Work")
        assert group_uuid is not None

    def test_get_group(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        group_uuid = vault.create_group("Personal")
        group = vault.get_group(group_uuid)

        assert group["name"] == "Personal"
        assert group["uuid"] == str(group_uuid)

    def test_create_group_with_parent(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        parent_uuid = vault.create_group("Parent")
        child_uuid = vault.create_group("Child", parent_uuid)

        child = vault.get_group(child_uuid)
        assert child["parent"] == str(parent_uuid)

    def test_list_groups(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        vault.create_group("Group 1")
        vault.create_group("Group 2")

        groups = vault.list_groups()
        assert len(groups) == 2
        names = [g["name"] for g in groups]
        assert "Group 1" in names
        assert "Group 2" in names

    def test_entry_with_group(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        group_uuid = vault.create_group("Work")
        entry_uuid = vault.create_entry("Work Login", "https://work.com", group_uuid)

        head = vault.get_entry_head(entry_uuid)
        assert head["group"] == str(group_uuid)

    def test_vault_with_keyfile(self, temp_dir, test_password, keyfile):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, keyfile, name="test_vault")

        vault2 = Vault(vault_path)
        vault2.unlock(test_password, keyfile)
        assert vault2.is_unlocked()

    def test_vault_wrong_keyfile_fails(self, temp_dir, test_password, keyfile):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, keyfile, name="test_vault")

        other_keyfile = temp_dir / "other.key"
        other_keyfile.write_bytes(b"different_key_material")

        vault2 = Vault(vault_path)
        with pytest.raises(Exception):
            vault2.unlock(test_password, other_keyfile)

    def test_double_encryption_body(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("Test", "https://test.com")
        vault.set_entry_body(entry_uuid, "user", "password")

        body_file = vault.entries_path / f"{vault._hash_uuid(entry_uuid)}.body"
        encrypted_data = body_file.read_bytes()
        decrypted_once = CipherSuite.decrypt_aes_cbc(vault._derived_key, encrypted_data)
        with pytest.raises(Exception):
            json.loads(decrypted_once)

    def test_update_entry_head(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("Original", "https://original.com")
        vault.update_entry_head(entry_uuid, "Updated", "https://updated.com")

        head = vault.get_entry_head(entry_uuid)
        assert head["name"] == "Updated"
        assert head["url"] == "https://updated.com"

    def test_update_entry_with_email_notes(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("Test", "https://test.com")
        vault.set_entry_body(entry_uuid, "user", "pass", "test@example.com", "Some notes")

        body = vault.get_entry_body(entry_uuid)
        assert body["email"] == "test@example.com"
        assert body["notes"] == "Some notes"

    def test_delete_entry(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        entry_uuid = vault.create_entry("To Delete", "https://delete.com")
        vault.delete_entry(entry_uuid)

        head = vault.get_entry_head(entry_uuid)
        assert head is None

    def test_update_group(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        group_uuid = vault.create_group("Original Name")
        vault.update_group(group_uuid, "New Name")

        group = vault.get_group(group_uuid)
        assert group["name"] == "New Name"

    def test_delete_group(self, temp_dir, test_password):
        vault_path = temp_dir / "vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)

        group_uuid = vault.create_group("To Delete")
        vault.delete_group(group_uuid)

        group = vault.get_group(group_uuid)
        assert group is None


class TestDuplicateNames:
    @pytest.fixture
    def vault(self, temp_dir, test_password):
        from secpass.vault import Vault
        vault_path = temp_dir / "dup_vault"
        vault = Vault(vault_path)
        vault.create(test_password, name="test_vault")
        vault.unlock(test_password)
        return vault

    def test_create_duplicate_entry_raises(self, vault):
        vault.create_entry("Login")
        with pytest.raises(ValueError, match="already exists"):
            vault.create_entry("Login")

    def test_create_duplicate_group_raises(self, vault):
        vault.create_group("Email")
        with pytest.raises(ValueError, match="already exists"):
            vault.create_group("Email")

    def test_create_different_names_allowed(self, vault):
        uuid1 = vault.create_entry("Entry1")
        uuid2 = vault.create_entry("Entry2")
        assert uuid1 != uuid2
        assert len(vault.list_entries()) == 2

    def test_update_entry_same_name_allowed(self, vault):
        entry_uuid = vault.create_entry("MyEntry")
        vault.update_entry_head(entry_uuid, "MyEntry", "")
        head = vault.get_entry_head(entry_uuid)
        assert head["name"] == "MyEntry"

    def test_update_entry_to_existing_name_raises(self, vault):
        vault.create_entry("Existing")
        entry_uuid = vault.create_entry("Other")
        with pytest.raises(ValueError, match="already exists"):
            vault.update_entry_head(entry_uuid, "Existing", "")

    def test_update_group_same_name_allowed(self, vault):
        group_uuid = vault.create_group("MyGroup")
        vault.update_group(group_uuid, "MyGroup")
        group = vault.get_group(group_uuid)
        assert group["name"] == "MyGroup"

    def test_update_group_to_existing_name_raises(self, vault):
        vault.create_group("ExistingGroup")
        group_uuid = vault.create_group("OtherGroup")
        with pytest.raises(ValueError, match="already exists"):
            vault.update_group(group_uuid, "ExistingGroup")