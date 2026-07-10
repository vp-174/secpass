import pytest
from secure import SecureString


class TestSecureString:
    def test_creation_with_data(self):
        data = b"secret_password"
        ss = SecureString(data)
        assert len(ss) == len(data)
        assert ss.get() == data

    def test_creation_empty(self):
        ss = SecureString()
        assert len(ss) == 0

    def test_get_returns_bytes(self):
        data = b"test_data"
        ss = SecureString(data)
        result = ss.get()
        assert isinstance(result, bytes)
        assert result == data

    def test_str_conversion(self):
        data = b"hello"
        ss = SecureString(data)
        assert str(ss) == "hello"

    def test_repr(self):
        ss = SecureString(b"test")
        assert "SecureString" in repr(ss)
        assert "length=4" in repr(ss)

    def test_length(self):
        ss = SecureString(b"12345678")
        assert len(ss) == 8

    def test_zeroize_clears_data(self):
        data = b"secret_data"
        ss = SecureString(data)
        ss.zeroize()
        result = ss.get()
        assert result != data

    def test_empty_data_length(self):
        ss = SecureString(b"")
        assert len(ss) == 0

    def test_large_data(self):
        data = b"x" * 10000
        ss = SecureString(data)
        assert len(ss) == 10000
        assert ss.get() == data

    def test_binary_data(self):
        data = bytes(range(256))
        ss = SecureString(data)
        assert len(ss) == 256
        assert ss.get() == data
