"""Repository для refresh-сессий пользователей."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import UserSession


class UserSessionRepository:
    """CRUD и запросы для refresh-сессий пользователей."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        *,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> UserSession:
        """Создает refresh-сессию и подтягивает значения, сгенерированные БД."""
        user_session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self.db.add(user_session)
        await self.db.flush()
        await self.db.refresh(user_session)
        return user_session

    async def get_active_session_by_hash(
        self,
        refresh_token_hash: str,
        now: datetime,
    ) -> UserSession | None:
        """Возвращает активную refresh-сессию по hash токена."""
        statement = select(UserSession).where(
            UserSession.refresh_token_hash == refresh_token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_session(self, user_session: UserSession, now: datetime) -> None:
        """Отзывает одну refresh-сессию."""
        user_session.revoked_at = now
        await self.db.flush()

    async def revoke_all_sessions_for_user(self, user_id: UUID, now: datetime) -> None:
        """Отзывает все активные refresh-сессии пользователя."""
        statement = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.db.execute(statement)
        await self.db.flush()
