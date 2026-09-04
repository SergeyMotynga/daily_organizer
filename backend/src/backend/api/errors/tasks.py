"""API-представление task-ошибок."""

from backend.api.errors.responses import ErrorSpec
from backend.exceptions.tasks import (
    InvalidTaskTitleError,
    TaskError,
    TaskNotFoundError,
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
    InvalidTaskTitleError: ErrorSpec(
        status_code=400,
        code="INVALID_TASK_TITLE",
        message="Название задачи обязательно и должно быть не длиннее 255 символов",
    ),
}
