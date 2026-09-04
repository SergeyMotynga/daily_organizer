"""Валидаторы task-модуля."""

from backend.exceptions.tasks import InvalidTaskTitleError

MAX_TASK_TITLE_LENGTH = 255


def validate_task_title(title: str | None) -> str:
    """Проверяет и очищает название задачи."""
    if title is None:
        raise InvalidTaskTitleError()

    title = title.strip()
    if not title or len(title) > MAX_TASK_TITLE_LENGTH:
        raise InvalidTaskTitleError()

    return title
