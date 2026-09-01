"""Формирование JSON-ответов для API-ошибок."""

from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class ErrorSpec:
    """Описание HTTP-представления ошибки."""

    status_code: int
    code: str
    message: str


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Создает JSON-ответ в едином формате ошибок."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )
