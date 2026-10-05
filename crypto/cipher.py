import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


class CipherSuite:
    """Криптографические операции: вывод ключа (Argon2id)
    и аутентифицированное шифрование AES-256-GCM."""

    GCM_NONCE_SIZE = 12

    @staticmethod
    def derive_key(password: bytes, salt: bytes, memory: int = 65536, iterations: int = 3) -> bytes:
        """Argon2id (64 MiB, 3 итерации, 4 линии) → 32-байтовый ключ."""
        kdf = Argon2id(
            salt=salt,
            length=32,
            memory_cost=memory,
            iterations=iterations,
            lanes=4,
        )
        return kdf.derive(password)

    @staticmethod
    def encrypt_gcm(key: bytes, plaintext: bytes) -> bytes:
        """AES-256-GCM: возвращает nonce(12) + шифротекст + тег."""
        nonce = os.urandom(CipherSuite.GCM_NONCE_SIZE)
        return nonce + AESGCM(key).encrypt(nonce, plaintext, None)

    @staticmethod
    def decrypt_gcm(key: bytes, data: bytes) -> bytes:
        """AES-256-GCM: проверяет целостность, бросает InvalidTag при подделке."""
        if len(data) <= CipherSuite.GCM_NONCE_SIZE:
            raise ValueError("Invalid GCM payload")
        return AESGCM(key).decrypt(
            data[: CipherSuite.GCM_NONCE_SIZE],
            data[CipherSuite.GCM_NONCE_SIZE :],
            None,
        )

    @staticmethod
    def generate_master_key() -> bytes:
        return os.urandom(32)

    @staticmethod
    def generate_salt() -> bytes:
        return os.urandom(16)
