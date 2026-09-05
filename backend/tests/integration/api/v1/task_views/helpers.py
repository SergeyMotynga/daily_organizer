"""Helper-функции для integration tests представлений задач."""

from typing import Any


def block_titles(payload: dict[str, Any], block_name: str) -> list[str]:
    """Возвращает названия задач из блока экрана Сегодня."""
    return [item["title"] for item in payload["blocks"][block_name]]


def block_ids(payload: dict[str, Any], block_name: str) -> list[str]:
    """Возвращает id задач из блока экрана Сегодня."""
    return [item["id"] for item in payload["blocks"][block_name]]


def regular_block_ids(payload: dict[str, Any]) -> list[str]:
    """Возвращает id задач из обычных блоков экрана Сегодня."""
    ids: list[str] = []
    for block_name in [
        "planned_today",
        "inbox",
        "soon_deadline",
        "today_deadline",
        "overdue",
    ]:
        ids.extend(block_ids(payload, block_name))

    return ids
