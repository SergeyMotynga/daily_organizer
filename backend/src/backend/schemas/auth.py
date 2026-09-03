"""DTO запросов auth API."""

from pydantic import BaseModel, Field, field_validator


def trim(value: str) -> str:
    """Обрезает пробелы по краям строки."""
    return value.strip()


class RegisterRequest(BaseModel):
    """Запрос регистрации пользователя."""

    login: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)

    _trim_login = field_validator("login")(trim)
    _trim_name = field_validator("name")(trim)


class LoginRequest(BaseModel):
    """Запрос входа пользователя."""

    login: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)

    _trim_login = field_validator("login")(trim)


class ChangePasswordRequest(BaseModel):
    """Запрос смены пароля текущего пользователя."""

    old_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=1, max_length=255)


class DevResetPasswordRequest(BaseModel):
    """Запрос dev-сброса пароля."""

    login: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=1, max_length=255)

    _trim_login = field_validator("login")(trim)
