"""Настройки приложения."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]
REPOSITORY_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Runtime-настройки, загружаемые из переменных окружения."""

    def __init__(self, **values: Any) -> None:
        """Создает настройки из env и явно описывает mypy допустимый вызов без аргументов."""
        super().__init__(**values)

    app_env: str = Field(alias="APP_ENV")
    app_debug: bool = Field(alias="APP_DEBUG")
    database_url: str = Field(alias="DATABASE_URL")
    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_access_token_ttl_minutes: int = Field(alias="JWT_ACCESS_TOKEN_TTL_MINUTES")
    jwt_refresh_token_ttl_days: int = Field(alias="JWT_REFRESH_TOKEN_TTL_DAYS")
    cookie_secure: bool = Field(alias="COOKIE_SECURE")
    cookie_samesite: Literal["lax", "strict", "none"] = Field(alias="COOKIE_SAMESITE")
    cors_origins: str = Field(alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_DIR / ".env", BACKEND_DIR / ".env"),
        extra="ignore",
    )

    @property
    def is_dev_mode(self) -> bool:
        """Проверяет, разрешены ли dev-only endpoint-ы."""
        return self.app_env in {"local", "dev", "test"}

    @property
    def cors_origin_list(self) -> list[str]:
        """Возвращает список origins из CSV-настройки CORS_ORIGINS."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Возвращает кешированный объект настроек приложения."""
    return Settings()
