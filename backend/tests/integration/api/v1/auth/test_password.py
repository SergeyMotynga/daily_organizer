"""Integration tests смены пароля пользователя."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.auth.helpers import login_user, register_user


@pytest.mark.anyio
async def test_change_password_updates_password_clears_cookies_and_revokes_sessions(
    client: AsyncClient,
) -> None:
    """Смена пароля обновляет пароль, чистит cookies и отзывает refresh-сессии."""
    await register_user(client)
    login_response = await login_user(client)
    old_refresh_token = login_response.cookies["refresh_token"]

    response = await client.patch(
        "/api/v1/auth/password",
        json={
            "old_password": "Password1",
            "new_password": "NewPassword1",
        },
    )

    assert response.status_code == 204
    assert "access_token" not in client.cookies
    assert "refresh_token" not in client.cookies

    old_password_login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": "sergey",
            "password": "Password1",
        },
    )
    revoked_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={old_refresh_token}"},
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
    assert revoked_refresh_response.status_code == 401
    assert revoked_refresh_response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"
    assert new_password_login_response.status_code == 200
    assert "access_token" in new_password_login_response.cookies
    assert "refresh_token" in new_password_login_response.cookies


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"old_password": "", "new_password": "NewPassword1"},
        {"old_password": "Password1", "new_password": ""},
        {"old_password": "P" * 256, "new_password": "NewPassword1"},
        {"old_password": "Password1", "new_password": "P" * 256},
    ],
)
async def test_change_password_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict[str, str],
) -> None:
    """Смена пароля с невалидным payload возвращает VALIDATION_ERROR."""
    await register_user(client)
    await login_user(client)

    response = await client.patch("/api/v1/auth/password", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_change_password_rejects_wrong_old_password(client: AsyncClient) -> None:
    """Смена пароля с неверным текущим паролем возвращает INVALID_OLD_PASSWORD."""
    await register_user(client)
    await login_user(client)

    response = await client.patch(
        "/api/v1/auth/password",
        json={
            "old_password": "WrongPassword1",
            "new_password": "NewPassword1",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_OLD_PASSWORD"


@pytest.mark.anyio
async def test_change_password_rejects_weak_new_password(client: AsyncClient) -> None:
    """Смена пароля отклоняет новый пароль, который не проходит policy."""
    await register_user(client)
    await login_user(client)

    response = await client.patch(
        "/api/v1/auth/password",
        json={
            "old_password": "Password1",
            "new_password": "password",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WEAK_PASSWORD"


@pytest.mark.anyio
async def test_change_password_rejects_request_without_access_token(
    client: AsyncClient,
) -> None:
    """Смена пароля без access cookie возвращает UNAUTHORIZED."""
    response = await client.patch(
        "/api/v1/auth/password",
        json={
            "old_password": "Password1",
            "new_password": "NewPassword1",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.anyio
async def test_change_password_rejects_invalid_access_token(
    client: AsyncClient,
) -> None:
    """Смена пароля с битым access cookie возвращает UNAUTHORIZED."""
    response = await client.patch(
        "/api/v1/auth/password",
        headers={"Cookie": "access_token=invalid-token"},
        json={
            "old_password": "Password1",
            "new_password": "NewPassword1",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
