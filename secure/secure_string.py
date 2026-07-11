import sys
import ctypes


class SecureString:
    """Защищённая строка: данные в памяти блокируются (mlock/VirtualLock)
    и гарантированно зануляются при освобождении."""
    def __init__(self, data: bytes = b""):
        self._data = bytearray(data)
        self._locked = self._lock_memory()

    def _lock_memory(self) -> bool:
        if sys.platform == "win32":
            try:
                mlock = ctypes.cdll.msvcrt.mlock
                mlock(ctypes.addressof(self._data), len(self._data))
                return True
            except Exception:
                return False
        elif sys.platform in ("linux", "darwin"):
            try:
                libc_name = ctypes.util.find_library("c")
                if libc_name:
                    libc = ctypes.CDLL(libc_name)
                    result = libc.mlock(ctypes.addressof(self._data), len(self._data))
                    return result == 0
            except Exception:
                pass
        return False

    def _unlock_memory(self):
        if sys.platform == "win32":
            try:
                munlock = ctypes.cdll.msvcrt.munlock
                munlock(ctypes.addressof(self._data), len(self._data))
            except Exception:
                pass
        elif sys.platform in ("linux", "darwin"):
            try:
                libc_name = ctypes.util.find_library("c")
                if libc_name:
                    libc = ctypes.CDLL(libc_name)
                    libc.munlock(ctypes.addressof(self._data), len(self._data))
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.zeroize()
        return False

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
        return f"<SecureString length={len(self._data)} locked={self._locked}>"
