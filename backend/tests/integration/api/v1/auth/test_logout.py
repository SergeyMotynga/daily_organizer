"""Integration tests выхода пользователя."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.auth.helpers import login_user, register_user


@pytest.mark.anyio
async def test_logout_clears_cookies_and_revokes_refresh_session(client: AsyncClient) -> None:
    """Logout очищает cookies и отзывает текущую refresh-сессию."""
    await register_user(client)
    await login_user(client)

    logout_response = await client.post("/api/v1/auth/logout")
    refresh_response = await client.post("/api/v1/auth/refresh")

    assert logout_response.status_code == 204
    assert "access_token" not in client.cookies
    assert "refresh_token" not in client.cookies
    assert refresh_response.status_code == 401
    assert refresh_response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


@pytest.mark.anyio
async def test_logout_rejects_request_without_refresh_cookie(client: AsyncClient) -> None:
    """Logout без refresh cookie возвращает INVALID_REFRESH_TOKEN."""
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


@pytest.mark.anyio
async def test_logout_rejects_invalid_refresh_token(client: AsyncClient) -> None:
    """Logout с неизвестным refresh cookie возвращает INVALID_REFRESH_TOKEN."""
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": "refresh_token=invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"
