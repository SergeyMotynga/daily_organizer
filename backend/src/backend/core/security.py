"""Security-утилиты для паролей и токенов."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import Settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_BYTES = 64

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хеширует пароль для хранения в БД."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль по сохраненному hash."""
    return pwd_context.verify(password, password_hash)


def create_refresh_token() -> str:
    """Создает opaque refresh token."""
    return token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(refresh_token: str) -> str:
    """Хеширует refresh token перед сохранением или сравнением."""
    return sha256(refresh_token.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    """Возвращает текущий timezone-aware UTC datetime."""
    return datetime.now(UTC)


def create_access_token(user_id: UUID, settings: Settings) -> str:
    """Создает JWT access token для пользователя."""
    expires_at = utc_now() + timedelta(minutes=settings.jwt_access_token_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "jti": str(uuid4()),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> UUID | None:
    """Декодирует и валидирует JWT access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except JWTError:
        return None

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None

    try:
        return UUID(subject)
    except ValueError:
        return None
