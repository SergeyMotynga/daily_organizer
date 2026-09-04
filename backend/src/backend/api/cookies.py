"""Helper-функции для auth cookies."""

from fastapi import Response

from backend.api.deps import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME
from backend.core.config import Settings
from backend.services.auth import AuthResult


def set_access_cookie(response: Response, auth: AuthResult, settings: Settings) -> None:
    """Устанавливает access token в httpOnly cookie."""
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        auth.access_token,
        max_age=settings.jwt_access_token_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def set_auth_cookies(response: Response, auth: AuthResult, settings: Settings) -> None:
    """Устанавливает access и refresh token в httpOnly cookies."""
    set_access_cookie(response, auth, settings)
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        auth.refresh_token,
        max_age=settings.jwt_refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Удаляет access и refresh cookies."""
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
