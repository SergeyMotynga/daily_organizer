"""Точка входа FastAPI-приложения."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Создает и настраивает экземпляр FastAPI."""
    app = FastAPI(title="Daily Organizer API", version="0.1.0")

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        """Проверяет, что приложение запущено."""
        return {"status": "ok"}

    return app


app = create_app()
