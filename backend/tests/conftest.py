"""Общие fixtures для backend-тестов."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.fixture
def anyio_backend() -> str:
    """Фиксирует asyncio как backend для async-тестов."""
    return "asyncio"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Отдает async HTTP-клиент для запросов к FastAPI-приложению."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
