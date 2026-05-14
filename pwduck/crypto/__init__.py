import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.backends import default_backend
from pwduck.debug import get_logger

logger = get_logger("crypto")


class CipherSuite:
    BLOCK_SIZE = 16

    @staticmethod
    def derive_key(password: bytes, salt: bytes, memory: int = 65536, iterations: int = 3) -> bytes:
        logger.debug(f"Deriving key with salt={salt[:8].hex()}..., memory={memory}, iterations={iterations}")
        kdf = Argon2id(
            salt=salt,
            length=32,
            memory_cost=memory,
            iterations=iterations,
            lanes=4,
        )
        key = kdf.derive(password)
        logger.debug(f"Key derived successfully, length={len(key)}")
        return key

    @staticmethod
    def encrypt_aes_cbc(key: bytes, plaintext: bytes) -> bytes:
        logger.debug(f"AES-CBC encrypt: plaintext_len={len(plaintext)}")
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padding = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([padding] * padding)
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        result = base64.b64encode(iv + ciphertext)
        logger.debug(f"AES-CBC encrypt: ciphertext_len={len(result)}")
        return result

    @staticmethod
    def decrypt_aes_cbc(key: bytes, ciphertext: bytes) -> bytes:
        logger.debug(f"AES-CBC decrypt: ciphertext_len={len(ciphertext)}")
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
        result = padded[:-padding]
        logger.debug(f"AES-CBC decrypt: plaintext_len={len(result)}")
        return result

    @staticmethod
    def encrypt_chacha20(key: bytes, plaintext: bytes) -> bytes:
        logger.debug(f"ChaCha20 encrypt: plaintext_len={len(plaintext)}")
        nonce = os.urandom(16)
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext)
        result = base64.b64encode(nonce + ciphertext)
        logger.debug(f"ChaCha20 encrypt: ciphertext_len={len(result)}")
        return result

    @staticmethod
    def decrypt_chacha20(key: bytes, ciphertext: bytes) -> bytes:
        logger.debug(f"ChaCha20 decrypt: ciphertext_len={len(ciphertext)}")
        data = base64.b64decode(ciphertext)
        nonce = data[:16]
        ct = data[16:]
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
        decryptor = cipher.decryptor()
        result = decryptor.update(ct)
        logger.debug(f"ChaCha20 decrypt: plaintext_len={len(result)}")
        return result

    @staticmethod
    def generate_master_key() -> bytes:
        logger.debug("Generating master key")
        return os.urandom(32)

    @staticmethod
    def generate_salt() -> bytes:
        logger.debug("Generating salt")
        return os.urandom(16)