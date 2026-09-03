"""Exception handlers для FastAPI."""

from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from backend.api.errors.auth import AUTH_ERROR_SPECS
from backend.api.errors.responses import ErrorSpec, build_error_response
from backend.exceptions.auth import AuthError


def make_domain_error_handler(
    error_specs: dict[type[AuthError], ErrorSpec],
) -> Callable[[Request, AuthError], Awaitable[JSONResponse]]:
    """Создает handler для группы доменных ошибок."""

    async def handler(_request: Request, exc: AuthError) -> JSONResponse:
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


async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Преобразует ошибки валидации запроса в единый формат."""
    return build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Ошибка валидации запроса",
        details={"errors": exc.errors()},
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
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, validation_error_handler),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        cast(ExceptionHandler, http_error_handler),
    )
