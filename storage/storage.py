import base64
import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.exceptions import InvalidTag

from crypto import CipherSuite
from log import get_logger
from secure import SecureString
from storage.errors import (
    DuplicateNameError,
    GroupNotEmptyError,
    InvalidPasswordError,
    KeyfileError,
    TamperError,
    VaultExistsError,
    VaultLockedError,
    VaultNotFoundError,
)

logger = get_logger("storage")

MAGIC = b"SPV2"
SALT_SIZE = 16
MAX_KEYFILE_SIZE = 16 * 1024 * 1024


def _atomic_write(path: Path, data: bytes) -> None:
    """Атомарная запись: temp-файл, fsync, подмена, права владельца."""
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _zeroize(buf: bytearray) -> None:
    for i in range(len(buf)):
        buf[i] = 0


class Storage:
    """Хранилище паролей: создание, открытие, блокировка, CRUD записей и групп.

    Формат v2: все данные шифруются AES-256-GCM мастер-ключом, который
    обёрнут ключом из Argon2id. Имена файлов — SHA256(UUID)."""

    def __init__(self, path):
        self.path = Path(path)
        self.entries_path = self.path / "entries"
        self.groups_path = self.path / "groups"
        self.masterkey_path = self.path / "masterkey"
        self._master_key: Optional[SecureString] = None
        self._name: Optional[str] = None

    @property
    def name(self) -> str:
        return self._name or self.path.name

    def is_unlocked(self) -> bool:
        return self._master_key is not None

    def _require_unlocked(self) -> None:
        if self._master_key is None:
            raise VaultLockedError("Vault is locked")

    @staticmethod
    def _read_keyfile(keyfile) -> bytes:
        keyfile = Path(keyfile)
        if not keyfile.exists():
            raise KeyfileError(f"Key file not found: {keyfile}")
        if keyfile.stat().st_size > MAX_KEYFILE_SIZE:
            raise KeyfileError("Key file is too large")
        return keyfile.read_bytes()

    @staticmethod
    def _mix_password(password: str, keyfile) -> tuple:
        """Пароль + SHA256 содержимого ключ-файла (доменное разделение)."""
        if keyfile is not None:
            data = Storage._read_keyfile(keyfile)
            return password.encode() + b"\x1f" + hashlib.sha256(data).digest(), True
        return password.encode(), False

    def create(self, password: str, keyfile=None, name: Optional[str] = None) -> None:
        if self.masterkey_path.exists():
            raise VaultExistsError(f"Vault already exists at {self.path}")

        password_bytes, kf_used = self._mix_password(password, keyfile)

        self.path.mkdir(parents=True, exist_ok=True)
        self.entries_path.mkdir(exist_ok=True)
        self.groups_path.mkdir(exist_ok=True)
        self._name = name if name else self.path.name

        salt = CipherSuite.generate_salt()
        kek = bytearray(CipherSuite.derive_key(password_bytes, salt))
        master_key = CipherSuite.generate_master_key()

        payload = json.dumps(
            {
                "name": self._name,
                "key": base64.b64encode(master_key).decode("ascii"),
            }
        ).encode()
        blob = CipherSuite.encrypt_gcm(kek, payload)
        kf_flag = bytes([1 if kf_used else 0])
        _atomic_write(self.masterkey_path, MAGIC + kf_flag + salt + blob)

        _zeroize(kek)
        self._master_key = SecureString(master_key)

    def unlock(self, password: str, keyfile=None) -> None:
        if not self.masterkey_path.exists():
            raise VaultNotFoundError(f"Vault does not exist at {self.path}")

        raw = self.masterkey_path.read_bytes()
        if not raw.startswith(MAGIC):
            raise InvalidPasswordError("Unrecognized vault format")

        self._unlock_v2(password, keyfile, raw)

    def _unlock_v2(self, password: str, keyfile, raw: bytes) -> None:
        if len(raw) <= len(MAGIC) + 1 + SALT_SIZE:
            raise InvalidPasswordError("Corrupted vault master key")

        kf_flag = raw[len(MAGIC)]
        salt = raw[len(MAGIC) + 1 : len(MAGIC) + 1 + SALT_SIZE]
        blob = raw[len(MAGIC) + 1 + SALT_SIZE :]

        if kf_flag and keyfile is None:
            raise KeyfileError("This vault requires a key file")
        if not kf_flag and keyfile is not None:
            raise KeyfileError("This vault does not use a key file")

        password_bytes, _ = self._mix_password(password, keyfile)
        kek = bytearray(CipherSuite.derive_key(password_bytes, salt))
        try:
            try:
                payload = json.loads(CipherSuite.decrypt_gcm(kek, blob))
            except (InvalidTag, ValueError, json.JSONDecodeError):
                raise InvalidPasswordError("Invalid password or key file")

            self._name = payload.get("name", self.path.name)
            try:
                master_key = base64.b64decode(payload["key"])
            except Exception:
                raise InvalidPasswordError("Corrupted vault master key")
            if len(master_key) != 32:
                raise InvalidPasswordError("Corrupted vault master key")
        finally:
            _zeroize(kek)

        self._master_key = SecureString(master_key)

    def lock(self) -> None:
        if self._master_key is not None:
            self._master_key.zeroize()
            self._master_key = None

    def _encrypt(self, plaintext: bytes) -> bytes:
        self._require_unlocked()
        return CipherSuite.encrypt_gcm(self._master_key.get(), plaintext)

    def _decrypt(self, data: bytes) -> bytes:
        self._require_unlocked()
        try:
            return CipherSuite.decrypt_gcm(self._master_key.get(), data)
        except InvalidTag:
            raise TamperError("Data integrity check failed")

    def _hash_uuid(self, entry_uuid: uuid.UUID) -> str:
        return hashlib.sha256(str(entry_uuid).encode()).hexdigest()

    def create_entry(self, name: str, url: str = "", group_uuid: Optional[uuid.UUID] = None) -> uuid.UUID:
        self._require_unlocked()
        if any(e.get("name") == name for e in self.list_entries()):
            raise DuplicateNameError(f"Entry with name '{name}' already exists")

        entry_uuid = uuid.uuid4()
        head = {
            "uuid": str(entry_uuid),
            "name": name,
            "url": url,
            "group": str(group_uuid) if group_uuid else None,
        }
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        _atomic_write(head_filename, self._encrypt(json.dumps(head).encode()))
        return entry_uuid

    def set_entry_body(self, entry_uuid: uuid.UUID, username: str, password: str, email: str = "", notes: str = ""):
        self._require_unlocked()
        body = {"username": username, "password": password, "email": email, "notes": notes}
        body_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.body"
        _atomic_write(body_filename, self._encrypt(json.dumps(body).encode()))

    def update_entry_head(self, entry_uuid: uuid.UUID, name: str, url: str, group_uuid: Optional[uuid.UUID] = None):
        self._require_unlocked()
        if any(e.get("name") == name and e.get("uuid") != str(entry_uuid) for e in self.list_entries()):
            raise DuplicateNameError(f"Entry with name '{name}' already exists")

        head = self.get_entry_head(entry_uuid)
        if not head:
            return
        head["name"] = name
        head["url"] = url
        if group_uuid is not None:
            head["group"] = str(group_uuid)
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        _atomic_write(head_filename, self._encrypt(json.dumps(head).encode()))

    def move_entry(self, entry_uuid: uuid.UUID, group_uuid: Optional[uuid.UUID] = None):
        self._require_unlocked()
        head = self.get_entry_head(entry_uuid)
        if not head:
            return
        if group_uuid is not None:
            head["group"] = str(group_uuid)
        else:
            head.pop("group", None)
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        _atomic_write(head_filename, self._encrypt(json.dumps(head).encode()))

    def delete_entry(self, entry_uuid: uuid.UUID):
        self._require_unlocked()
        head_file = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        body_file = self.entries_path / f"{self._hash_uuid(entry_uuid)}.body"
        if head_file.exists():
            head_file.unlink()
        if body_file.exists():
            body_file.unlink()

    def update_group(self, group_uuid: uuid.UUID, name: str, parent_uuid: Optional[uuid.UUID] = None):
        self._require_unlocked()
        if any(g.get("name") == name and g.get("uuid") != str(group_uuid) for g in self.list_groups()):
            raise DuplicateNameError(f"Group with name '{name}' already exists")

        group = self.get_group(group_uuid)
        if not group:
            return
        group["name"] = name
        if parent_uuid is not None:
            group["parent"] = str(parent_uuid)
        group_filename = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        _atomic_write(group_filename, self._encrypt(json.dumps(group).encode()))

    def delete_group(self, group_uuid: uuid.UUID):
        self._require_unlocked()
        gid = str(group_uuid)
        if any(e.get("group") == gid for e in self.list_entries()):
            raise GroupNotEmptyError("Group contains entries; move or delete them first")
        if any(g.get("parent") == gid for g in self.list_groups()):
            raise GroupNotEmptyError("Group contains subgroups; delete them first")
        group_file = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        if group_file.exists():
            group_file.unlink()

    def get_entry_head(self, entry_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        self._require_unlocked()
        head_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.head"
        if not head_filename.exists():
            return None
        decrypted = self._decrypt(head_filename.read_bytes())
        return json.loads(decrypted)

    def get_entry_body(self, entry_uuid: uuid.UUID) -> Optional[Dict[str, str]]:
        self._require_unlocked()
        body_filename = self.entries_path / f"{self._hash_uuid(entry_uuid)}.body"
        if not body_filename.exists():
            return None
        decrypted = self._decrypt(body_filename.read_bytes())
        return json.loads(decrypted)

    def list_entries(self) -> list:
        self._require_unlocked()
        entries = []
        for head_file in sorted(self.entries_path.glob("*.head")):
            head = self.get_entry_head_from_file(head_file)
            if head:
                entries.append(head)
        entries.sort(key=lambda e: e.get("name", "").lower())
        return entries

    def get_entry_head_from_file(self, head_file: Path) -> Optional[Dict[str, Any]]:
        encrypted = head_file.read_bytes()
        try:
            decrypted = self._decrypt(encrypted)
            return json.loads(decrypted)
        except (TamperError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to decrypt/parse entry head {head_file.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading entry head {head_file.name}: {e}")
            return None

    def create_group(self, name: str, parent_uuid: Optional[uuid.UUID] = None) -> uuid.UUID:
        self._require_unlocked()
        if any(g.get("name") == name for g in self.list_groups()):
            raise DuplicateNameError(f"Group with name '{name}' already exists")

        group_uuid = uuid.uuid4()
        group = {
            "uuid": str(group_uuid),
            "name": name,
            "parent": str(parent_uuid) if parent_uuid else None,
        }
        group_filename = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        _atomic_write(group_filename, self._encrypt(json.dumps(group).encode()))
        return group_uuid

    def get_group(self, group_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        self._require_unlocked()
        group_filename = self.groups_path / f"{self._hash_uuid(group_uuid)}.group"
        if not group_filename.exists():
            return None
        decrypted = self._decrypt(group_filename.read_bytes())
        return json.loads(decrypted)

    def list_groups(self) -> list:
        self._require_unlocked()
        groups = []
        for group_file in sorted(self.groups_path.glob("*.group")):
            encrypted = group_file.read_bytes()
            try:
                decrypted = self._decrypt(encrypted)
                groups.append(json.loads(decrypted))
            except (TamperError, ValueError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to decrypt/parse group {group_file.name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error reading group {group_file.name}: {e}")
        groups.sort(key=lambda g: g.get("name", "").lower())
        return groups
