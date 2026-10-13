"""Exception handlers для FastAPI."""

from collections.abc import Awaitable, Callable
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from backend.api.errors.auth import AUTH_ERROR_SPECS
from backend.api.errors.projects import PROJECT_ERROR_SPECS
from backend.api.errors.responses import ErrorSpec, build_error_response
from backend.api.errors.tasks import TASK_ERROR_SPECS
from backend.exceptions.auth import AuthError
from backend.exceptions.projects import ProjectError
from backend.exceptions.tasks import TaskError


def make_domain_error_handler[ErrorT: Exception](
    error_specs: dict[type[ErrorT], ErrorSpec],
) -> Callable[[Request, ErrorT], Awaitable[JSONResponse]]:
    """Создает handler для группы доменных ошибок."""

    async def handler(_request: Request, exc: ErrorT) -> JSONResponse:
        spec = error_specs.get(type(exc))
        if spec is None:
            return build_error_response(
                status_code=500,
                code="INTERNAL_ERROR",
                message="Внутренняя ошибка сервера",
            )

        return build_error_response(
            status_code=spec.status_code,
            code=spec.code,
            message=spec.message,
        )

    return handler


auth_error_handler = make_domain_error_handler(AUTH_ERROR_SPECS)
task_error_handler = make_domain_error_handler(TASK_ERROR_SPECS)
project_error_handler = make_domain_error_handler(PROJECT_ERROR_SPECS)


def make_json_safe(value: Any) -> Any:
    """Приводит details ошибок в JSON-совместимый вид."""
    if isinstance(value, BaseException):
        return str(value)
    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return tuple(make_json_safe(item) for item in value)

    return value


async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Преобразует ошибки валидации запроса в единый формат."""
    return build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Ошибка валидации запроса",
        details={"errors": make_json_safe(exc.errors())},
    )


async def http_error_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Преобразует стандартные HTTP-ошибки в единый формат."""
    return build_error_response(
        status_code=exc.status_code,
        code="HTTP_ERROR",
        message=str(exc.detail),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует exception handlers приложения."""
    app.add_exception_handler(AuthError, cast(ExceptionHandler, auth_error_handler))
    app.add_exception_handler(TaskError, cast(ExceptionHandler, task_error_handler))
    app.add_exception_handler(ProjectError, cast(ExceptionHandler, project_error_handler))
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_error_handler),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        cast(ExceptionHandler, http_error_handler),
    )
