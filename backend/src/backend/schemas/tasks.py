"""HTTP-схемы task API."""

import re
from datetime import date, datetime, time
from typing import Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from backend.domain.tasks import TaskRecurrenceTypeCode, TaskStatusCode
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


def validate_local_time_format(value: str | time | None) -> str | time | None:
    """Проверяет строковый формат локального времени задачи."""
    if isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value) is None:
        msg = "Время должно быть в формате HH:MM"
        raise ValueError(msg)
    return value


class TaskCreateRequest(BaseModel):
    """Запрос создания задачи."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    planned_date: date | None = None
    planned_time: time | None = None
    deadline_date: date | None = None
    deadline_time: time | None = None
    recurrence_type_code: TaskRecurrenceTypeCode = TaskRecurrenceTypeCode.none
    recurrence_interval: int = Field(default=1, ge=1)
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    status: TaskStatusCode | None = None
    project_id: UUID | None = None
    project_column_id: UUID | None = None

    _trim_title = field_validator("title")(trim_text)
    _normalize_description = field_validator("description")(normalize_description)
    _validate_planned_time = field_validator("planned_time", mode="before")(
        validate_local_time_format
    )
    _validate_deadline_time = field_validator("deadline_time", mode="before")(
        validate_local_time_format
    )

    @model_validator(mode="after")
    def validate_deadline_time_dependency(self) -> Self:
        """Не разрешает время дедлайна без даты дедлайна."""
        if self.deadline_time is not None and self.deadline_date is None:
            msg = "Время дедлайна можно указать только вместе с датой"
            raise ValueError(msg)
        return self

    model_config = ConfigDict(extra="forbid")


class TaskUpdateRequest(BaseModel):
    """Запрос частичного изменения задачи."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    planned_date: date | None = None
    planned_time: time | None = None
    deadline_date: date | None = None
    deadline_time: time | None = None
    recurrence_type_code: TaskRecurrenceTypeCode | None = None
    recurrence_interval: int | None = Field(default=None, ge=1)
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    status: TaskStatusCode | None = None
    archived: bool = False
    project_id: UUID | None = None
    project_column_id: UUID | None = None

    _trim_title = field_validator("title")(trim_text)
    _normalize_description = field_validator("description")(normalize_description)
    _validate_planned_time = field_validator("planned_time", mode="before")(
        validate_local_time_format
    )
    _validate_deadline_time = field_validator("deadline_time", mode="before")(
        validate_local_time_format
    )

    model_config = ConfigDict(extra="forbid")


class TaskResponse(BaseModel):
    """Публичное представление задачи."""

    id: UUID
    title: str
    description: str | None
    status: TaskStatusCode = Field(validation_alias="status_code")
    planned_date: date | None
    planned_time: time | None
    deadline_date: date | None
    deadline_time: time | None
    recurrence_type_code: TaskRecurrenceTypeCode
    recurrence_interval: int
    recurrence_start_date: date | None
    recurrence_end_date: date | None
    project_id: UUID | None
    project_column_id: UUID | None
    project_position: int | None
    occurrence_date: date | None = None
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("planned_time", "deadline_time", when_used="json")
    def serialize_local_time(self, value: time | None) -> str | None:
        """Сериализует локальное время без секунд."""
        return value.strftime("%H:%M") if value is not None else None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TaskListResponse(BaseModel):
    """Ответ списка задач с пагинацией."""

    items: list[TaskResponse]
    pagination: PaginationMeta


class TaskRecurrenceCompletionResponse(BaseModel):
    """Публичное представление выполнения повторения задачи."""

    id: UUID
    task_id: UUID
    occurrence_date: date
    completed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
