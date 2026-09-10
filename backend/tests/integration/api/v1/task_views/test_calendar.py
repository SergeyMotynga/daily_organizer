"""Integration tests календарного представления задач."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.tasks.helpers import auth_client, create_task


def calendar_titles(payload: dict[str, object], group: str) -> list[str]:
    """Возвращает названия задач из календарной группы."""
    items = payload[group]
    assert isinstance(items, list)
    return [item["task"]["title"] for item in items]


@pytest.mark.anyio
async def test_calendar_returns_range_items_and_recurrence_completions(
    client: AsyncClient,
) -> None:
    """Календарь собирает план, дедлайны и occurrence без N+1 API-запросов."""
    await auth_client(client)
    await create_task(client, {"title": "План", "planned_date": "2026-09-10"})
    await create_task(client, {"title": "Дедлайн", "deadline_date": "2026-09-11"})
    await create_task(client, {"title": "Вне диапазона", "planned_date": "2026-10-01"})
    archived = await create_task(
        client,
        {"title": "В архиве", "planned_date": "2026-09-10"},
    )
    await client.patch(f"/api/v1/tasks/{archived['id']}", json={"archived": True})
    recurring = await create_task(
        client,
        {
            "title": "Каждый день",
            "recurrence_type_code": "daily",
            "recurrence_start_date": "2026-09-10",
            "recurrence_end_date": "2026-09-12",
        },
    )
    completion = await client.put(
        f"/api/v1/tasks/{recurring['id']}/recurrence-completions/2026-09-11"
    )
    assert completion.status_code == 201

    response = await client.get(
        "/api/v1/calendar",
        params={"date_from": "2026-09-10", "date_to": "2026-09-12"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["date_from"] == "2026-09-10"
    assert payload["date_to"] == "2026-09-12"
    assert calendar_titles(payload, "planned") == ["План"]
    assert calendar_titles(payload, "deadlines") == ["Дедлайн"]
    assert calendar_titles(payload, "recurrences") == ["Каждый день"] * 3
    assert [item["occurrence_date"] for item in payload["recurrences"]] == [
        "2026-09-10",
        "2026-09-11",
        "2026-09-12",
    ]
    assert [item["status"] for item in payload["recurrences"]] == ["todo", "done", "todo"]
    assert "status" not in payload["recurrences"][0]["task"]
    assert "occurrence_date" not in payload["recurrences"][0]["task"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("date_from", "date_to"),
    [
        ("2026-09-12", "2026-09-10"),
        ("2026-09-01", "2026-10-13"),
    ],
)
async def test_calendar_rejects_invalid_range(
    client: AsyncClient,
    date_from: str,
    date_to: str,
) -> None:
    """Неверный календарный диапазон возвращает доменную ошибку 422."""
    await auth_client(client)

    response = await client.get(
        "/api/v1/calendar",
        params={"date_from": date_from, "date_to": date_to},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CALENDAR_RANGE"
