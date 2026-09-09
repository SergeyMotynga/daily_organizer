"""Integration tests изменения задач."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.tasks.helpers import auth_client, create_task


@pytest.mark.anyio
async def test_patch_task_fields(client: AsyncClient) -> None:
    """PATCH изменяет разрешенные поля задачи."""
    await auth_client(client)
    task = await create_task(client)

    response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "title": "  Новое название  ",
            "description": "  Новое описание  ",
            "planned_date": "2026-09-05",
            "planned_time": "09:15",
            "deadline_date": "2026-09-06",
        },
    )

    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["title"] == "Новое название"
    assert updated_task["description"] == "Новое описание"
    assert updated_task["planned_date"] == "2026-09-05"
    assert updated_task["planned_time"] == "09:15"
    assert updated_task["deadline_date"] == "2026-09-06"
    assert "status_code" not in updated_task


@pytest.mark.anyio
async def test_patch_description_to_null(client: AsyncClient) -> None:
    """PATCH отличает отсутствие description от явного null."""
    await auth_client(client)
    task = await create_task(client, {"title": "Задача", "description": "Описание"})

    response = await client.patch(f"/api/v1/tasks/{task['id']}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None


@pytest.mark.anyio
async def test_patch_planned_time_to_null(client: AsyncClient) -> None:
    """PATCH с planned_time=null очищает плановое время."""
    await auth_client(client)
    task = await create_task(client, {"title": "Задача", "planned_time": "18:45"})

    response = await client.patch(f"/api/v1/tasks/{task['id']}", json={"planned_time": None})

    assert response.status_code == 200
    assert response.json()["planned_time"] is None


@pytest.mark.anyio
async def test_patch_title_to_null_is_rejected(client: AsyncClient) -> None:
    """PATCH с title=null не превращается в пустую строку."""
    await auth_client(client)
    task = await create_task(client)

    response = await client.patch(f"/api/v1/tasks/{task['id']}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_patch_status_done_then_todo(client: AsyncClient) -> None:
    """Переход todo -> done -> todo ставит и очищает completed_at."""
    await auth_client(client)
    task = await create_task(client)

    done_response = await client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"})
    assert done_response.status_code == 200
    done_task = done_response.json()
    assert done_task["status"] == "done"
    assert done_task["completed_at"] is not None

    todo_response = await client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "todo"})
    assert todo_response.status_code == 200
    todo_task = todo_response.json()
    assert todo_task["status"] == "todo"
    assert todo_task["completed_at"] is None
    assert todo_task["archived_at"] is None


@pytest.mark.anyio
@pytest.mark.parametrize("initial_status", ["todo", "done"])
async def test_archive_and_restore_preserve_status(
    client: AsyncClient,
    initial_status: str,
) -> None:
    """Архивация и восстановление не меняют состояние выполнения."""
    await auth_client(client)
    task = await create_task(client, {"title": "Задача", "status": initial_status})

    archive_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"archived": True},
    )

    assert archive_response.status_code == 200
    archived_task = archive_response.json()
    assert archived_task["status"] == initial_status
    assert archived_task["completed_at"] == task["completed_at"]
    assert archived_task["archived_at"] is not None

    restore_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"archived": False},
    )

    assert restore_response.status_code == 200
    restored_task = restore_response.json()
    assert restored_task["status"] == initial_status
    assert restored_task["completed_at"] == task["completed_at"]
    assert restored_task["archived_at"] is None


@pytest.mark.anyio
async def test_patch_rejects_archived_status(client: AsyncClient) -> None:
    """PATCH не принимает архивацию как статус выполнения."""
    await auth_client(client)
    task = await create_task(client)

    response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "archived"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_status_transition_preserves_archived_at(client: AsyncClient) -> None:
    """Смена состояния выполнения не восстанавливает архивную задачу."""
    await auth_client(client)
    task = await create_task(client)
    archive_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"archived": True},
    )
    archived_at = archive_response.json()["archived_at"]

    done_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "done"},
    )
    assert done_response.status_code == 200
    assert done_response.json()["status"] == "done"
    assert done_response.json()["archived_at"] == archived_at

    todo_response = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "todo"},
    )
    assert todo_response.status_code == 200
    assert todo_response.json()["status"] == "todo"
    assert todo_response.json()["archived_at"] == archived_at


@pytest.mark.anyio
@pytest.mark.parametrize(
    "field",
    ["status_code", "completed_at", "archived_at", "created_at", "updated_at"],
)
async def test_patch_rejects_internal_fields(client: AsyncClient, field: str) -> None:
    """PATCH не принимает внутренние и системные поля."""
    await auth_client(client)
    task = await create_task(client)

    response = await client.patch(f"/api/v1/tasks/{task['id']}", json={field: "value"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
