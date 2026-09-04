"""Общие внутренние DTO."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PaginationParams:
    """Параметры пагинации для внутренних слоев."""

    limit: int = 50
    offset: int = 0
