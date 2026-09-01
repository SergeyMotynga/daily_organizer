"""Helpers для auth integration tests."""

from typing import cast

from httpx import AsyncClient, Response


async def register_user(
    client: AsyncClient,
    *,
    login: str = "sergey",
    password: str = "Password1",
    name: str = "Sergey",
) -> dict[str, str]:
    """Регистрирует пользователя через API и возвращает JSON-ответ."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "login": login,
            "password": password,
            "name": name,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, str], response.json())


async def login_user(
    client: AsyncClient,
    *,
    login: str = "sergey",
    password: str = "Password1",
) -> Response:
    """Выполняет вход пользователя через API."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "login": login,
            "password": password,
        },
    )
    assert response.status_code == 200
    return response
