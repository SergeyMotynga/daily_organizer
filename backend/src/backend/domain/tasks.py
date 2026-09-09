"""Доменные значения task-модуля."""

from enum import StrEnum


class TaskStatusCode(StrEnum):
    """Коды системных статусов задач."""

    todo = "todo"
    done = "done"


class TaskSort(StrEnum):
    """Поддерживаемые сортировки списка задач."""

    created_at_desc = "created_at_desc"
    created_at_asc = "created_at_asc"
    planned_date_asc = "planned_date_asc"
    deadline_date_asc = "deadline_date_asc"


class TaskListPreset(StrEnum):
    """Продуктовые пресеты списка задач."""

    today = "today"
    tomorrow = "tomorrow"
    week = "week"
    no_date = "no_date"
    all = "all"


class TaskDeadlinePreset(StrEnum):
    """Поддерживаемые пресеты дедлайна списка задач."""

    overdue = "overdue"
    today = "today"
    soon = "soon"
