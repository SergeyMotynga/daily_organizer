"""Базовый класс SQLAlchemy-моделей."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общая declarative base для ORM-моделей."""
