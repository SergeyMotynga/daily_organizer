"""DTO пользователей."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Публичное представление пользователя."""

    id: UUID
    login: str
    name: str

    model_config = ConfigDict(from_attributes=True)
