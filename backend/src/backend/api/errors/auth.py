"""API-представление auth-ошибок."""

from backend.api.errors.responses import ErrorSpec
from backend.exceptions.auth import (
    AuthError,
    DevEndpointDisabledError,
    InvalidCredentialsError,
    InvalidOldPasswordError,
    InvalidRefreshTokenError,
    LoginAlreadyExistsError,
    UnauthorizedError,
    UserNotFoundError,
    WeakPasswordError,
)

AUTH_ERROR_SPECS: dict[type[AuthError], ErrorSpec] = {
    LoginAlreadyExistsError: ErrorSpec(
        status_code=409,
        code="LOGIN_ALREADY_EXISTS",
        message="Пользователь с таким login уже существует. Login чувствителен к регистру",
    ),
    InvalidCredentialsError: ErrorSpec(
        status_code=401,
        code="INVALID_CREDENTIALS",
        message="Неверный login или пароль. Login и пароль чувствительны к регистру",
    ),
    InvalidOldPasswordError: ErrorSpec(
        status_code=401,
        code="INVALID_OLD_PASSWORD",
        message="Неверный текущий пароль",
    ),
    UnauthorizedError: ErrorSpec(
        status_code=401,
        code="UNAUTHORIZED",
        message="Требуется авторизация",
    ),
    InvalidRefreshTokenError: ErrorSpec(
        status_code=401,
        code="INVALID_REFRESH_TOKEN",
        message="Refresh-сессия недействительна",
    ),
    DevEndpointDisabledError: ErrorSpec(
        status_code=404,
        code="DEV_ENDPOINT_DISABLED",
        message="Dev endpoint недоступен",
    ),
    UserNotFoundError: ErrorSpec(
        status_code=404,
        code="USER_NOT_FOUND",
        message="Пользователь не найден",
    ),
    WeakPasswordError: ErrorSpec(
        status_code=400,
        code="WEAK_PASSWORD",
        message=(
            "Пароль должен быть от 8 до 30 символов и содержать только латинские "
            "буквы и цифры, минимум одну букву и одну цифру"
        ),
    ),
}
