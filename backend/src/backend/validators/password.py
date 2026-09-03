"""Валидация политики новых паролей."""

import string

from backend.exceptions.auth import WeakPasswordError

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 30
ALLOWED_PASSWORD_CHARS = string.ascii_letters + string.digits


class PasswordValidator:
    """Проверяет новые пароли по политике v0.1."""

    def validate_new_password(self, password: str) -> None:
        """Проверяет пароль для регистрации, смены или dev reset."""
        if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
            raise WeakPasswordError()

        if any(char not in ALLOWED_PASSWORD_CHARS for char in password):
            raise WeakPasswordError()

        has_latin_letter = any(char in string.ascii_letters for char in password)
        if not has_latin_letter:
            raise WeakPasswordError()

        has_digit = any(char in string.digits for char in password)
        if not has_digit:
            raise WeakPasswordError()
