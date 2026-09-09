"""Внутренние DTO task-модуля."""

from dataclasses import dataclass
from datetime import date, time

from backend.domain.tasks import (
    TaskDeadlinePreset,
    TaskListPreset,
    TaskRecurrenceTypeCode,
    TaskSort,
    TaskStatusCode,
)


@dataclass(frozen=True)
class TaskCreateData:
    """Данные для создания задачи."""

    title: str
    description: str | None = None
    planned_date: date | None = None
    planned_time: time | None = None
    deadline_date: date | None = None
    deadline_time: time | None = None
    recurrence_type_code: TaskRecurrenceTypeCode = TaskRecurrenceTypeCode.none
    recurrence_interval: int = 1
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    status: TaskStatusCode | None = None


@dataclass(frozen=True)
class TaskUpdateData:
    """Данные для частичного изменения задачи."""

    fields_set: frozenset[str]
    title: str | None = None
    description: str | None = None
    planned_date: date | None = None
    planned_time: time | None = None
    deadline_date: date | None = None
    deadline_time: time | None = None
    recurrence_type_code: TaskRecurrenceTypeCode | None = None
    recurrence_interval: int | None = None
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    status: TaskStatusCode | None = None
    archived: bool = False

    def has(self, field: str) -> bool:
        """Проверяет, что поле пришло в PATCH-запросе."""
        return field in self.fields_set


@dataclass(frozen=True)
class TaskListQuery:
    """Query-параметры списка задач, собранные API-слоем."""

    preset: TaskListPreset = TaskListPreset.all
    statuses: list[TaskStatusCode] | None = None
    archived: bool = False
    planned_date: date | None = None
    deadline_date: date | None = None
    deadline_preset: TaskDeadlinePreset | None = None
    timezone: str = "UTC"
    q: str | None = None
    sort: TaskSort = TaskSort.created_at_desc


@dataclass(frozen=True)
class TaskListFilters:
    """Технические фильтры списка задач для repository layer."""

    statuses: list[TaskStatusCode]
    archived: bool = False
    planned_date_from: date | None = None
    planned_date_to: date | None = None
    planned_date_is_null: bool = False
    deadline_date: date | None = None
    deadline_date_from: date | None = None
    deadline_date_to: date | None = None
    overdue_date: date | None = None
    overdue_time: time | None = None
    recurrence_date: date | None = None
    q: str | None = None
    sort: TaskSort = TaskSort.created_at_desc
