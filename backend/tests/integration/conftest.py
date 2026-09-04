"""Fixtures для integration tests."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.core.config import get_settings
from backend.db.session import get_db
from backend.main import app

BACKEND_DIR = Path(__file__).resolve().parents[2]


def get_test_database_url() -> str:
    """Возвращает URL тестовой БД или падает с понятной ошибкой."""
    test_database_url = get_settings().test_database_url
    if test_database_url is None:
        msg = "Для integration tests нужно задать TEST_DATABASE_URL"
        raise RuntimeError(msg)

    return test_database_url


def get_test_migration_database_url() -> str:
    """Возвращает sync URL тестовой БД для Alembic."""
    return get_test_database_url().replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)


@pytest.fixture(scope="session", autouse=True)
def apply_test_migrations() -> None:
    """Применяет Alembic migrations к тестовой БД перед integration tests."""
    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_config.attributes["database_url"] = get_test_migration_database_url()
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def test_engine() -> AsyncEngine:
    """Создает async engine для тестовой БД."""
    return create_async_engine(get_test_database_url(), poolclass=NullPool)


@pytest.fixture(scope="session")
def test_sessionmaker(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Создает фабрику async-сессий для тестовой БД."""
    return async_sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture(autouse=True)
async def clean_data_tables(test_sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    """Очищает пользовательские данные перед каждым integration test."""
    async with test_sessionmaker() as db:
        await db.execute(text("TRUNCATE tasks, user_sessions, users RESTART IDENTITY CASCADE"))
        await db.commit()


@pytest.fixture
async def client(
    test_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    """Отдает HTTP-клиент с подменой DB dependency на тестовую БД."""

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with test_sessionmaker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()
