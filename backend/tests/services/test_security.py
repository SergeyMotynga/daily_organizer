"""Тесты security-утилит."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import jwt

from backend.core.config import get_settings
from backend.core.security import create_access_token, decode_access_token


def test_decode_access_token_returns_user_id_for_valid_token() -> None:
    """Валидный access token декодируется в user id."""
    settings = get_settings()
    user_id = uuid4()
    token = create_access_token(user_id, settings)

    assert decode_access_token(token, settings) == user_id


def test_decode_access_token_rejects_wrong_token_type() -> None:
    """Token с неподходящим type не считается access token."""
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    assert decode_access_token(token, settings) is None


def test_decode_access_token_rejects_missing_subject() -> None:
    """Token без sub не декодируется в пользователя."""
    settings = get_settings()
    token = jwt.encode(
        {
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    assert decode_access_token(token, settings) is None


def test_decode_access_token_rejects_malformed_subject() -> None:
    """Token с sub не в формате UUID не декодируется в пользователя."""
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "not-a-uuid",
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    assert decode_access_token(token, settings) is None
