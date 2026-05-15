import os
import json
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

from secpass.crypto import CipherSuite
from secpass.secure import SecureString


class Vault:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.entries_path = self.path / "entries"
        self.groups_path = self.path / "groups"
        self.masterkey_path = self.path / "masterkey"
        self._master_key: Optional[SecureString] = None
        self._name: Optional[str] = None
        self._derived_key: Optional[bytes] = None

    def exists(self) -> bool:
        return self.path.exists() and self.masterkey_path.exists()

    @property
    def name(self) -> str:
        if self._name:
            return self._name
        return self.path.name

    def create(self, password: str, keyfile: Optional[Path] = None, name: Optional[str] = None):
        self.path.mkdir(parents=True, exist_ok=True)
        self.entries_path.mkdir(exist_ok=True)
        self.groups_path.mkdir(exist_ok=True)

        self._name = name if name else self.path.name

        salt = CipherSuite.generate_salt()
        if keyfile and keyfile.exists():
            keyfile_data = keyfile.read_bytes()
            password_bytes = password.encode() + keyfile_data
        else:
            password_bytes = password.encode()

        self._master_key = SecureString(CipherSuite.generate_master_key())
        derived_key = CipherSuite.derive_key(password_bytes, salt)

        vault_data = json.dumps({"name": self._name}).encode()
        encrypted_master = CipherSuite.encrypt_aes_cbc(derived_key, vault_data + b"|" + self._master_key.get())
        self.masterkey_path.write_bytes(salt + b"::" + encrypted_master)
        self._derived_key = derived_key

    def unlock(self, password: str, keyfile: Optional[Path] = None):
        data = self.masterkey_path.read_bytes()
        salt, encrypted_master = data.split(b"::")

        if keyfile and keyfile.exists():
            keyfile_data = keyfile.read_bytes()
            password_bytes = password.encode() + keyfile_data
        else:
            password_bytes = password.encode()

        derived_key = CipherSuite.derive_key(password_bytes, salt)
        decrypted = CipherSuite.decrypt_aes_cbc(derived_key, encrypted_master)

        try:
            vault_data_raw, master_key = decrypted.split(b"|")
            vault_data = json.loads(vault_data_raw)
            self._name = vault_data.get("name", self.path.name)
        except ValueError:
            self._name = self.path.name
            master_key = decrypted

        self._master_key = SecureString(master_key)
        self._derived_key = derived_key

    def lock(self):
        if self._master_key:
            self._master_key.zeroize()
            self._master_key = None

    def is_unlocked(self) -> bool:
        return self._master_key is not None

    def _hash_uuid(self, entry_uuid: uuid.UUID) -> str:
        return hashlib.sha256(str(entry_uuid).encode()).hexdigest()

    def create_entry(self, name: str, url: str = "", group_uuid: Optional[uuid.UUID] = None) -> uuid.UUID:
        entry_uuid = uuid.uuid4()
        head = {
            "uuid": str(entry_uuid),
            "name": name,
            "url": url,
            "group": str(group_uuid) if group_uuid else None
        }
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        encrypted_head = CipherSuite.encrypt_aes_cbc(self._derived_key, json.dumps(head).encode())
        head_filename.write_bytes(encrypted_head)
        return entry_uuid

    def set_entry_body(self, entry_uuid: uuid.UUID, username: str, password: str, email: str = "", notes: str = ""):
        body = {"username": username, "password": password, "email": email, "notes": notes}
        body_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.body"
        inner_encrypted = CipherSuite.encrypt_aes_cbc(self._derived_key, json.dumps(body).encode())
        outer_encrypted = CipherSuite.encrypt_aes_cbc(self._derived_key, inner_encrypted)
        body_filename.write_bytes(outer_encrypted)

    def update_entry_head(self, entry_uuid: uuid.UUID, name: str, url: str, group_uuid: Optional[uuid.UUID] = None):
        head = self.get_entry_head(entry_uuid)
        if not head:
            return
        head["name"] = name
        head["url"] = url
        if group_uuid is not None:
            head["group"] = str(group_uuid)
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        encrypted_head = CipherSuite.encrypt_aes_cbc(self._derived_key, json.dumps(head).encode())
        head_filename.write_bytes(encrypted_head)

    def delete_entry(self, entry_uuid: uuid.UUID):
        head_file = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        body_file = self.entries_path / f"{self._hash_uuid(entry_uuid)}.body"
        if head_file.exists():
            head_file.unlink()
        if body_file.exists():
            body_file.unlink()

    def update_group(self, group_uuid: uuid.UUID, name: str, parent_uuid: Optional[uuid.UUID] = None):
        group = self.get_group(group_uuid)
        if not group:
            return
        group["name"] = name
        if parent_uuid is not None:
            group["parent"] = str(parent_uuid)
        group_filename = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        encrypted_group = CipherSuite.encrypt_aes_cbc(self._derived_key, json.dumps(group).encode())
        group_filename.write_bytes(encrypted_group)

    def delete_group(self, group_uuid: uuid.UUID):
        group_file = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        if group_file.exists():
            group_file.unlink()

    def get_entry_head(self, entry_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        if not head_filename.exists():
            return None
        encrypted = head_filename.read_bytes()
        decrypted = CipherSuite.decrypt_aes_cbc(self._derived_key, encrypted)
        return json.loads(decrypted)

    def get_entry_body(self, entry_uuid: uuid.UUID) -> Optional[Dict[str, str]]:
        body_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.body"
        if not body_filename.exists():
            return None
        encrypted = body_filename.read_bytes()
        outer_decrypted = CipherSuite.decrypt_aes_cbc(self._derived_key, encrypted)
        inner_decrypted = CipherSuite.decrypt_aes_cbc(self._derived_key, outer_decrypted)
        return json.loads(inner_decrypted)

    def list_entries(self) -> list[Dict[str, Any]]:
        entries = []
        for head_file in self.entries_path.glob("*.head"):
            head = self.get_entry_head_from_file(head_file)
            if head:
                entries.append(head)
        return entries

    def get_entry_head_from_file(self, head_file: Path) -> Optional[Dict[str, Any]]:
        encrypted = head_file.read_bytes()
        try:
            decrypted = CipherSuite.decrypt_aes_cbc(self._derived_key, encrypted)
            return json.loads(decrypted)
        except Exception:
            return None

    def create_group(self, name: str, parent_uuid: Optional[uuid.UUID] = None) -> uuid.UUID:
        group_uuid = uuid.uuid4()
        group = {
            "uuid": str(group_uuid),
            "name": name,
            "parent": str(parent_uuid) if parent_uuid else None
        }
        group_filename = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        encrypted_group = CipherSuite.encrypt_aes_cbc(self._derived_key, json.dumps(group).encode())
        group_filename.write_bytes(encrypted_group)
        return group_uuid

    def get_group(self, group_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        group_filename = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        if not group_filename.exists():
            return None
        encrypted = group_filename.read_bytes()
        decrypted = CipherSuite.decrypt_aes_cbc(self._derived_key, encrypted)
        return json.loads(decrypted)

    def list_groups(self) -> list[Dict[str, Any]]:
        groups = []
        for group_file in self.groups_path.glob("*.group"):
            encrypted = group_file.read_bytes()
            try:
                decrypted = CipherSuite.decrypt_aes_cbc(self._derived_key, encrypted)
                groups.append(json.loads(decrypted))
            except Exception:
                continue
        return groups