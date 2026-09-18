"""Integration tests входа пользователя."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.auth.helpers import register_user


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"login": "", "password": "Password1"},
        {"login": "sergey", "password": ""},
        {"login": "s" * 256, "password": "Password1"},
        {"login": "sergey", "password": "P" * 256},
    ],
)
async def test_login_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict[str, str],
) -> None:
    """Вход с невалидным payload возвращает VALIDATION_ERROR."""
    response = await client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_login_sets_auth_cookies(client: AsyncClient) -> None:
    """Успешный вход устанавливает access и refresh cookies."""
    await register_user(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": "sergey",
            "password": "Password1",
        },
    )

    assert response.status_code == 200
    assert response.json()["login"] == "sergey"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.anyio
async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    """Вход с неверным паролем возвращает INVALID_CREDENTIALS."""
    await register_user(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": "sergey",
            "password": "WrongPassword1",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert response.json()["error"]["message"] == (
        "Неверный login или пароль. Login и пароль чувствительны к регистру"
    )


@pytest.mark.anyio
async def test_login_rejects_unknown_login(client: AsyncClient) -> None:
    """Вход с неизвестным login возвращает INVALID_CREDENTIALS."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": "unknown",
            "password": "Password1",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
