"""Бизнес-логика auth-модуля."""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import Settings
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    utc_now,
    verify_password,
)
from backend.exceptions.auth import (
    DevEndpointDisabledError,
    InvalidCredentialsError,
    InvalidOldPasswordError,
    InvalidRefreshTokenError,
    LoginAlreadyExistsError,
    UserNotFoundError,
)
from backend.models.user import User, UserSession
from backend.repositories.user_sessions import UserSessionRepository
from backend.repositories.users import UserRepository
from backend.validators.password import PasswordValidator


@dataclass(frozen=True)
class AuthResult:
    """Результат успешной auth-операции с выдачей токенов."""

    user: User
    access_token: str
    refresh_token: str


class AuthService:
    """Координирует auth-сценарии и транзакции."""

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        password_validator: PasswordValidator | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)
        self.user_sessions = UserSessionRepository(db)
        self.password_validator = password_validator or PasswordValidator()

    async def register(self, *, login: str, password: str, name: str) -> User:
        """Регистрирует пользователя без автоматического входа."""
        self.password_validator.validate_new_password(password)

        existing_user = await self.users.get_user_by_login(login)
        if existing_user is not None:
            raise LoginAlreadyExistsError()

        try:
            user = await self.users.create_user(
                login=login,
                name=name,
                password_hash=hash_password(password),
            )
            await self.db.commit()
        except IntegrityError as error:
            await self.db.rollback()
            constraint_name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            if constraint_name == "uq_users_login":
                raise LoginAlreadyExistsError() from error
            raise

        return user

    async def login(self, *, login: str, password: str) -> AuthResult:
        """Аутентифицирует пользователя и создает refresh-сессию."""
        user = await self.users.get_user_by_login(login)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        refresh_token = create_refresh_token()
        expires_at = utc_now() + timedelta(days=self.settings.jwt_refresh_token_ttl_days)
        await self.user_sessions.create_session(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
        access_token = create_access_token(user.id, self.settings)
        await self.db.commit()
        return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str | None) -> AuthResult:
        """Выдает новый access token по активной refresh-сессии."""
        user_session = await self._get_active_refresh_session(refresh_token)
        user = await self.users.get_user_by_id(user_session.user_id)
        if user is None:
            raise UserNotFoundError()

        access_token = create_access_token(user.id, self.settings)
        return AuthResult(user=user, access_token=access_token, refresh_token=refresh_token or "")

    async def logout(self, refresh_token: str | None) -> None:
        """Отзывает текущую refresh-сессию."""
        user_session = await self._get_active_refresh_session(refresh_token)
        await self.user_sessions.revoke_session(user_session, utc_now())
        await self.db.commit()

    async def change_password(self, *, user: User, old_password: str, new_password: str) -> None:
        """Меняет пароль пользователя и отзывает все его refresh-сессии."""
        if not verify_password(old_password, user.password_hash):
            raise InvalidOldPasswordError()

        self.password_validator.validate_new_password(new_password)
        now = utc_now()
        await self.users.update_user_password(user, hash_password(new_password))
        await self.user_sessions.revoke_all_sessions_for_user(user.id, now)
        await self.db.commit()

    async def dev_reset_password(self, *, login: str, new_password: str) -> None:
        """Сбрасывает пароль пользователя в dev-режиме."""
        if not self.settings.is_dev_mode:
            raise DevEndpointDisabledError()

        self.password_validator.validate_new_password(new_password)
        user = await self.users.get_user_by_login(login)
        if user is None:
            raise UserNotFoundError()

        now = utc_now()
        await self.users.update_user_password(user, hash_password(new_password))
        await self.user_sessions.revoke_all_sessions_for_user(user.id, now)
        await self.db.commit()

    async def _get_active_refresh_session(self, refresh_token: str | None) -> UserSession:
        """Возвращает активную refresh-сессию или выбрасывает auth-ошибку."""
        if not refresh_token:
            raise InvalidRefreshTokenError()

        user_session = await self.user_sessions.get_active_session_by_hash(
            hash_refresh_token(refresh_token),
            utc_now(),
        )
        if user_session is None:
            raise InvalidRefreshTokenError()

        return user_session
