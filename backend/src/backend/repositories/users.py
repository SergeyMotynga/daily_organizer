"""Repository для пользователей."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User


class UserRepository:
    """CRUD и запросы для пользователей."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Возвращает активного пользователя по id."""
        statement = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_login(self, login: str) -> User | None:
        """Возвращает активного пользователя по login."""
        statement = select(User).where(User.login == login, User.deleted_at.is_(None))
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_user(self, *, login: str, name: str, password_hash: str) -> User:
        """Создает пользователя и подтягивает значения, сгенерированные БД."""
        user = User(login=login, name=name, password_hash=password_hash)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_user_password(self, user: User, password_hash: str) -> None:
        """Обновляет password hash пользователя."""
        user.password_hash = password_hash
        await self.db.flush()
