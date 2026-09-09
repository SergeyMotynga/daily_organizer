"""Integration tests списка задач."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now
from backend.models.task import Task


def titles(payload: dict[str, object]) -> list[str]:
    """Возвращает названия задач из ответа списка."""
    items = payload["items"]
    assert isinstance(items, list)
    return [item["title"] for item in items]


@pytest.mark.anyio
async def test_list_tasks_default_excludes_archived(client: AsyncClient) -> None:
    """Обычный список исключает задачи с archived_at."""
    await auth_client(client)
    await create_task(client, {"title": "Активная"})
    await create_task(client, {"title": "Выполненная", "status": "done"})
    archived = await create_task(client, {"title": "Архивная"})
    archive_response = await client.patch(
        f"/api/v1/tasks/{archived['id']}",
        json={"archived": True},
    )
    assert archive_response.status_code == 200

    response = await client.get("/api/v1/tasks")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 2
    assert {item["status"] for item in payload["items"]} == {"todo", "done"}


@pytest.mark.anyio
async def test_list_tasks_filters_multiple_statuses(client: AsyncClient) -> None:
    """Фильтр statuses поддерживает несколько значений."""
    await auth_client(client)
    await create_task(client, {"title": "Активная"})
    await create_task(client, {"title": "Выполненная", "status": "done"})

    response = await client.get("/api/v1/tasks?statuses=todo,done")

    assert response.status_code == 200
    assert {item["status"] for item in response.json()["items"]} == {"todo", "done"}


@pytest.mark.anyio
async def test_list_archived_tasks_preserves_execution_statuses(client: AsyncClient) -> None:
    """Архивный список возвращает todo и done по archived_at."""
    await auth_client(client)
    todo_task = await create_task(client, {"title": "Архивная активная"})
    done_task = await create_task(
        client,
        {"title": "Архивная выполненная", "status": "done"},
    )
    await create_task(client, {"title": "Обычная"})

    for task in (todo_task, done_task):
        response = await client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"archived": True},
        )
        assert response.status_code == 200

    response = await client.get("/api/v1/tasks?archived=true&statuses=todo,done")

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["title"] for item in items} == {"Архивная активная", "Архивная выполненная"}
    assert {item["status"] for item in items} == {"todo", "done"}
    assert all(item["archived_at"] is not None for item in items)


@pytest.mark.anyio
async def test_list_tasks_rejects_archived_status_filter(client: AsyncClient) -> None:
    """Фильтр statuses не принимает archived."""
    await auth_client(client)

    response = await client.get("/api/v1/tasks?statuses=archived")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_list_tasks_rejects_unknown_status_filter(client: AsyncClient) -> None:
    """Фильтр statuses с неизвестным значением возвращает validation error."""
    await auth_client(client)

    response = await client.get("/api/v1/tasks?statuses=todo,unknown")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_list_tasks_filters_by_dates(client: AsyncClient) -> None:
    """Список фильтруется по planned_date и deadline_date."""
    await auth_client(client)
    await create_task(
        client,
        {"title": "Первая", "planned_date": "2026-09-05", "deadline_date": "2026-09-10"},
    )
    await create_task(
        client,
        {"title": "Вторая", "planned_date": "2026-09-06", "deadline_date": "2026-09-11"},
    )

    planned_response = await client.get("/api/v1/tasks?planned_date=2026-09-05")
    deadline_response = await client.get("/api/v1/tasks?deadline_date=2026-09-11")

    assert planned_response.status_code == 200
    assert titles(planned_response.json()) == ["Первая"]
    assert deadline_response.status_code == 200
    assert titles(deadline_response.json()) == ["Вторая"]


@pytest.mark.anyio
async def test_list_tasks_searches_title_and_description(client: AsyncClient) -> None:
    """Поиск q ищет по названию и описанию без учета регистра."""
    await auth_client(client)
    await create_task(client, {"title": "Купить молоко"})
    await create_task(client, {"title": "Документы", "description": "Prepare paper report"})
    await create_task(client, {"title": "Звонок"})

    title_response = await client.get("/api/v1/tasks?q=МОЛОКО")
    description_response = await client.get("/api/v1/tasks?q=paper")
    empty_response = await client.get("/api/v1/tasks?q=   ")

    assert title_response.status_code == 200
    assert titles(title_response.json()) == ["Купить молоко"]
    assert description_response.status_code == 200
    assert titles(description_response.json()) == ["Документы"]
    assert empty_response.status_code == 200
    assert empty_response.json()["pagination"]["total"] == 3


@pytest.mark.anyio
async def test_list_tasks_paginates(client: AsyncClient) -> None:
    """Список возвращает limit, offset и total."""
    await auth_client(client)
    await create_task(client, {"title": "Первая"})
    await create_task(client, {"title": "Вторая"})
    await create_task(client, {"title": "Третья"})

    response = await client.get("/api/v1/tasks?limit=2&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert payload["pagination"] == {"limit": 2, "offset": 1, "total": 3}


@pytest.mark.anyio
async def test_list_tasks_sorts_by_dates(client: AsyncClient) -> None:
    """Список поддерживает сортировки по planned_date и deadline_date."""
    await auth_client(client)
    await create_task(
        client,
        {"title": "Позже", "planned_date": "2026-09-07", "deadline_date": "2026-09-12"},
    )
    await create_task(
        client,
        {"title": "Раньше", "planned_date": "2026-09-05", "deadline_date": "2026-09-10"},
    )

    planned_response = await client.get("/api/v1/tasks?sort=planned_date_asc")
    deadline_response = await client.get("/api/v1/tasks?sort=deadline_date_asc")

    assert planned_response.status_code == 200
    assert titles(planned_response.json()) == ["Раньше", "Позже"]
    assert deadline_response.status_code == 200
    assert titles(deadline_response.json()) == ["Раньше", "Позже"]


@pytest.mark.anyio
async def test_list_tasks_sorts_planned_time_within_date_nulls_last(
    client: AsyncClient,
) -> None:
    """Сортировка по плановой дате учитывает время и ставит null в конец даты."""
    await auth_client(client)
    await create_task(
        client,
        {"title": "Без времени", "planned_date": "2026-09-05"},
    )
    await create_task(
        client,
        {"title": "Позднее время", "planned_date": "2026-09-05", "planned_time": "18:00"},
    )
    await create_task(
        client,
        {"title": "Раннее время", "planned_date": "2026-09-05", "planned_time": "09:00"},
    )
    await create_task(
        client,
        {"title": "Следующий день", "planned_date": "2026-09-06", "planned_time": "08:00"},
    )

    response = await client.get("/api/v1/tasks?sort=planned_date_asc")

    assert response.status_code == 200
    assert titles(response.json()) == [
        "Раннее время",
        "Позднее время",
        "Без времени",
        "Следующий день",
    ]


@pytest.mark.anyio
async def test_list_tasks_sorts_by_created_at(
    client: AsyncClient,
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Список поддерживает сортировки по created_at."""
    await auth_client(client)
    first = await create_task(client, {"title": "Первая"})
    second = await create_task(client, {"title": "Вторая"})

    async with test_sessionmaker() as db:
        await db.execute(
            update(Task)
            .where(Task.id == first["id"])
            .values(created_at=datetime(2026, 9, 1, tzinfo=UTC))
        )
        await db.execute(
            update(Task)
            .where(Task.id == second["id"])
            .values(created_at=datetime(2026, 9, 2, tzinfo=UTC))
        )
        await db.commit()

    asc_response = await client.get("/api/v1/tasks?sort=created_at_asc")
    desc_response = await client.get("/api/v1/tasks?sort=created_at_desc")

    assert asc_response.status_code == 200
    assert titles(asc_response.json()) == ["Первая", "Вторая"]
    assert desc_response.status_code == 200
    assert titles(desc_response.json()) == ["Вторая", "Первая"]


@pytest.mark.anyio
async def test_list_tasks_applies_presets(client: AsyncClient) -> None:
    """Список применяет продуктовые пресеты planned_date."""
    await auth_client(client)
    today = utc_now().date()
    tomorrow = today + timedelta(days=1)
    week_last_day = today + timedelta(days=6)
    later = today + timedelta(days=7)

    await create_task(client, {"title": "Сегодня", "planned_date": today.isoformat()})
    await create_task(client, {"title": "Завтра", "planned_date": tomorrow.isoformat()})
    await create_task(client, {"title": "Неделя", "planned_date": week_last_day.isoformat()})
    await create_task(client, {"title": "Потом", "planned_date": later.isoformat()})
    await create_task(client, {"title": "Без даты"})

    today_response = await client.get("/api/v1/tasks?preset=today")
    tomorrow_response = await client.get("/api/v1/tasks?preset=tomorrow")
    week_response = await client.get("/api/v1/tasks?preset=week")
    no_date_response = await client.get("/api/v1/tasks?preset=no_date")

    assert today_response.status_code == 200
    assert titles(today_response.json()) == ["Сегодня"]
    assert tomorrow_response.status_code == 200
    assert titles(tomorrow_response.json()) == ["Завтра"]
    assert week_response.status_code == 200
    assert set(titles(week_response.json())) == {"Сегодня", "Завтра", "Неделя"}
    assert no_date_response.status_code == 200
    assert titles(no_date_response.json()) == ["Без даты"]
