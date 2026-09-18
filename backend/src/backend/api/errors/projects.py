"""API-представление ошибок личных проектов."""

from backend.api.errors.responses import ErrorSpec
from backend.exceptions.projects import (
    InvalidProjectColumnOrderError,
    InvalidProjectColumnTitleError,
    InvalidProjectTitleError,
    InvalidTaskProjectError,
    ProjectColumnNotEmptyError,
    ProjectColumnNotFoundError,
    ProjectCompletionColumnRequiredError,
    ProjectError,
    ProjectNotFoundError,
    RecurringTaskCompletionColumnError,
)

PROJECT_ERROR_SPECS: dict[type[ProjectError], ErrorSpec] = {
    ProjectNotFoundError: ErrorSpec(404, "PROJECT_NOT_FOUND", "Проект не найден"),
    ProjectColumnNotFoundError: ErrorSpec(
        404,
        "PROJECT_COLUMN_NOT_FOUND",
        "Колонка проекта не найдена",
    ),
    InvalidProjectTitleError: ErrorSpec(
        400,
        "INVALID_PROJECT_TITLE",
        "Название проекта обязательно и должно быть не длиннее 255 символов",
    ),
    InvalidProjectColumnTitleError: ErrorSpec(
        400,
        "INVALID_PROJECT_COLUMN_TITLE",
        "Название колонки обязательно и должно быть не длиннее 255 символов",
    ),
    InvalidProjectColumnOrderError: ErrorSpec(
        400,
        "INVALID_PROJECT_COLUMN_ORDER",
        "Порядок должен содержать все колонки проекта без повторов",
    ),
    ProjectColumnNotEmptyError: ErrorSpec(
        409,
        "PROJECT_COLUMN_NOT_EMPTY",
        "Нельзя удалить колонку, пока в ней есть задачи",
    ),
    ProjectCompletionColumnRequiredError: ErrorSpec(
        409,
        "PROJECT_COMPLETION_COLUMN_REQUIRED",
        "В проекте должна оставаться одна завершающая колонка",
    ),
    InvalidTaskProjectError: ErrorSpec(
        400,
        "INVALID_TASK_PROJECT",
        "Выбранные проект и этап недоступны или не согласованы",
    ),
    RecurringTaskCompletionColumnError: ErrorSpec(
        409,
        "RECURRING_TASK_COMPLETION_COLUMN",
        "Повторяющуюся задачу нельзя переместить в завершающую колонку",
    ),
}
