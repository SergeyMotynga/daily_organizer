"""Интеграционные тесты пресетов дедлайна списка задач."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.tasks.helpers import auth_client, create_task

from backend.core.security import utc_now


def titles(payload: dict[str, object]) -> list[str]:
    """Возвращает названия задач из ответа списка."""
    items = payload["items"]
    assert isinstance(items, list)
    return [item["title"] for item in items]


@pytest.mark.anyio
async def test_list_tasks_applies_deadline_presets(client: AsyncClient) -> None:
    """Deadline preset разделяет просроченные, сегодняшние и ближайшие задачи."""
    await auth_client(client)
    today = utc_now().date()

    await create_task(
        client,
        {"title": "Просрочена", "deadline_date": (today - timedelta(days=1)).isoformat()},
    )
    await create_task(client, {"title": "Сегодня", "deadline_date": today.isoformat()})
    await create_task(
        client,
        {"title": "Завтра", "deadline_date": (today + timedelta(days=1)).isoformat()},
    )
    await create_task(
        client,
        {"title": "Через три дня", "deadline_date": (today + timedelta(days=3)).isoformat()},
    )
    await create_task(
        client,
        {"title": "Позже", "deadline_date": (today + timedelta(days=4)).isoformat()},
    )
    await create_task(
        client,
        {
            "title": "Выполненная просроченная",
            "deadline_date": (today - timedelta(days=1)).isoformat(),
            "status": "done",
        },
    )

    overdue = await client.get("/api/v1/tasks?deadline_preset=overdue&timezone=UTC")
    today_response = await client.get("/api/v1/tasks?deadline_preset=today&timezone=UTC")
    soon = await client.get("/api/v1/tasks?deadline_preset=soon&timezone=UTC")

    assert overdue.status_code == 200
    assert titles(overdue.json()) == ["Просрочена"]
    assert today_response.status_code == 200
    assert titles(today_response.json()) == ["Сегодня"]
    assert soon.status_code == 200
    assert set(titles(soon.json())) == {"Завтра", "Через три дня"}


@pytest.mark.anyio
async def test_overdue_preset_uses_deadline_time_today(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Просрочка сегодня учитывает время, а дедлайн без времени ждет конца дня."""
    await auth_client(client)
    fixed_now = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    monkeypatch.setattr("backend.services.tasks.utc_now", lambda: fixed_now)

    await create_task(
        client,
        {"title": "Время прошло", "deadline_date": "2026-09-10", "deadline_time": "11:00"},
    )
    await create_task(
        client,
        {"title": "Время впереди", "deadline_date": "2026-09-10", "deadline_time": "13:00"},
    )
    await create_task(client, {"title": "Без времени", "deadline_date": "2026-09-10"})

    overdue = await client.get("/api/v1/tasks?deadline_preset=overdue&timezone=UTC")
    today_response = await client.get("/api/v1/tasks?deadline_preset=today&timezone=UTC")

    assert overdue.status_code == 200
    assert titles(overdue.json()) == ["Время прошло"]
    assert today_response.status_code == 200
    assert set(titles(today_response.json())) == {
        "Время прошло",
        "Время впереди",
        "Без времени",
    }


@pytest.mark.anyio
async def test_deadline_preset_uses_user_timezone(client: AsyncClient) -> None:
    """Deadline preset считает today по локальной дате пользователя."""
    await auth_client(client)
    now = utc_now()
    timezone_name = "Pacific/Kiritimati"
    timezone = ZoneInfo(timezone_name)
    if now.astimezone(timezone).date() == now.date():
        timezone_name = "Pacific/Pago_Pago"
        timezone = ZoneInfo(timezone_name)
    local_today = now.astimezone(timezone).date()
    assert local_today != now.date()

    await create_task(
        client,
        {"title": "Локальный дедлайн", "deadline_date": local_today.isoformat()},
    )

    response = await client.get(
        "/api/v1/tasks",
        params={"deadline_preset": "today", "timezone": timezone_name},
    )

    assert response.status_code == 200
    assert titles(response.json()) == ["Локальный дедлайн"]


@pytest.mark.anyio
async def test_exact_deadline_date_has_priority_over_preset(client: AsyncClient) -> None:
    """Точная дата дедлайна сохраняет приоритет над deadline preset."""
    await auth_client(client)
    target = utc_now().date() + timedelta(days=10)
    await create_task(
        client,
        {"title": "Точная дата", "deadline_date": target.isoformat(), "status": "done"},
    )

    response = await client.get(
        "/api/v1/tasks",
        params={
            "deadline_preset": "overdue",
            "deadline_date": target.isoformat(),
            "statuses": "done",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 200
    assert titles(response.json()) == ["Точная дата"]


@pytest.mark.anyio
async def test_list_tasks_rejects_invalid_deadline_preset_and_timezone(
    client: AsyncClient,
) -> None:
    """Некорректные deadline preset и timezone возвращают ожидаемые ошибки."""
    await auth_client(client)

    preset_response = await client.get("/api/v1/tasks?deadline_preset=unknown")
    timezone_response = await client.get(
        "/api/v1/tasks",
        params={"deadline_preset": "today", "timezone": "Invalid/Timezone"},
    )

    assert preset_response.status_code == 422
    assert preset_response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert timezone_response.status_code == 400
    assert timezone_response.json()["error"]["code"] == "INVALID_TIMEZONE"
