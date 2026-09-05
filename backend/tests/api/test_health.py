"""Тесты системных endpoint-ов."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_check_returns_ok(client: AsyncClient) -> None:
    """Health endpoint возвращает статус приложения."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_cors_preflight_allows_local_frontend(client: AsyncClient) -> None:
    """CORS preflight разрешает локальный Vite frontend origin."""
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert response.headers["vary"] == "Origin"
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers
