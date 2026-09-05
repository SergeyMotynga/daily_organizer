"""Интеграционные тесты выполненных задач экрана Сегодня."""

from datetime import UTC, datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.integration.api.v1.task_views.helpers import block_titles
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now
from backend.models.task import Task


@pytest.mark.anyio
async def test_done_today_uses_completed_at_date(
    client: AsyncClient,
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Блок done_today строится по completed_at, а не по planned_date."""
    await auth_client(client)
    today = utc_now().date()
    today_completed = await create_task(
        client,
        {
            "title": "Выполнена сегодня без плана",
            "status": "done",
            "planned_date": (today + timedelta(days=1)).isoformat(),
        },
    )
    yesterday_completed = await create_task(
        client,
        {
            "title": "Выполнена вчера с планом сегодня",
            "status": "done",
            "planned_date": today.isoformat(),
        },
    )

    async with test_sessionmaker() as db:
        await db.execute(
            update(Task)
            .where(Task.id == today_completed["id"])
            .values(completed_at=datetime.combine(today, time(hour=12), tzinfo=UTC))
        )
        await db.execute(
            update(Task)
            .where(Task.id == yesterday_completed["id"])
            .values(
                completed_at=datetime.combine(
                    today - timedelta(days=1),
                    time(hour=23),
                    tzinfo=UTC,
                )
            )
        )
        await db.commit()

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    payload = response.json()
    assert block_titles(payload, "done_today") == ["Выполнена сегодня без плана"]
    assert block_titles(payload, "planned_today") == []
