import math
import re
import secrets

CHARS_LOWER = "abcdefghijklmnopqrstuvwxyz"
CHARS_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CHARS_DIGITS = "0123456789"
CHARS_SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"

MIN_ENTROPY_BITS = 80
MIN_MASTER_LENGTH = 12
GEN_MIN_LENGTH = 8
GEN_MAX_LENGTH = 128

STRENGTH_COLORS = {
    1: "#ff0000",
    2: "#ff6600",
    3: "#ffcc00",
    4: "#88ff00",
    5: "#00cc00",
}


def calculate_entropy(password: str) -> float:
    """Оценка энтропии: пул по фактическим размерам классов символов
    с поправкой на повторяющиеся символы."""
    if not password:
        return 0.0

    pool_size = 0
    if re.search(r"[a-z]", password):
        pool_size += len(CHARS_LOWER)
    if re.search(r"[A-Z]", password):
        pool_size += len(CHARS_UPPER)
    if re.search(r"[0-9]", password):
        pool_size += len(CHARS_DIGITS)
    if any(c in CHARS_SPECIAL for c in password):
        pool_size += len(CHARS_SPECIAL)

    if pool_size == 0:
        pool_size = len(CHARS_LOWER)

    entropy = len(password) * math.log2(pool_size)

    unique = len(set(password))
    if unique < len(password):
        entropy *= unique / len(password)
    return entropy


def get_strength_level(entropy: float) -> tuple:
    """Возвращает (уровень 1..5, текстовую метку); цвета — в STRENGTH_COLORS."""
    if entropy < 28:
        return 1, "Very Weak"
    elif entropy < 50:
        return 2, "Weak"
    elif entropy < 80:
        return 3, "Fair"
    elif entropy < 128:
        return 4, "Strong"
    else:
        return 5, "Very Strong"


def generate_password(
    length: int,
    upper: bool = True,
    lower: bool = True,
    digits: bool = True,
    special: bool = True,
) -> str:
    """Генерация пароля через CSPRNG (модуль secrets)."""
    chars = ""
    if upper:
        chars += CHARS_UPPER
    if lower:
        chars += CHARS_LOWER
    if digits:
        chars += CHARS_DIGITS
    if special:
        chars += CHARS_SPECIAL

    if not chars:
        chars = CHARS_LOWER

    return "".join(secrets.choice(chars) for _ in range(length))


def _generate_password_for(password_input, parent):
    from gui.dialogs.password_generator_dialog import PasswordGeneratorDialog

    dialog = PasswordGeneratorDialog(parent)
    if dialog.exec():
        password_input.setText(dialog.get_password())
