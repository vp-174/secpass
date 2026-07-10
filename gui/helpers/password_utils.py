import re
import math


def calculate_entropy(password: str) -> float:
    if not password:
        return 0.0

    char_sets = 0
    if re.search(r'[a-z]', password):
        char_sets += 1
    if re.search(r'[A-Z]', password):
        char_sets += 1
    if re.search(r'[0-9]', password):
        char_sets += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        char_sets += 1

    pool_size = 0
    if char_sets == 0:
        return 0.0

    if re.search(r'[a-z]', password):
        pool_size += 26
    if re.search(r'[A-Z]', password):
        pool_size += 26
    if re.search(r'[0-9]', password):
        pool_size += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        pool_size += 32

    if pool_size == 0:
        pool_size = 26

    entropy = len(password) * math.log2(pool_size)
    return entropy


def get_strength_level(entropy: float) -> tuple:
    if entropy < 28:
        return 1, "Very Weak", "#ff0000"
    elif entropy < 50:
        return 2, "Weak", "#ff6600"
    elif entropy < 80:
        return 3, "Fair", "#ffcc00"
    elif entropy < 128:
        return 4, "Strong", "#88ff00"
    else:
        return 5, "Very Strong", "#00cc00"


def _generate_password_for(password_input, parent):
    from gui.dialogs.password_generator_dialog import PasswordGeneratorDialog
    dialog = PasswordGeneratorDialog(parent)
    if dialog.exec():
        password_input.setText(dialog.get_password())
