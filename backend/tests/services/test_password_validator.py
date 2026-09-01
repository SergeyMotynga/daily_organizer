"""Тесты политики новых паролей."""

import pytest

from backend.exceptions.auth import WeakPasswordError
from backend.validators.password import PasswordValidator


@pytest.fixture
def password_validator() -> PasswordValidator:
    """Создает валидатор паролей."""
    return PasswordValidator()


@pytest.mark.parametrize(
    "password",
    [
        "Password1",
        "qwerty123",
        "ABCdef123",
    ],
)
def test_validate_new_password_accepts_valid_passwords(
    password_validator: PasswordValidator,
    password: str,
) -> None:
    """Валидные пароли проходят проверку."""
    password_validator.validate_new_password(password)


@pytest.mark.parametrize(
    "password",
    [
        "Passw1",
        "PasswordPasswordPasswordPassword1",
        "Password",
        "12345678",
        "Пароль123",
        "Password 1",
        "Password!",
    ],
)
def test_validate_new_password_rejects_invalid_passwords(
    password_validator: PasswordValidator,
    password: str,
) -> None:
    """Невалидные пароли не проходят проверку."""
    with pytest.raises(WeakPasswordError):
        password_validator.validate_new_password(password)
