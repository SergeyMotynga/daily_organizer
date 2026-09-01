"""Фабрика асинхронных SQLAlchemy-сессий."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import get_settings


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Создает и кеширует фабрику async-сессий."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Отдает асинхронную сессию БД на время обработки запроса."""
    async with get_sessionmaker()() as db:
        yield db
