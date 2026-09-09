"""Integration tests удаления задач."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now
from backend.models.task import Task, TaskRecurrenceCompletion


@pytest.mark.anyio
async def test_delete_task_removes_row_physically(
    client: AsyncClient,
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """DELETE физически удаляет задачу из БД."""
    await auth_client(client)
    task = await create_task(client)

    response = await client.delete(f"/api/v1/tasks/{task['id']}")

    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/tasks/{task['id']}")
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "TASK_NOT_FOUND"

    async with test_sessionmaker() as db:
        count = await db.scalar(select(func.count()).select_from(Task).where(Task.id == task["id"]))

    assert count == 0


@pytest.mark.anyio
async def test_delete_recurring_task_cascades_completion_history(
    client: AsyncClient,
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """DELETE recurring task физически удаляет ее completion history."""
    await auth_client(client)
    today = utc_now().date()
    task = await create_task(
        client,
        {
            "title": "Повторение",
            "recurrence_type_code": "daily",
            "recurrence_start_date": today.isoformat(),
        },
    )
    complete_response = await client.put(
        f"/api/v1/tasks/{task['id']}/recurrence-completions/{today.isoformat()}"
    )
    assert complete_response.status_code == 201

    response = await client.delete(f"/api/v1/tasks/{task['id']}")

    assert response.status_code == 204
    async with test_sessionmaker() as db:
        completion_count = await db.scalar(
            select(func.count())
            .select_from(TaskRecurrenceCompletion)
            .where(TaskRecurrenceCompletion.task_id == task["id"])
        )

    assert completion_count == 0
