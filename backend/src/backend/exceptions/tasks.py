"""Доменные исключения task-модуля."""


class TaskError(Exception):
    """Базовое исключение task-модуля."""


class TaskNotFoundError(TaskError):
    """Задача не найдена или недоступна текущему пользователю."""


class TaskStatusNotFoundError(TaskError):
    """Статус задачи не найден или неактивен."""


class InvalidTaskTitleError(TaskError):
    """Название задачи не прошло валидацию."""


class InvalidTimezoneError(TaskError):
    """Timezone не является валидным IANA timezone name."""
