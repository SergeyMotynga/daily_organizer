"""Интеграционные тесты дедлайнов экрана Сегодня."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.task_views.helpers import block_titles
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now


@pytest.mark.anyio
async def test_today_deadline_has_priority_over_inbox(client: AsyncClient) -> None:
    """Задача без planned_date и с дедлайном сегодня попадает не во Входящие."""
    await auth_client(client)
    today = utc_now().date()
    await create_task(
        client,
        {"title": "Без плана с дедлайном сегодня", "deadline_date": today.isoformat()},
    )

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    payload = response.json()
    assert block_titles(payload, "today_deadline") == ["Без плана с дедлайном сегодня"]
    assert block_titles(payload, "inbox") == []


@pytest.mark.anyio
async def test_soon_deadline_includes_next_three_days_without_today(
    client: AsyncClient,
) -> None:
    """Блок soon_deadline берет следующие 3 дня без сегодня и просрочки."""
    await auth_client(client)
    today = utc_now().date()
    await create_task(
        client,
        {"title": "Дедлайн завтра", "deadline_date": (today + timedelta(days=1)).isoformat()},
    )
    await create_task(
        client,
        {
            "title": "Дедлайн через три дня",
            "deadline_date": (today + timedelta(days=3)).isoformat(),
        },
    )
    await create_task(
        client,
        {
            "title": "Дедлайн через четыре дня",
            "deadline_date": (today + timedelta(days=4)).isoformat(),
        },
    )
    await create_task(
        client,
        {"title": "Дедлайн сегодня", "deadline_date": today.isoformat()},
    )
    await create_task(
        client,
        {"title": "Просрочена", "deadline_date": (today - timedelta(days=1)).isoformat()},
    )

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    payload = response.json()
    assert block_titles(payload, "soon_deadline") == [
        "Дедлайн завтра",
        "Дедлайн через три дня",
    ]
    assert block_titles(payload, "today_deadline") == ["Дедлайн сегодня"]
    assert block_titles(payload, "overdue") == ["Просрочена"]
    assert block_titles(payload, "inbox") == ["Дедлайн через четыре дня"]
