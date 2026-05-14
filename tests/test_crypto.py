import pytest
from pwduck.crypto import CipherSuite


class TestCipherSuite:
    def test_generate_master_key(self):
        key = CipherSuite.generate_master_key()
        assert len(key) == 32
        assert isinstance(key, bytes)

    def test_generate_salt(self):
        salt = CipherSuite.generate_salt()
        assert len(salt) == 16
        assert isinstance(salt, bytes)

    def test_derive_key(self):
        password = b"test_password"
        salt = CipherSuite.generate_salt()
        key = CipherSuite.derive_key(password, salt)
        assert len(key) == 32
        assert isinstance(key, bytes)

    def test_derive_key_different_salts(self):
        password = b"test_password"
        salt1 = CipherSuite.generate_salt()
        salt2 = CipherSuite.generate_salt()
        key1 = CipherSuite.derive_key(password, salt1)
        key2 = CipherSuite.derive_key(password, salt2)
        assert key1 != key2

    def test_derive_key_same_password_salt(self):
        password = b"test_password"
        salt = CipherSuite.generate_salt()
        key1 = CipherSuite.derive_key(password, salt)
        key2 = CipherSuite.derive_key(password, salt)
        assert key1 == key2

    def test_encrypt_decrypt_aes_cbc(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"Hello, World!"
        ciphertext = CipherSuite.encrypt_aes_cbc(key, plaintext)
        decrypted = CipherSuite.decrypt_aes_cbc(key, ciphertext)
        assert decrypted == plaintext

    def test_encrypt_decrypt_aes_cbc_longer(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"A" * 1000
        ciphertext = CipherSuite.encrypt_aes_cbc(key, plaintext)
        decrypted = CipherSuite.decrypt_aes_cbc(key, ciphertext)
        assert decrypted == plaintext

    def test_encrypt_aes_cbc_random_iv(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"Test message"
        ct1 = CipherSuite.encrypt_aes_cbc(key, plaintext)
        ct2 = CipherSuite.encrypt_aes_cbc(key, plaintext)
        assert ct1 != ct2

    def test_encrypt_decrypt_chacha20(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"Secret message"
        ciphertext = CipherSuite.encrypt_chacha20(key, plaintext)
        decrypted = CipherSuite.decrypt_chacha20(key, ciphertext)
        assert decrypted == plaintext

    def test_encrypt_decrypt_chacha20_longer(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"X" * 5000
        ciphertext = CipherSuite.encrypt_chacha20(key, plaintext)
        decrypted = CipherSuite.decrypt_chacha20(key, ciphertext)
        assert decrypted == plaintext

    def test_chacha20_different_nonces(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"Same message"
        ct1 = CipherSuite.encrypt_chacha20(key, plaintext)
        ct2 = CipherSuite.encrypt_chacha20(key, plaintext)
        assert ct1 != ct2

    def test_decrypt_wrong_key_raises(self):
        key1 = CipherSuite.generate_master_key()
        key2 = CipherSuite.generate_master_key()
        plaintext = b"Secret"
        ciphertext = CipherSuite.encrypt_aes_cbc(key1, plaintext)
        with pytest.raises(Exception):
            CipherSuite.decrypt_aes_cbc(key2, ciphertext)

    def test_decrypt_invalid_data_raises(self):
        key = CipherSuite.generate_master_key()
        with pytest.raises(Exception):
            CipherSuite.decrypt_aes_cbc(key, b"invalid_base64!")

    def test_encrypt_returns_base64(self):
        key = CipherSuite.generate_master_key()
        plaintext = b"test"
        result = CipherSuite.encrypt_aes_cbc(key, plaintext)
        assert all(c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in result)