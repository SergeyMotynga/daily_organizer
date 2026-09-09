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
async def test_create_task_with_planned_time(client: AsyncClient) -> None:
    """Создание задачи принимает и возвращает плановое время в формате HH:MM."""
    await auth_client(client)

    task = await create_task(
        client,
        {"title": "Встреча", "planned_date": "2026-09-10", "planned_time": "10:30"},
    )

    assert task["planned_date"] == "2026-09-10"
    assert task["planned_time"] == "10:30"


@pytest.mark.anyio
async def test_create_task_with_deadline_time_and_recurrence(client: AsyncClient) -> None:
    """Создание возвращает время дедлайна и проверенное правило повторения."""
    await auth_client(client)

    task = await create_task(
        client,
        {
            "title": "Повторяющаяся задача",
            "deadline_date": "2026-09-10",
            "deadline_time": "18:30",
            "recurrence_type_code": "daily",
            "recurrence_interval": 3,
            "recurrence_start_date": "2026-09-01",
            "recurrence_end_date": "2026-10-01",
        },
    )

    assert task["deadline_time"] == "18:30"
    assert task["recurrence_type_code"] == "daily"
    assert task["recurrence_interval"] == 3
    assert task["recurrence_start_date"] == "2026-09-01"
    assert task["recurrence_end_date"] == "2026-10-01"
    assert task["status"] == "todo"


@pytest.mark.anyio
async def test_create_task_rejects_deadline_time_without_date(client: AsyncClient) -> None:
    """Время дедлайна без даты возвращает validation error."""
    await auth_client(client)

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Некорректный дедлайн", "deadline_time": "10:30"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        (
            {
                "title": "Без даты старта",
                "recurrence_type_code": "daily",
                "recurrence_interval": 1,
            },
            400,
        ),
        (
            {
                "title": "Нулевой интервал",
                "recurrence_type_code": "daily",
                "recurrence_interval": 0,
                "recurrence_start_date": "2026-09-01",
            },
            422,
        ),
        (
            {
                "title": "Будни с интервалом",
                "recurrence_type_code": "weekdays",
                "recurrence_interval": 2,
                "recurrence_start_date": "2026-09-01",
            },
            400,
        ),
        (
            {"title": "Неизвестный тип", "recurrence_type_code": "monthly"},
            422,
        ),
    ],
)
async def test_create_task_validates_recurrence(
    client: AsyncClient,
    payload: dict[str, Any],
    expected_status: int,
) -> None:
    """Создание проверяет тип, интервал и дату старта повторения."""
    await auth_client(client)

    response = await client.post("/api/v1/tasks", json=payload)

    assert response.status_code == expected_status


@pytest.mark.anyio
async def test_create_task_rejects_planned_time_with_seconds(client: AsyncClient) -> None:
    """Создание задачи отклоняет время не в формате HH:MM."""
    await auth_client(client)

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Встреча", "planned_time": "10:30:00"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


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
async def test_create_task_rejects_archived_status(client: AsyncClient) -> None:
    """Создание задачи не принимает архивацию как статус выполнения."""
    await auth_client(client)

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Архивная", "status": "archived"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


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
