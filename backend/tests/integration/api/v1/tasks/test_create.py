"""Integration tests создания задач."""

from typing import Any

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.tasks.helpers import auth_client, create_task


@pytest.mark.anyio
async def test_create_task_without_status_uses_todo(client: AsyncClient) -> None:
    """Создание задачи без status ставит todo."""
    await auth_client(client)

    task = await create_task(client, {"title": "  Купить хлеб  ", "description": "  "})

    assert task["title"] == "Купить хлеб"
    assert task["description"] is None
    assert task["status"] == "todo"
    assert task["completed_at"] is None
    assert task["archived_at"] is None
    assert "status_code" not in task


@pytest.mark.anyio
async def test_create_task_accepts_todo_status(client: AsyncClient) -> None:
    """Создание задачи принимает status todo."""
    await auth_client(client)

    task = await create_task(client, {"title": "Активная", "status": "todo"})

    assert task["status"] == "todo"
    assert task["completed_at"] is None
    assert task["archived_at"] is None
    assert "status_code" not in task


@pytest.mark.anyio
async def test_create_task_with_done_status_sets_completed_at(client: AsyncClient) -> None:
    """Создание выполненной задачи сразу ставит completed_at."""
    await auth_client(client)

    task = await create_task(client, {"title": "Выполненная", "status": "done"})

    assert task["status"] == "done"
    assert task["completed_at"] is not None
    assert task["archived_at"] is None
    assert "status_code" not in task


@pytest.mark.anyio
async def test_create_task_with_archived_status_sets_archived_at(client: AsyncClient) -> None:
    """Создание архивной задачи сразу ставит archived_at."""
    await auth_client(client)

    task = await create_task(client, {"title": "Архивная", "status": "archived"})

    assert task["status"] == "archived"
    assert task["completed_at"] is None
    assert task["archived_at"] is not None
    assert "status_code" not in task


@pytest.mark.anyio
async def test_create_task_rejects_unknown_status(client: AsyncClient) -> None:
    """Создание задачи с неизвестным status возвращает validation error."""
    await auth_client(client)

    response = await client.post("/api/v1/tasks", json={"title": "Задача", "status": "unknown"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "a" * 256},
        {"title": None},
    ],
)
async def test_create_task_validates_title(
    client: AsyncClient,
    payload: dict[str, Any],
) -> None:
    """Создание задачи валидирует title."""
    await auth_client(client)

    response = await client.post("/api/v1/tasks", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
