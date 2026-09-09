"""API-представление task-ошибок."""

from backend.api.errors.responses import ErrorSpec
from backend.exceptions.tasks import (
    InvalidTaskRecurrenceCompletionError,
    InvalidTaskScheduleError,
    InvalidTaskTitleError,
    InvalidTimezoneError,
    TaskError,
    TaskNotFoundError,
    TaskRecurrenceTypeNotFoundError,
    TaskStatusNotFoundError,
)

TASK_ERROR_SPECS: dict[type[TaskError], ErrorSpec] = {
    TaskNotFoundError: ErrorSpec(
        status_code=404,
        code="TASK_NOT_FOUND",
        message="Задача не найдена",
    ),
    TaskStatusNotFoundError: ErrorSpec(
        status_code=400,
        code="TASK_STATUS_NOT_FOUND",
        message="Статус задачи не найден",
    ),
    TaskRecurrenceTypeNotFoundError: ErrorSpec(
        status_code=400,
        code="TASK_RECURRENCE_TYPE_NOT_FOUND",
        message="Тип повторения задачи не найден",
    ),
    InvalidTaskScheduleError: ErrorSpec(
        status_code=400,
        code="INVALID_TASK_SCHEDULE",
        message="Некорректные даты, время или правило повторения задачи",
    ),
    InvalidTaskRecurrenceCompletionError: ErrorSpec(
        status_code=400,
        code="INVALID_TASK_RECURRENCE_COMPLETION",
        message="Для этой задачи или даты нельзя изменить выполнение повторения",
    ),
    InvalidTaskTitleError: ErrorSpec(
        status_code=400,
        code="INVALID_TASK_TITLE",
        message="Название задачи обязательно и должно быть не длиннее 255 символов",
    ),
    InvalidTimezoneError: ErrorSpec(
        status_code=400,
        code="INVALID_TIMEZONE",
        message="Некорректная timezone",
    ),
}
