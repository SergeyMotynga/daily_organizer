"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.errors import register_exception_handlers
from backend.api.router import api_router
from backend.core.config import get_settings


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""
    settings = get_settings()
    app = FastAPI(title="Daily Organizer API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Проверяет, что приложение запущено."""
        return {"status": "ok"}

    app.include_router(api_router)

    return app


app = create_app()
