"""HTTP-схемы task API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.domain.tasks import TaskStatusCode
from backend.schemas.common import PaginationMeta


def trim_text(value: str | None) -> str:
    """Обрезает пробелы по краям строки."""
    if value is None:
        msg = "Поле обязательно"
        raise ValueError(msg)

    stripped = value.strip()
    if not stripped:
        msg = "Поле не может быть пустым"
        raise ValueError(msg)
    return stripped


def normalize_description(value: str | None) -> str | None:
    """Обрезает описание и превращает пустую строку в null."""
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


class TaskCreateRequest(BaseModel):
    """Запрос создания задачи."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    planned_date: date | None = None
    deadline_date: date | None = None
    status: TaskStatusCode | None = None

    _trim_title = field_validator("title")(trim_text)
    _normalize_description = field_validator("description")(normalize_description)

    model_config = ConfigDict(extra="forbid")


class TaskUpdateRequest(BaseModel):
    """Запрос частичного изменения задачи."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    planned_date: date | None = None
    deadline_date: date | None = None
    status: TaskStatusCode | None = None

    _trim_title = field_validator("title")(trim_text)
    _normalize_description = field_validator("description")(normalize_description)

    model_config = ConfigDict(extra="forbid")


class TaskResponse(BaseModel):
    """Публичное представление задачи."""

    id: UUID
    title: str
    description: str | None
    status: TaskStatusCode = Field(validation_alias="status_code")
    planned_date: date | None
    deadline_date: date | None
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TaskListResponse(BaseModel):
    """Ответ списка задач с пагинацией."""

    items: list[TaskResponse]
    pagination: PaginationMeta
