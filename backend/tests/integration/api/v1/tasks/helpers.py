"""Helper-функции для integration tests задач."""

from typing import Any, cast

from httpx import AsyncClient
from tests.integration.api.v1.helpers import login_user, register_user


async def auth_client(
    client: AsyncClient,
    *,
    login: str = "sergey",
    password: str = "Password1",
    name: str = "Sergey",
) -> None:
    """Регистрирует пользователя и логинит тестовый клиент."""
    await register_user(client, login=login, password=password, name=name)
    await login_user(client, login=login, password=password)


async def create_task(
    client: AsyncClient,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Создает задачу через API и возвращает JSON-ответ."""
    response = await client.post(
        "/api/v1/tasks",
        json=payload or {"title": "Задача"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())
