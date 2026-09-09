"""Интеграционные тесты сводки экрана Сегодня."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.task_views.helpers import regular_block_ids
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now


@pytest.mark.anyio
async def test_today_view_summary_counts_visible_tasks(client: AsyncClient) -> None:
    """Сводка экрана Сегодня считает активные задачи и ключевые блоки."""
    await auth_client(client)
    today = utc_now().date()
    await create_task(client, {"title": "Запланирована", "planned_date": today.isoformat()})
    await create_task(client, {"title": "Входящая"})
    await create_task(
        client,
        {"title": "Дедлайн сегодня", "deadline_date": today.isoformat()},
    )
    await create_task(
        client,
        {"title": "Просрочена", "deadline_date": (today - timedelta(days=1)).isoformat()},
    )
    await create_task(client, {"title": "Выполнена сегодня", "status": "done"})

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    assert response.json()["summary"] == {
        "total_active": 4,
        "done_today": 1,
        "overdue": 1,
        "today_deadline": 1,
    }


@pytest.mark.anyio
async def test_today_view_excludes_archived_tasks(client: AsyncClient) -> None:
    """Экран Сегодня не возвращает архивные задачи в блоках и сводке."""
    await auth_client(client)
    today = utc_now().date()
    archived_todo = await create_task(
        client,
        {
            "title": "Архивная активная с датами",
            "planned_date": today.isoformat(),
            "deadline_date": today.isoformat(),
        },
    )
    archived_done = await create_task(
        client,
        {"title": "Архивная выполненная", "status": "done"},
    )
    for task in (archived_todo, archived_done):
        archive_response = await client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"archived": True},
        )
        assert archive_response.status_code == 200

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    payload = response.json()
    assert archived_todo["id"] not in regular_block_ids(payload)
    assert archived_done["id"] not in regular_block_ids(payload)
    assert payload["blocks"]["done_today"] == []
    assert payload["summary"] == {
        "total_active": 0,
        "done_today": 0,
        "overdue": 0,
        "today_deadline": 0,
    }
