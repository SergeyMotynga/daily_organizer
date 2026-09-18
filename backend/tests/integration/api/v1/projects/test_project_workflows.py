"""Расширенные интеграционные сценарии проектов и проектных задач."""

from typing import Any, cast
from uuid import uuid4

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.helpers import login_user, register_user


async def auth_client(client: AsyncClient) -> None:
    """Регистрирует пользователя и выполняет вход."""
    await register_user(client)
    await login_user(client)


async def create_project(client: AsyncClient, title: str = "Проект") -> dict[str, Any]:
    """Создает проект и возвращает публичное представление."""
    response = await client.post("/api/v1/projects", json={"title": title})
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


async def create_task(client: AsyncClient, **payload: Any) -> dict[str, Any]:
    """Создает задачу с обязательным названием по умолчанию."""
    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Задача", **payload},
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json())


@pytest.mark.anyio
async def test_project_search_update_and_missing_resource_errors(client: AsyncClient) -> None:
    """Поиск работает по названию и описанию, а чужие UUID скрыты за 404."""
    await auth_client(client)
    first = await create_project(client, "Домашний ремонт")
    second = await create_project(client, "Работа")
    updated = await client.patch(
        f"/api/v1/projects/{second['id']}",
        json={"description": "Ремонт релизного процесса"},
    )
    assert updated.status_code == 200

    by_title = (await client.get("/api/v1/projects?q=домашний")).json()["items"]
    by_description = (await client.get("/api/v1/projects?q=релизного")).json()["items"]
    assert [item["id"] for item in by_title] == [first["id"]]
    assert [item["id"] for item in by_description] == [second["id"]]

    missing_id = uuid4()
    assert (await client.get(f"/api/v1/projects/{missing_id}")).status_code == 404
    assert (await client.patch(f"/api/v1/projects/{missing_id}", json={})).status_code == 404
    assert (await client.delete(f"/api/v1/projects/{missing_id}")).status_code == 404


@pytest.mark.anyio
async def test_empty_column_lifecycle_and_completion_guards(client: AsyncClient) -> None:
    """Пустую колонку можно менять и удалять, завершающую — нельзя потерять."""
    await auth_client(client)
    project = await create_project(client)
    done = project["columns"][-1]

    created = await client.post(
        f"/api/v1/projects/{project['id']}/columns",
        json={"title": "  Ожидание  "},
    )
    assert created.status_code == 201
    column = created.json()
    assert column["title"] == "Ожидание"
    assert column["position"] == 5

    renamed = await client.patch(
        f"/api/v1/projects/{project['id']}/columns/{column['id']}",
        json={"title": "Пауза"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Пауза"

    cannot_unset = await client.patch(
        f"/api/v1/projects/{project['id']}/columns/{done['id']}",
        json={"is_completion_column": False},
    )
    cannot_delete = await client.delete(f"/api/v1/projects/{project['id']}/columns/{done['id']}")
    assert cannot_unset.status_code == 409
    assert cannot_delete.status_code == 409
    assert cannot_delete.json()["error"]["code"] == "PROJECT_COMPLETION_COLUMN_REQUIRED"

    deleted = await client.delete(f"/api/v1/projects/{project['id']}/columns/{column['id']}")
    assert deleted.status_code == 204
    columns = (await client.get(f"/api/v1/projects/{project['id']}/columns")).json()
    assert [item["position"] for item in columns] == list(range(5))

    invalid_order = await client.put(
        f"/api/v1/projects/{project['id']}/columns/order",
        json={"column_ids": [columns[0]["id"]]},
    )
    assert invalid_order.status_code == 400
    assert invalid_order.json()["error"]["code"] == "INVALID_PROJECT_COLUMN_ORDER"

    missing_column = uuid4()
    assert (
        await client.patch(
            f"/api/v1/projects/{project['id']}/columns/{missing_column}",
            json={"title": "Нет"},
        )
    ).status_code == 404


@pytest.mark.anyio
async def test_new_completion_column_reopens_old_completed_tasks(client: AsyncClient) -> None:
    """Смена завершающей колонки синхронизирует статусы задач старого этапа."""
    await auth_client(client)
    project = await create_project(client)
    old_done = project["columns"][-1]
    task = await create_task(
        client,
        project_id=project["id"],
        project_column_id=old_done["id"],
    )
    assert task["status"] == "done"

    response = await client.post(
        f"/api/v1/projects/{project['id']}/columns",
        json={"title": "Закрыто", "is_completion_column": True},
    )
    assert response.status_code == 201
    new_done = response.json()

    columns = (await client.get(f"/api/v1/projects/{project['id']}/columns")).json()
    assert [item["id"] for item in columns if item["is_completion_column"]] == [new_done["id"]]
    reopened = (await client.get(f"/api/v1/tasks/{task['id']}")).json()
    assert reopened["status"] == "todo"
    assert reopened["completed_at"] is None


@pytest.mark.anyio
async def test_completion_reassignment_synchronizes_both_columns(client: AsyncClient) -> None:
    """Назначение существующего этапа завершающим обновляет задачи обеих колонок."""
    await auth_client(client)
    project = await create_project(client)
    backlog, old_done = project["columns"][0], project["columns"][-1]
    active = await create_task(
        client,
        title="Активная",
        project_id=project["id"],
        project_column_id=backlog["id"],
    )
    completed = await create_task(
        client,
        title="Готовая",
        project_id=project["id"],
        project_column_id=old_done["id"],
    )

    response = await client.patch(
        f"/api/v1/projects/{project['id']}/columns/{backlog['id']}",
        json={"is_completion_column": True},
    )
    assert response.status_code == 200
    active_after = (await client.get(f"/api/v1/tasks/{active['id']}")).json()
    completed_after = (await client.get(f"/api/v1/tasks/{completed['id']}")).json()
    assert active_after["status"] == "done"
    assert active_after["completed_at"] is not None
    assert completed_after["status"] == "todo"
    assert completed_after["completed_at"] is None


@pytest.mark.anyio
async def test_move_inside_column_normalizes_positions_and_clamps_target(
    client: AsyncClient,
) -> None:
    """Перемещение внутри этапа не оставляет дублей или дыр в позициях."""
    await auth_client(client)
    project = await create_project(client)
    backlog = project["columns"][0]
    tasks = [
        await create_task(client, title=f"Задача {index}", project_id=project["id"])
        for index in range(3)
    ]

    moved = await client.post(
        f"/api/v1/tasks/{tasks[2]['id']}/move",
        json={
            "project_id": project["id"],
            "target_column_id": backlog["id"],
            "target_position": 0,
        },
    )
    assert moved.status_code == 200
    assert moved.json()["project_position"] == 0

    clamped = await client.post(
        f"/api/v1/tasks/{tasks[2]['id']}/move",
        json={
            "project_id": project["id"],
            "target_column_id": backlog["id"],
            "target_position": 99,
        },
    )
    assert clamped.status_code == 200
    positions = [
        (await client.get(f"/api/v1/tasks/{task['id']}")).json()["project_position"]
        for task in tasks
    ]
    assert sorted(positions) == [0, 1, 2]
    assert clamped.json()["project_position"] == 2


@pytest.mark.anyio
async def test_bulk_move_and_status_keep_tasks_consistent(client: AsyncClient) -> None:
    """Массовые операции синхронизируют этап, статус и позиции."""
    await auth_client(client)
    project = await create_project(client)
    backlog, in_progress, done = (
        project["columns"][0],
        project["columns"][2],
        project["columns"][-1],
    )
    first = await create_task(client, title="Первая", project_id=project["id"])
    second = await create_task(
        client,
        title="Вторая",
        project_id=project["id"],
        project_column_id=in_progress["id"],
    )

    completed = await client.post(
        f"/api/v1/projects/{project['id']}/tasks/bulk-move",
        json={"task_ids": [first["id"], second["id"]], "target_column_id": done["id"]},
    )
    assert completed.status_code == 200
    assert {item["status"] for item in completed.json()} == {"done"}
    assert sorted(item["project_position"] for item in completed.json()) == [0, 1]

    reopened = await client.post(
        f"/api/v1/projects/{project['id']}/tasks/bulk-status",
        json={"task_ids": [first["id"], second["id"]], "status": "todo"},
    )
    assert reopened.status_code == 200
    assert {item["project_column_id"] for item in reopened.json()} == {backlog["id"]}
    assert {item["status"] for item in reopened.json()} == {"todo"}

    invalid = await client.post(
        f"/api/v1/projects/{project['id']}/tasks/bulk-move",
        json={"task_ids": [first["id"], str(uuid4())], "target_column_id": done["id"]},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_TASK_PROJECT"


@pytest.mark.anyio
async def test_task_project_membership_validation_and_detach(client: AsyncClient) -> None:
    """PATCH задачи безопасно присоединяет, переносит и отвязывает ее от проекта."""
    await auth_client(client)
    first = await create_project(client, "Первый")
    second = await create_project(client, "Второй")
    task = await create_task(client)

    attached = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"project_id": first["id"]},
    )
    assert attached.status_code == 200
    assert attached.json()["project_column_id"] == first["columns"][0]["id"]
    assert attached.json()["project_position"] == 0

    mismatched = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "project_id": first["id"],
            "project_column_id": second["columns"][0]["id"],
        },
    )
    assert mismatched.status_code == 400

    missing_project = await client.post(
        "/api/v1/tasks",
        json={"title": "Нет проекта", "project_id": str(uuid4())},
    )
    assert missing_project.status_code == 404

    detached = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"project_id": None},
    )
    assert detached.status_code == 200
    assert detached.json()["project_id"] is None
    assert detached.json()["project_column_id"] is None
    assert detached.json()["project_position"] is None


@pytest.mark.anyio
async def test_recurring_project_guards_cover_create_update_and_bulk(client: AsyncClient) -> None:
    """Повторяющаяся задача не может оказаться в завершающем этапе любым путем."""
    await auth_client(client)
    project = await create_project(client)
    backlog, done = project["columns"][0], project["columns"][-1]

    rejected_create = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Повтор",
            "project_id": project["id"],
            "project_column_id": done["id"],
            "recurrence_type_code": "daily",
            "recurrence_start_date": "2026-09-18",
        },
    )
    assert rejected_create.status_code == 409

    completed = await create_task(
        client,
        project_id=project["id"],
        project_column_id=done["id"],
    )
    made_recurring = await client.patch(
        f"/api/v1/tasks/{completed['id']}",
        json={
            "recurrence_type_code": "daily",
            "recurrence_start_date": "2026-09-18",
        },
    )
    assert made_recurring.status_code == 200
    assert made_recurring.json()["project_column_id"] == backlog["id"]
    assert made_recurring.json()["status"] == "todo"

    blocked_bulk = await client.post(
        f"/api/v1/projects/{project['id']}/tasks/bulk-status",
        json={"task_ids": [completed["id"]], "status": "done"},
    )
    assert blocked_bulk.status_code == 409
    assert blocked_bulk.json()["error"]["code"] == "RECURRING_TASK_COMPLETION_COLUMN"


@pytest.mark.anyio
async def test_move_rejects_wrong_project_missing_task_and_column(client: AsyncClient) -> None:
    """Move endpoint различает отсутствующие сущности и несогласованный проект."""
    await auth_client(client)
    first = await create_project(client, "Первый")
    second = await create_project(client, "Второй")
    task = await create_task(client, project_id=first["id"])

    wrong_project = await client.post(
        f"/api/v1/tasks/{task['id']}/move",
        json={
            "project_id": second["id"],
            "target_column_id": second["columns"][0]["id"],
            "target_position": 0,
        },
    )
    assert wrong_project.status_code == 400

    missing_task = await client.post(
        f"/api/v1/tasks/{uuid4()}/move",
        json={
            "project_id": first["id"],
            "target_column_id": first["columns"][0]["id"],
            "target_position": 0,
        },
    )
    assert missing_task.status_code == 404
    assert missing_task.json()["error"]["code"] == "TASK_NOT_FOUND"

    missing_column = await client.post(
        f"/api/v1/tasks/{task['id']}/move",
        json={
            "project_id": first["id"],
            "target_column_id": str(uuid4()),
            "target_position": 0,
        },
    )
    assert missing_column.status_code == 404
    assert missing_column.json()["error"]["code"] == "PROJECT_COLUMN_NOT_FOUND"


@pytest.mark.anyio
async def test_project_filter_returns_regular_and_recurring_tasks(client: AsyncClient) -> None:
    """Фильтр project_id не теряет повторяющиеся задачи проекта."""
    await auth_client(client)
    first = await create_project(client, "Первый")
    second = await create_project(client, "Второй")
    regular = await create_task(client, title="Обычная", project_id=first["id"])
    recurring = await create_task(
        client,
        title="Повтор",
        project_id=first["id"],
        recurrence_type_code="daily",
        recurrence_start_date="2026-09-18",
    )
    await create_task(client, title="Чужая", project_id=second["id"])

    response = await client.get(f"/api/v1/tasks?project_id={first['id']}&limit=100")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()["items"]} == {
        regular["id"],
        recurring["id"],
    }
