"""FastAPI dependencies для API-слоя."""

from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings, get_settings
from backend.core.security import decode_access_token
from backend.db.session import get_db
from backend.exceptions.auth import UnauthorizedError
from backend.models.user import User
from backend.repositories.users import UserRepository
from backend.services.auth import AuthService
from backend.services.tasks import TaskService

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    """Создает AuthService для обработки запроса."""
    return AuthService(db, settings)


def get_task_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TaskService:
    """Создает TaskService для обработки запроса."""
    return TaskService(db)


def get_access_token_cookie(
    access_token: Annotated[
        str | None,
        Cookie(alias=ACCESS_COOKIE_NAME, include_in_schema=False),
    ] = None,
) -> str:
    """Возвращает access token из cookie или выбрасывает auth-ошибку."""
    if access_token is None:
        raise UnauthorizedError()

    return access_token


async def get_current_user(
    access_token: Annotated[str, Depends(get_access_token_cookie)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Возвращает текущего пользователя по access token из cookie."""
    user_id = decode_access_token(access_token, settings)
    if user_id is None:
        raise UnauthorizedError()

    user = await UserRepository(db).get_user_by_id(user_id)
    if user is None:
        raise UnauthorizedError()

    return user
