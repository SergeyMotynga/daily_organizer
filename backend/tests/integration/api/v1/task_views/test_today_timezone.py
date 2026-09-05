"""Интеграционные тесты таймзоны экрана Сегодня."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.integration.api.v1.task_views.helpers import block_titles
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now
from backend.models.task import Task


@pytest.mark.anyio
async def test_today_view_rejects_invalid_timezone(client: AsyncClient) -> None:
    """Невалидная timezone возвращает доменную ошибку."""
    await auth_client(client)

    response = await client.get(
        "/api/v1/task-views/today",
        params={"timezone": "Invalid/Timezone"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TIMEZONE"


@pytest.mark.anyio
async def test_done_today_uses_user_local_day(
    client: AsyncClient,
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Блок done_today использует локальный день пользователя."""
    await auth_client(client)
    timezone = ZoneInfo("Asia/Omsk")
    today = utc_now().astimezone(timezone).date()
    included = await create_task(
        client,
        {"title": "Выполнена локально сегодня", "status": "done"},
    )
    before_local_day = await create_task(
        client,
        {"title": "Выполнена перед локальным днем", "status": "done"},
    )
    after_local_day = await create_task(
        client,
        {"title": "Выполнена после локального дня", "status": "done"},
    )

    async with test_sessionmaker() as db:
        await db.execute(
            update(Task)
            .where(Task.id == included["id"])
            .values(completed_at=_local_datetime_utc(today, time(hour=0, minute=30), timezone))
        )
        await db.execute(
            update(Task)
            .where(Task.id == before_local_day["id"])
            .values(
                completed_at=_local_datetime_utc(
                    today - timedelta(days=1),
                    time(hour=23, minute=30),
                    timezone,
                )
            )
        )
        await db.execute(
            update(Task)
            .where(Task.id == after_local_day["id"])
            .values(
                completed_at=_local_datetime_utc(
                    today + timedelta(days=1),
                    time(hour=0, minute=30),
                    timezone,
                )
            )
        )
        await db.commit()

    response = await client.get(
        "/api/v1/task-views/today",
        params={"timezone": "Asia/Omsk"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == today.isoformat()
    assert block_titles(payload, "done_today") == ["Выполнена локально сегодня"]
    assert payload["summary"]["done_today"] == 1


def _local_datetime_utc(day: date, day_time: time, timezone: ZoneInfo) -> datetime:
    """Переводит локальное время пользователя в UTC."""
    return datetime.combine(day, day_time, tzinfo=timezone).astimezone(UTC)
