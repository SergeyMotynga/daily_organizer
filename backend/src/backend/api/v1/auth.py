"""Auth endpoint-ы API v1."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from backend.api.cookies import clear_auth_cookies, set_access_cookie, set_auth_cookies
from backend.api.deps import (
    REFRESH_COOKIE_NAME,
    get_auth_service,
    get_current_user,
)
from backend.core.config import Settings, get_settings
from backend.models.user import User
from backend.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from backend.schemas.users import UserResponse
from backend.services.auth import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Регистрирует пользователя без автоматического входа."""
    return await auth_service.register(
        login=payload.login,
        password=payload.password,
        name=payload.name,
    )


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Аутентифицирует пользователя и устанавливает auth cookies."""
    auth = await auth_service.login(login=payload.login, password=payload.password)
    set_auth_cookies(response, auth, settings)
    return auth.user


@router.post("/refresh", response_model=UserResponse)
async def refresh(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME, include_in_schema=False),
    ] = None,
) -> User:
    """Выдает новый access token по refresh cookie."""
    auth = await auth_service.refresh(refresh_token)
    set_access_cookie(response, auth, settings)
    return auth.user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[
        str | None,
        Cookie(alias=REFRESH_COOKIE_NAME, include_in_schema=False),
    ] = None,
) -> None:
    """Отзывает текущую refresh-сессию и очищает auth cookies."""
    await auth_service.logout(refresh_token)
    clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Возвращает текущего пользователя."""
    return current_user


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Меняет пароль текущего пользователя."""
    await auth_service.change_password(
        user=current_user,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )
    clear_auth_cookies(response)
