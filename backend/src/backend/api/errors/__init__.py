"""Обработка API-ошибок."""

from backend.api.errors.handlers import (
    auth_error_handler,
    http_error_handler,
    register_exception_handlers,
    validation_error_handler,
)

__all__ = (
    "auth_error_handler",
    "http_error_handler",
    "register_exception_handlers",
    "validation_error_handler",
)
