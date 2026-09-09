"""Integration tests справочника типов повторения задач."""

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.integration.api.v1.tasks.helpers import auth_client

from backend.models.task import TaskRecurrenceType


@pytest.mark.anyio
async def test_list_task_recurrence_types_returns_active_reference(
    client: AsyncClient,
) -> None:
    """Endpoint возвращает типы повторения в системном порядке."""
    await auth_client(client)

    response = await client.get("/api/v1/task-recurrence-types")

    assert response.status_code == 200
    assert response.json() == [
        {"code": "none", "title": "Не повторять", "sort_order": 10},
        {"code": "daily", "title": "По дням", "sort_order": 20},
        {"code": "weekdays", "title": "По будням", "sort_order": 30},
        {"code": "weekly", "title": "По неделям", "sort_order": 40},
    ]


@pytest.mark.anyio
async def test_list_task_recurrence_types_requires_auth(client: AsyncClient) -> None:
    """Справочник не доступен без авторизации."""
    response = await client.get("/api/v1/task-recurrence-types")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_task_rejects_inactive_recurrence_type(
    client: AsyncClient,
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Task service проверяет тип повторения через активный справочник."""
    await auth_client(client)
    async with test_sessionmaker() as db:
        await db.execute(
            update(TaskRecurrenceType)
            .where(TaskRecurrenceType.code == "daily")
            .values(is_active=False)
        )
        await db.commit()

    try:
        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Отключенное повторение",
                "recurrence_type_code": "daily",
                "recurrence_start_date": "2026-09-10",
            },
        )
    finally:
        async with test_sessionmaker() as db:
            await db.execute(
                update(TaskRecurrenceType)
                .where(TaskRecurrenceType.code == "daily")
                .values(is_active=True)
            )
            await db.commit()

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TASK_RECURRENCE_TYPE_NOT_FOUND"
