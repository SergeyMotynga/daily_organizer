"""Доменные исключения auth-модуля."""


class AuthError(Exception):
    """Базовое исключение auth-модуля."""


class LoginAlreadyExistsError(AuthError):
    """Пользователь с таким login уже существует."""


class InvalidCredentialsError(AuthError):
    """Переданы неверные учетные данные."""


class InvalidOldPasswordError(AuthError):
    """Передан неверный текущий пароль."""


class UnauthorizedError(AuthError):
    """Пользователь не авторизован для protected endpoint-а."""


class InvalidRefreshTokenError(AuthError):
    """Refresh token отсутствует, истек или отозван."""


class DevEndpointDisabledError(AuthError):
    """Dev-only endpoint недоступен в текущем окружении."""


class UserNotFoundError(AuthError):
    """Пользователь не найден."""


class WeakPasswordError(AuthError):
    """Новый пароль не соответствует политике безопасности."""
