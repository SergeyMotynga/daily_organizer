"""Интеграционные сценарии личных проектов."""

from typing import Any, cast

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.helpers import login_user, register_user


async def auth_client(client: AsyncClient) -> None:
    """Регистрирует основного пользователя и выполняет вход."""
    await register_user(client)
    await login_user(client)


async def create_project(
    client: AsyncClient,
    *,
    title: str = "Daily Organizer",
) -> dict[str, Any]:
    """Создает проект и возвращает JSON."""
    response = await client.post(
        "/api/v1/projects",
        json={"title": title, "description": "Разработка приложения"},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


@pytest.mark.anyio
async def test_project_crud_defaults_archive_and_restore(client: AsyncClient) -> None:
    """Проект создается со стандартными колонками и меняет архивное состояние."""
    await auth_client(client)
    project = await create_project(client)

    assert [item["title"] for item in project["columns"]] == [
        "Бэклог",
        "К выполнению",
        "В работе",
        "На проверке",
        "Готово",
    ]
    assert [item["position"] for item in project["columns"]] == list(range(5))
    assert [item["title"] for item in project["columns"] if item["is_completion_column"]] == [
        "Готово"
    ]

    archived = await client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"archived": True},
    )
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None
    assert (await client.get("/api/v1/projects")).json()["items"] == []
    assert len((await client.get("/api/v1/projects?archived=true")).json()["items"]) == 1

    restored = await client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"archived": False, "title": "Органайзер"},
    )
    assert restored.status_code == 200
    assert restored.json()["archived_at"] is None
    assert restored.json()["title"] == "Органайзер"


@pytest.mark.anyio
async def test_project_ownership_is_hidden(client: AsyncClient) -> None:
    """Другой пользователь не видит проект и его колонки."""
    await auth_client(client)
    project = await create_project(client)
    await register_user(client, login="other", name="Другой")
    await login_user(client, login="other")

    assert (await client.get(f"/api/v1/projects/{project['id']}")).status_code == 404
    assert (await client.get(f"/api/v1/projects/{project['id']}/columns")).status_code == 404


@pytest.mark.anyio
async def test_delete_project_detaches_tasks(client: AsyncClient) -> None:
    """Удаление проекта не удаляет связанные задачи."""
    await auth_client(client)
    project = await create_project(client)
    backlog = project["columns"][0]
    task_response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Проектная задача",
            "project_id": project["id"],
            "project_column_id": backlog["id"],
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    assert (await client.delete(f"/api/v1/projects/{project['id']}")).status_code == 204
    task = (await client.get(f"/api/v1/tasks/{task_id}")).json()
    assert task["project_id"] is None
    assert task["project_column_id"] is None
    assert task["project_position"] is None


@pytest.mark.anyio
async def test_columns_reorder_completion_and_nonempty_delete(client: AsyncClient) -> None:
    """Колонки нормализуются, completion меняется атомарно, непустая не удаляется."""
    await auth_client(client)
    project = await create_project(client)
    columns = project["columns"]
    backlog, done = columns[0], columns[-1]
    created_column = await client.post(
        f"/api/v1/projects/{project['id']}/columns",
        json={"title": "Пауза"},
    )
    assert created_column.status_code == 201
    pause = created_column.json()

    order = [pause["id"], *[item["id"] for item in columns]]
    reordered = await client.put(
        f"/api/v1/projects/{project['id']}/columns/order",
        json={"column_ids": order},
    )
    assert reordered.status_code == 200
    assert [item["position"] for item in reordered.json()] == list(range(6))

    completion = await client.patch(
        f"/api/v1/projects/{project['id']}/columns/{pause['id']}",
        json={"is_completion_column": True},
    )
    assert completion.status_code == 200
    latest = (await client.get(f"/api/v1/projects/{project['id']}/columns")).json()
    assert [item["id"] for item in latest if item["is_completion_column"]] == [pause["id"]]
    assert (
        next(item for item in latest if item["id"] == done["id"])["is_completion_column"] is False
    )

    task = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Задача",
            "project_id": project["id"],
            "project_column_id": backlog["id"],
        },
    )
    assert task.status_code == 201
    blocked = await client.delete(f"/api/v1/projects/{project['id']}/columns/{backlog['id']}")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "PROJECT_COLUMN_NOT_EMPTY"


@pytest.mark.anyio
async def test_move_and_status_keep_column_in_sync(client: AsyncClient) -> None:
    """Kanban-перенос и обычный PATCH статуса синхронизируют обе характеристики."""
    await auth_client(client)
    project = await create_project(client)
    backlog, in_progress, done = (
        project["columns"][0],
        project["columns"][2],
        project["columns"][-1],
    )
    task = (
        await client.post(
            "/api/v1/tasks",
            json={"title": "Задача", "project_id": project["id"]},
        )
    ).json()
    second = (
        await client.post(
            "/api/v1/tasks",
            json={"title": "Вторая", "project_id": project["id"]},
        )
    ).json()
    assert task["project_column_id"] == backlog["id"]
    assert [task["project_position"], second["project_position"]] == [0, 1]

    moved = await client.post(
        f"/api/v1/tasks/{second['id']}/move",
        json={
            "project_id": project["id"],
            "target_column_id": in_progress["id"],
            "target_position": 0,
        },
    )
    assert moved.status_code == 200
    assert moved.json()["status"] == "todo"

    completed = await client.post(
        f"/api/v1/tasks/{second['id']}/move",
        json={
            "project_id": project["id"],
            "target_column_id": done["id"],
            "target_position": 0,
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "done"
    assert completed.json()["completed_at"] is not None

    reopened = await client.patch(f"/api/v1/tasks/{second['id']}", json={"status": "todo"})
    assert reopened.status_code == 200
    assert reopened.json()["project_column_id"] == backlog["id"]
    assert reopened.json()["completed_at"] is None


@pytest.mark.anyio
async def test_recurring_task_cannot_enter_completion_column(client: AsyncClient) -> None:
    """Recurring history остается отдельной, а карточка не уходит в completion column."""
    await auth_client(client)
    project = await create_project(client)
    done = project["columns"][-1]
    task = (
        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Повторение",
                "project_id": project["id"],
                "recurrence_type_code": "daily",
                "recurrence_start_date": "2026-09-18",
            },
        )
    ).json()
    completion = await client.put(f"/api/v1/tasks/{task['id']}/recurrence-completions/2026-09-18")
    assert completion.status_code == 201

    blocked = await client.post(
        f"/api/v1/tasks/{task['id']}/move",
        json={
            "project_id": project["id"],
            "target_column_id": done["id"],
            "target_position": 0,
        },
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "RECURRING_TASK_COMPLETION_COLUMN"
    unchanged = (await client.get(f"/api/v1/tasks/{task['id']}")).json()
    assert unchanged["project_column_id"] == project["columns"][0]["id"]
    assert unchanged["status"] == "todo"


@pytest.mark.anyio
async def test_project_list_aggregates_ignore_archived_tasks(client: AsyncClient) -> None:
    """Карточка проекта считает активные задачи и прогресс без отдельных запросов."""
    await auth_client(client)
    project = await create_project(client)
    done = project["columns"][-1]
    first = (
        await client.post(
            "/api/v1/tasks",
            json={"title": "Готово", "project_id": project["id"], "project_column_id": done["id"]},
        )
    ).json()
    second = (
        await client.post(
            "/api/v1/tasks",
            json={"title": "Активно", "project_id": project["id"]},
        )
    ).json()
    assert first["status"] == "done"
    await client.patch(f"/api/v1/tasks/{second['id']}", json={"archived": True})

    summary = (await client.get("/api/v1/projects")).json()["items"][0]
    assert summary["task_count"] == 1
    assert summary["completed_task_count"] == 1
    assert summary["progress_percent"] == 100
