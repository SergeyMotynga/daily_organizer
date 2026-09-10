"""Доменные исключения task-модуля."""


class TaskError(Exception):
    """Базовое исключение task-модуля."""


class TaskNotFoundError(TaskError):
    """Задача не найдена или недоступна текущему пользователю."""


class TaskStatusNotFoundError(TaskError):
    """Статус задачи не найден или неактивен."""


class TaskRecurrenceTypeNotFoundError(TaskError):
    """Тип повторения задачи не найден или неактивен."""


class InvalidTaskScheduleError(TaskError):
    """Даты, время или правило повторения задачи некорректны."""


class InvalidTaskRecurrenceCompletionError(TaskError):
    """Для указанной задачи или даты нельзя изменить факт выполнения."""


class InvalidTaskTitleError(TaskError):
    """Название задачи не прошло валидацию."""


class InvalidTimezoneError(TaskError):
    """Timezone не является валидным IANA timezone name."""


class InvalidCalendarRangeError(TaskError):
    """Диапазон календаря имеет неверный порядок или превышает лимит."""
