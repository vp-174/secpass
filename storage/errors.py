class StorageError(Exception):
    """Базовая ошибка хранилища."""


class VaultExistsError(StorageError):
    """Хранилище уже существует по указанному пути."""


class VaultNotFoundError(StorageError):
    """Хранилище не найдено."""


class VaultLockedError(StorageError):
    """Операция требует разблокированного хранилища."""


class InvalidPasswordError(StorageError):
    """Неверный пароль/ключ-файл либо повреждённый мастер-ключ."""


class TamperError(StorageError):
    """Данные повреждены или подделаны (не прошли проверку целостности)."""


class KeyfileError(StorageError):
    """Проблема с ключ-файлом: отсутствует, слишком большой или не ожидался."""


class DuplicateNameError(StorageError, ValueError):
    """Имя записи или группы уже занято."""


class GroupNotEmptyError(StorageError):
    """Группа не пуста: содержит записи или подгруппы."""
