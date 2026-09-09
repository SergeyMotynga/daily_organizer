"""Интеграционные тесты блоков экрана Сегодня."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.task_views.helpers import block_titles, regular_block_ids
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now


@pytest.mark.anyio
async def test_today_view_groups_tasks_by_blocks(client: AsyncClient) -> None:
    """Экран Сегодня раскладывает активные задачи по основным блокам."""
    await auth_client(client)
    today = utc_now().date()

    planned = await create_task(
        client,
        {"title": "Запланирована сегодня", "planned_date": today.isoformat()},
    )
    inbox = await create_task(client, {"title": "Входящая"})
    soon_deadline = await create_task(
        client,
        {"title": "Скоро дедлайн", "deadline_date": (today + timedelta(days=3)).isoformat()},
    )
    today_deadline = await create_task(
        client,
        {"title": "Дедлайн сегодня", "deadline_date": today.isoformat()},
    )
    overdue = await create_task(
        client,
        {"title": "Просрочена", "deadline_date": (today - timedelta(days=1)).isoformat()},
    )

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == today.isoformat()
    assert block_titles(payload, "planned_today") == ["Запланирована сегодня"]
    assert block_titles(payload, "inbox") == ["Входящая"]
    assert block_titles(payload, "soon_deadline") == ["Скоро дедлайн"]
    assert block_titles(payload, "today_deadline") == ["Дедлайн сегодня"]
    assert block_titles(payload, "overdue") == ["Просрочена"]
    assert set(regular_block_ids(payload)) == {
        planned["id"],
        inbox["id"],
        soon_deadline["id"],
        today_deadline["id"],
        overdue["id"],
    }


@pytest.mark.anyio
async def test_planned_tasks_are_also_visible_in_attention_blocks(
    client: AsyncClient,
) -> None:
    """План на сегодня сохраняет задачи, которые также требуют внимания."""
    await auth_client(client)
    today = utc_now().date()
    await create_task(
        client,
        {
            "title": "Запланирована с дедлайном сегодня",
            "planned_date": today.isoformat(),
            "deadline_date": today.isoformat(),
        },
    )
    await create_task(
        client,
        {
            "title": "Запланирована просроченная",
            "planned_date": today.isoformat(),
            "deadline_date": (today - timedelta(days=1)).isoformat(),
        },
    )

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    payload = response.json()
    assert block_titles(payload, "planned_today") == [
        "Запланирована просроченная",
        "Запланирована с дедлайном сегодня",
    ]
    assert block_titles(payload, "today_deadline") == ["Запланирована с дедлайном сегодня"]
    assert block_titles(payload, "overdue") == ["Запланирована просроченная"]
    for block_name in ("planned_today", "today_deadline", "overdue"):
        block_ids = [task["id"] for task in payload["blocks"][block_name]]
        assert len(block_ids) == len(set(block_ids))
    assert payload["summary"]["total_active"] == 2
