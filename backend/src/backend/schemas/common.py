"""Общие response-схемы HTTP API."""

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """Метаданные пагинации в ответах API."""

    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
