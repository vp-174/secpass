import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.backends import default_backend


class CipherSuite:
    """Набор криптографических операций: вывод ключа, шифрование AES-256-CBC и ChaCha20."""

    @staticmethod
    def derive_key(password: bytes, salt: bytes, memory: int = 65536, iterations: int = 3) -> bytes:
        kdf = Argon2id(
            salt=salt,
            length=32,
            memory_cost=memory,
            iterations=iterations,
            lanes=4,
        )
        return kdf.derive(password)

    @staticmethod
    def encrypt_aes_cbc(key: bytes, plaintext: bytes) -> bytes:
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padding = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([padding] * padding)
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext)

    @staticmethod
    def decrypt_aes_cbc(key: bytes, ciphertext: bytes) -> bytes:
        data = base64.b64decode(ciphertext)
        iv = data[:16]
        ct = data[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ct) + decryptor.finalize()
        padding = padded[-1]
        if not (1 <= padding <= 16):
            raise ValueError("Invalid padding")
        for i in range(padding):
            if padded[-(i+1)] != padding:
                raise ValueError("Invalid padding bytes")
        return padded[:-padding]

    @staticmethod
    def encrypt_chacha20(key: bytes, plaintext: bytes) -> bytes:
        nonce = os.urandom(16)
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext)
        return base64.b64encode(nonce + ciphertext)

    @staticmethod
    def decrypt_chacha20(key: bytes, ciphertext: bytes) -> bytes:
        data = base64.b64decode(ciphertext)
        nonce = data[:16]
        ct = data[16:]
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct)

    @staticmethod
    def generate_master_key() -> bytes:
        return os.urandom(32)

    @staticmethod
    def generate_salt() -> bytes:
        return os.urandom(16)
