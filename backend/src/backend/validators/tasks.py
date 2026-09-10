"""Валидаторы task-модуля."""

from datetime import date

from backend.exceptions.tasks import InvalidCalendarRangeError, InvalidTaskTitleError

MAX_CALENDAR_RANGE_DAYS = 42
MAX_TASK_TITLE_LENGTH = 255


def validate_task_title(title: str | None) -> str:
    """Проверяет и очищает название задачи."""
    if title is None:
        raise InvalidTaskTitleError()

    title = title.strip()
    if not title or len(title) > MAX_TASK_TITLE_LENGTH:
        raise InvalidTaskTitleError()

    return title


def validate_calendar_range(date_from: date, date_to: date) -> None:
    """Проверяет порядок и максимальную длину календарного диапазона."""
    range_days = (date_to - date_from).days + 1
    if range_days < 1 or range_days > MAX_CALENDAR_RANGE_DAYS:
        raise InvalidCalendarRangeError()
