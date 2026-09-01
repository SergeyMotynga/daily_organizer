"""Integration tests обновления access token."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.auth.helpers import login_user, register_user


@pytest.mark.anyio
async def test_refresh_updates_access_cookie(client: AsyncClient) -> None:
    """Refresh по активной сессии обновляет access cookie."""
    await register_user(client)
    login_response = await login_user(client)
    old_access_token = login_response.cookies["access_token"]

    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json() == login_response.json()
    assert "access_token" in response.cookies
    assert response.cookies["access_token"] != old_access_token


@pytest.mark.anyio
async def test_refresh_rejects_request_without_refresh_cookie(client: AsyncClient) -> None:
    """Refresh без refresh cookie возвращает INVALID_REFRESH_TOKEN."""
    response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


@pytest.mark.anyio
async def test_refresh_rejects_invalid_refresh_token(client: AsyncClient) -> None:
    """Refresh с неизвестным refresh cookie возвращает INVALID_REFRESH_TOKEN."""
    response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": "refresh_token=invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"
