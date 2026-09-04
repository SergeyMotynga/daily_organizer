"""Integration tests справочника статусов задач."""

import pytest
from httpx import AsyncClient
from tests.integration.api.v1.tasks.helpers import auth_client


@pytest.mark.anyio
async def test_list_task_statuses_returns_active_statuses(client: AsyncClient) -> None:
    """Endpoint статусов возвращает активный системный справочник."""
    await auth_client(client)

    response = await client.get("/api/v1/task-statuses")

    assert response.status_code == 200
    assert response.json() == [
        {"code": "todo", "title": "Активная", "sort_order": 10},
        {"code": "done", "title": "Выполненная", "sort_order": 20},
        {"code": "archived", "title": "Архивная", "sort_order": 30},
    ]
