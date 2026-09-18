"""HTTP-схемы project API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.domain.tasks import TaskStatusCode
from backend.schemas.tasks import normalize_description, trim_text


class ProjectCreateRequest(BaseModel):
    """Запрос создания проекта."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None

    _trim_title = field_validator("title")(trim_text)
    _normalize_description = field_validator("description")(normalize_description)
    model_config = ConfigDict(extra="forbid")


class ProjectUpdateRequest(BaseModel):
    """Запрос частичного изменения проекта."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    archived: bool = False

    _trim_title = field_validator("title")(trim_text)
    _normalize_description = field_validator("description")(normalize_description)
    model_config = ConfigDict(extra="forbid")


class ProjectColumnCreateRequest(BaseModel):
    """Запрос создания колонки."""

    title: str = Field(min_length=1, max_length=255)
    is_completion_column: bool = False

    _trim_title = field_validator("title")(trim_text)
    model_config = ConfigDict(extra="forbid")


class ProjectColumnUpdateRequest(BaseModel):
    """Запрос частичного изменения колонки."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    is_completion_column: bool = False

    _trim_title = field_validator("title")(trim_text)
    model_config = ConfigDict(extra="forbid")


class ProjectColumnsReorderRequest(BaseModel):
    """Атомарный порядок всех колонок проекта."""

    column_ids: list[UUID] = Field(min_length=1)
    model_config = ConfigDict(extra="forbid")


class ProjectColumnResponse(BaseModel):
    """Публичное представление колонки проекта."""

    id: UUID
    project_id: UUID
    title: str
    position: int
    is_completion_column: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    """Публичное представление проекта с агрегатами."""

    id: UUID
    title: str
    description: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    completed_task_count: int = 0
    progress_percent: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Проект с колонками для доски и настроек."""

    columns: list[ProjectColumnResponse]


class ProjectListResponse(BaseModel):
    """Список личных проектов."""

    items: list[ProjectResponse]


class TaskMoveRequest(BaseModel):
    """Запрос атомарного перемещения карточки."""

    project_id: UUID
    target_column_id: UUID
    target_position: int = Field(ge=0)
    model_config = ConfigDict(extra="forbid")


class ProjectTasksBulkMoveRequest(BaseModel):
    """Запрос массового перемещения задач в этап."""

    task_ids: list[UUID] = Field(min_length=1, max_length=100)
    target_column_id: UUID
    model_config = ConfigDict(extra="forbid")


class ProjectTasksBulkStatusRequest(BaseModel):
    """Запрос массового изменения выполнения задач."""

    task_ids: list[UUID] = Field(min_length=1, max_length=100)
    status: TaskStatusCode
    model_config = ConfigDict(extra="forbid")
