"""Внутренние DTO project-модуля."""

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from backend.models.project import Project


@dataclass(frozen=True)
class ProjectCreateData:
    """Данные создания проекта."""

    title: str
    description: str | None = None


@dataclass(frozen=True)
class ProjectUpdateData:
    """Данные частичного изменения проекта."""

    fields_set: frozenset[str]
    title: str | None = None
    description: str | None = None
    archived: bool = False

    def has(self, field: str) -> bool:
        """Проверяет присутствие поля в PATCH-запросе."""
        return field in self.fields_set


@dataclass(frozen=True)
class ProjectColumnCreateData:
    """Данные создания колонки проекта."""

    title: str
    is_completion_column: bool = False


@dataclass(frozen=True)
class ProjectColumnUpdateData:
    """Данные частичного изменения колонки."""

    fields_set: frozenset[str]
    title: str | None = None
    is_completion_column: bool = False

    def has(self, field: str) -> bool:
        """Проверяет присутствие поля в PATCH-запросе."""
        return field in self.fields_set


@dataclass(frozen=True)
class ProjectSummaryData:
    """Проект с агрегатами для списка без N+1."""

    project: "Project"
    task_count: int
    completed_task_count: int


@dataclass(frozen=True)
class TaskMoveData:
    """Цель атомарного перемещения проектной задачи."""

    project_id: UUID
    target_column_id: UUID
    target_position: int
