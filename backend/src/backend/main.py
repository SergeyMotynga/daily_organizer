"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI

from backend.api.errors import register_exception_handlers
from backend.api.router import api_router


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""
    app = FastAPI(title="Daily Organizer API", version="0.1.0")
    register_exception_handlers(app)

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Проверяет, что приложение запущено."""
        return {"status": "ok"}

    app.include_router(api_router)

    return app


app = create_app()
