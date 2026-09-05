"""Интеграционные тесты доступа к экрану Сегодня."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_today_view_rejects_request_without_access_token(client: AsyncClient) -> None:
    """Экран Сегодня требует авторизацию."""
    response = await client.get("/api/v1/task-views/today", params={"timezone": "UTC"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
