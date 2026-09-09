"""Integration tests повторяющихся задач экрана Сегодня."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.task_views.helpers import block_ids, block_titles
from tests.integration.api.v1.tasks.helpers import auth_client, create_task


@pytest.mark.anyio
async def test_daily_recurrence_completion_is_scoped_to_occurrence_date(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Daily completion закрывает только выбранный день и снимается отдельным API."""
    await auth_client(client)
    first_day = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("backend.services.tasks.utc_now", lambda: first_day)
    task = await create_task(
        client,
        {
            "title": "Ежедневная",
            "recurrence_type_code": "daily",
            "recurrence_interval": 1,
            "recurrence_start_date": "2026-09-10",
        },
    )

    initial_view = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    assert initial_view.status_code == 200
    initial_task = initial_view.json()["blocks"]["planned_today"][0]
    assert initial_task["status"] == "todo"
    assert initial_task["occurrence_date"] == "2026-09-10"

    complete_response = await client.put(
        f"/api/v1/tasks/{task['id']}/recurrence-completions/2026-09-10"
    )
    assert complete_response.status_code == 201

    completed_view = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    assert block_titles(completed_view.json(), "planned_today") == []
    completed_task = completed_view.json()["blocks"]["done_today"][0]
    assert completed_task["status"] == "done"
    assert completed_task["occurrence_date"] == "2026-09-10"

    stored_task = await client.get(f"/api/v1/tasks/{task['id']}")
    assert stored_task.json()["status"] == "todo"
    assert stored_task.json()["completed_at"] is None

    uncomplete_response = await client.delete(
        f"/api/v1/tasks/{task['id']}/recurrence-completions/2026-09-10"
    )
    assert uncomplete_response.status_code == 204
    restored_view = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    assert block_titles(restored_view.json(), "planned_today") == ["Ежедневная"]

    next_day = datetime(2026, 9, 11, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("backend.services.tasks.utc_now", lambda: next_day)
    next_view = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    next_task = next_view.json()["blocks"]["planned_today"][0]
    assert next_task["status"] == "todo"
    assert next_task["occurrence_date"] == "2026-09-11"


@pytest.mark.anyio
async def test_weekdays_recurrence_is_hidden_on_weekend(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Повторение по будням не создает occurrence в субботу."""
    await auth_client(client)
    saturday = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("backend.services.tasks.utc_now", lambda: saturday)
    task = await create_task(
        client,
        {
            "title": "Только будни",
            "recurrence_type_code": "weekdays",
            "recurrence_interval": 1,
            "recurrence_start_date": "2026-09-07",
        },
    )

    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 200
    assert all(
        task["id"] not in block_ids(response.json(), block_name)
        for block_name in response.json()["blocks"]
    )


@pytest.mark.anyio
async def test_weekly_interval_and_archive_control_today_visibility(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Weekly interval выбирает нужную неделю, а архив скрывает правило из Today."""
    await auth_client(client)
    skipped_week = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("backend.services.tasks.utc_now", lambda: skipped_week)
    task = await create_task(
        client,
        {
            "title": "Раз в две недели",
            "recurrence_type_code": "weekly",
            "recurrence_interval": 2,
            "recurrence_start_date": "2026-09-03",
        },
    )

    skipped_response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    assert block_titles(skipped_response.json(), "planned_today") == []

    due_week = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("backend.services.tasks.utc_now", lambda: due_week)
    due_response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    assert block_titles(due_response.json(), "planned_today") == ["Раз в две недели"]

    archive_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"archived": True},
    )
    assert archive_response.status_code == 200
    archived_view = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})
    assert block_titles(archived_view.json(), "planned_today") == []
