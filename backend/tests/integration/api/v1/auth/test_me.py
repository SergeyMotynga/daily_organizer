"""Integration tests получения текущего пользователя."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.auth.helpers import login_user, register_user

from backend.core.config import get_settings
from backend.core.security import create_access_token


@pytest.mark.anyio
async def test_me_rejects_request_without_access_token(client: AsyncClient) -> None:
    """Запрос без access cookie возвращает UNAUTHORIZED."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.anyio
async def test_me_rejects_invalid_access_token(client: AsyncClient) -> None:
    """Запрос с битым access cookie возвращает UNAUTHORIZED."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Cookie": "access_token=invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.anyio
async def test_me_rejects_access_token_for_unknown_user(client: AsyncClient) -> None:
    """Запрос с access token несуществующего пользователя возвращает UNAUTHORIZED."""
    access_token = create_access_token(uuid4(), get_settings())

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Cookie": f"access_token={access_token}"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.anyio
async def test_me_returns_current_user(client: AsyncClient) -> None:
    """Запрос с access cookie возвращает текущего пользователя."""
    await register_user(client)
    login_response = await login_user(client)

    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == login_response.json()
