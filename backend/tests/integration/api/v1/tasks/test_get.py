"""Integration tests получения задач."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.tasks.helpers import auth_client, create_task


@pytest.mark.anyio
async def test_get_task_returns_own_task(client: AsyncClient) -> None:
    """Получение одной задачи возвращает задачу владельца."""
    await auth_client(client)
    created_task = await create_task(
        client,
        {
            "title": "Прочитать",
            "deadline_date": "2026-09-10",
            "deadline_time": "18:30",
            "recurrence_type_code": "weekly",
            "recurrence_start_date": "2026-09-03",
        },
    )

    response = await client.get(f"/api/v1/tasks/{created_task['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created_task["id"]
    assert response.json()["title"] == "Прочитать"
    assert response.json()["status"] == "todo"
    assert response.json()["deadline_time"] == "18:30"
    assert response.json()["recurrence_type_code"] == "weekly"
    assert "status_code" not in response.json()


@pytest.mark.anyio
async def test_get_unknown_task_returns_404(client: AsyncClient) -> None:
    """Несуществующая задача возвращает TASK_NOT_FOUND."""
    await auth_client(client)

    response = await client.get(f"/api/v1/tasks/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


@pytest.mark.anyio
async def test_get_foreign_task_returns_404(client: AsyncClient) -> None:
    """Чужая задача выглядит как TASK_NOT_FOUND."""
    await auth_client(client, login="owner", name="Owner")
    task = await create_task(client, {"title": "Личная"})

    await auth_client(client, login="other", name="Other")
    response = await client.get(f"/api/v1/tasks/{task['id']}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"
