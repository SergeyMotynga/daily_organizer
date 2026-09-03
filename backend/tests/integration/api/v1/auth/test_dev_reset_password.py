"""Integration tests dev-сброса пароля пользователя."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.auth.helpers import login_user, register_user

from backend.core.config import get_settings
from backend.main import app


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"login": "", "new_password": "NewPassword1"},
        {"login": "sergey", "new_password": ""},
        {"login": "s" * 256, "new_password": "NewPassword1"},
        {"login": "sergey", "new_password": "P" * 256},
    ],
)
async def test_dev_reset_password_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict[str, str],
) -> None:
    """Dev reset с невалидным payload возвращает VALIDATION_ERROR."""
    response = await client.post("/api/v1/dev/auth/reset-password", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_dev_reset_password_updates_password_and_revokes_sessions(
    client: AsyncClient,
) -> None:
    """Dev reset обновляет пароль пользователя и отзывает refresh-сессии."""
    await register_user(client)
    await login_user(client)

    response = await client.post(
        "/api/v1/dev/auth/reset-password",
        json={
            "login": "sergey",
            "new_password": "NewPassword1",
        },
    )
    revoked_refresh_response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 204
    assert revoked_refresh_response.status_code == 401
    assert revoked_refresh_response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"

    old_password_login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": "sergey",
            "password": "Password1",
        },
    )
    new_password_login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": "sergey",
            "password": "NewPassword1",
        },
    )

    assert old_password_login_response.status_code == 401
    assert old_password_login_response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert new_password_login_response.status_code == 200


@pytest.mark.anyio
async def test_dev_reset_password_rejects_weak_password(client: AsyncClient) -> None:
    """Dev reset отклоняет новый пароль, который не проходит policy."""
    await register_user(client)

    response = await client.post(
        "/api/v1/dev/auth/reset-password",
        json={
            "login": "sergey",
            "new_password": "password",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WEAK_PASSWORD"


@pytest.mark.anyio
async def test_dev_reset_password_rejects_unknown_user(client: AsyncClient) -> None:
    """Dev reset для неизвестного пользователя возвращает USER_NOT_FOUND."""
    response = await client.post(
        "/api/v1/dev/auth/reset-password",
        json={
            "login": "unknown",
            "new_password": "NewPassword1",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


@pytest.mark.anyio
async def test_dev_reset_password_is_disabled_outside_dev_mode(
    client: AsyncClient,
) -> None:
    """Dev reset вне dev-mode возвращает DEV_ENDPOINT_DISABLED."""
    settings = get_settings().model_copy(update={"app_env": "prod"})
    app.dependency_overrides[get_settings] = lambda: settings

    response = await client.post(
        "/api/v1/dev/auth/reset-password",
        json={
            "login": "sergey",
            "new_password": "NewPassword1",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DEV_ENDPOINT_DISABLED"
