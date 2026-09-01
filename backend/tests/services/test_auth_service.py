"""Unit tests AuthService."""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.exceptions.auth import UserNotFoundError
from backend.services.auth import AuthService


@pytest.mark.anyio
async def test_refresh_raises_user_not_found_when_session_user_is_missing() -> None:
    """Refresh возвращает USER_NOT_FOUND, если refresh-сессия указывает на удаленного user."""
    service = AuthService(db=cast(AsyncSession, object()), settings=get_settings())
    user_id = uuid4()
    cast(Any, service).user_sessions = SimpleNamespace(
        get_active_session_by_hash=AsyncMock(return_value=SimpleNamespace(user_id=user_id)),
    )
    cast(Any, service).users = SimpleNamespace(get_user_by_id=AsyncMock(return_value=None))

    with pytest.raises(UserNotFoundError):
        await service.refresh("refresh-token")

    cast(Any, service).users.get_user_by_id.assert_awaited_once_with(user_id)
