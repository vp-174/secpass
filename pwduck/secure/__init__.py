import os
import ctypes
import ctypes.wintypes
from typing import Optional


class SecureString:
    _locked_memory: bytearray = bytearray()

    def __init__(self, data: bytes = b""):
        self._data = bytearray(data)
        self._lock_memory()

    def _lock_memory(self):
        try:
            mlock = ctypes.cdll.msvcrt.mlock
            mlock(ctypes.addressof(self._data), len(self._data))
        except Exception:
            pass

    def _unlock_memory(self):
        try:
            munlock = ctypes.cdll.msvcrt.munlock
            munlock(ctypes.addressof(self._data), len(self._data))
        except Exception:
            pass

    def __del__(self):
        self.zeroize()

    def zeroize(self):
        for i in range(len(self._data)):
            self._data[i] = 0
        self._unlock_memory()

    def get(self) -> bytes:
        return bytes(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __str__(self) -> str:
        return self.get().decode("utf-8", errors="replace")

    def __repr__(self) -> str:
        return f"<SecureString length={len(self._data)}>"


def encrypt_master_key_protected(master_key: bytes, protection_key: bytes) -> bytes:
    from pwduck.crypto import CipherSuite
    return CipherSuite.encrypt_chacha20(protection_key, master_key)


def decrypt_master_key_protected(encrypted_key: bytes, protection_key: bytes) -> bytes:
    from pwduck.crypto import CipherSuite
    return CipherSuite.decrypt_chacha20(protection_key, encrypted_key)