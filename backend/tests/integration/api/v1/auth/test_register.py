"""Integration tests регистрации пользователя."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"login": "", "password": "Password1", "name": "Sergey"},
        {"login": "sergey", "password": "", "name": "Sergey"},
        {"login": "sergey", "password": "Password1", "name": ""},
        {"login": "s" * 256, "password": "Password1", "name": "Sergey"},
        {"login": "sergey", "password": "P" * 256, "name": "Sergey"},
        {"login": "sergey", "password": "Password1", "name": "S" * 256},
    ],
)
async def test_register_rejects_invalid_payload(
    client: AsyncClient,
    payload: dict[str, str],
) -> None:
    """Регистрация с невалидным payload возвращает VALIDATION_ERROR."""
    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_register_creates_user(client: AsyncClient) -> None:
    """Регистрация создает пользователя и не логинит автоматически."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "login": "sergey",
            "password": "Password1",
            "name": "Sergey",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "login": "sergey",
        "name": "Sergey",
    }
    assert "access_token" not in response.cookies
    assert "refresh_token" not in response.cookies


@pytest.mark.anyio
async def test_register_rejects_weak_password(client: AsyncClient) -> None:
    """Регистрация отклоняет пароль, который не проходит policy."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "login": "sergey",
            "password": "password",
            "name": "Sergey",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WEAK_PASSWORD"


@pytest.mark.anyio
async def test_register_rejects_duplicate_login(client: AsyncClient) -> None:
    """Регистрация отклоняет повторный login."""
    payload = {
        "login": "sergey",
        "password": "Password1",
        "name": "Sergey",
    }
    first_response = await client.post("/api/v1/auth/register", json=payload)
    second_response = await client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "LOGIN_ALREADY_EXISTS"
