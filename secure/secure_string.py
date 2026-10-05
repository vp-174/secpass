import ctypes
import ctypes.util
import sys


def _buffer_address(buf: bytearray) -> int:
    """Адрес буфера bytearray для передачи в нативные вызовы."""
    return ctypes.addressof((ctypes.c_char * len(buf)).from_buffer(buf))


class SecureString:
    """Защищённая строка: данные в памяти блокируются (mlock/VirtualLock)
    и гарантированно зануляются при освобождении."""

    def __init__(self, data: bytes = b""):
        self._data = bytearray(data)
        self._locked = False
        self._locked = self._lock_memory()

    def _lock_memory(self) -> bool:
        if not self._data:
            return False
        try:
            addr = ctypes.c_void_p(_buffer_address(self._data))
            size = ctypes.c_size_t(len(self._data))
            if sys.platform == "win32":
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                fn = kernel32.VirtualLock
                fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                fn.restype = ctypes.c_bool
                return bool(fn(addr, size))
            libc = ctypes.CDLL(ctypes.util.find_library("c") or None)
            fn = libc.mlock
            fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
            fn.restype = ctypes.c_int
            return fn(addr, size) == 0
        except Exception:
            return False

    def _unlock_memory(self):
        if not self._locked or not self._data:
            return
        try:
            addr = ctypes.c_void_p(_buffer_address(self._data))
            size = ctypes.c_size_t(len(self._data))
            if sys.platform == "win32":
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                fn = kernel32.VirtualUnlock
                fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                fn.restype = ctypes.c_bool
                fn(addr, size)
            else:
                libc = ctypes.CDLL(ctypes.util.find_library("c") or None)
                fn = libc.munlock
                fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                fn.restype = ctypes.c_int
                fn(addr, size)
        except Exception:
            pass
        finally:
            self._locked = False

    def __del__(self):
        try:
            self.zeroize()
        except Exception:
            pass

    def zeroize(self):
        """Зануляет содержимое и снимает блокировку памяти. Идемпотентно."""
        try:
            if self._data:
                ctypes.memset(_buffer_address(self._data), 0, len(self._data))
        finally:
            self._unlock_memory()

    def get(self) -> bytes:
        """Возвращает копию данных (копия не подлежит занулению)."""
        return bytes(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"<SecureString length={len(self._data)} locked={self._locked}>"
