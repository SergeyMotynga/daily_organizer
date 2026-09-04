"""Integration tests удаления задач."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.models.task import Task


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
