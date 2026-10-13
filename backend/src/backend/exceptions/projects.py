"""Доменные ошибки личных проектов."""


class ProjectError(Exception):
    """Базовая ошибка project-модуля."""


class ProjectNotFoundError(ProjectError):
    """Проект не найден или не принадлежит пользователю."""


class ProjectColumnNotFoundError(ProjectError):
    """Колонка не найдена или не принадлежит проекту пользователя."""


class InvalidProjectTitleError(ProjectError):
    """Название проекта некорректно."""


class InvalidProjectColumnTitleError(ProjectError):
    """Название колонки некорректно."""


class InvalidProjectColumnOrderError(ProjectError):
    """Новый порядок не содержит точный набор колонок проекта."""


class ProjectColumnNotEmptyError(ProjectError):
    """В удаляемой колонке есть задачи."""


class ProjectCompletionColumnRequiredError(ProjectError):
    """Проект должен иметь ровно одну завершающую колонку."""


class InvalidTaskProjectError(ProjectError):
    """Проектные поля задачи несогласованы или недоступны пользователю."""


class RecurringTaskCompletionColumnError(ProjectError):
    """Повторяющуюся задачу нельзя поместить в завершающую колонку."""
