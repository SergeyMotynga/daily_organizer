"""ORM-модели задач и системных статусов задач."""

from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.db.base import Base
from backend.models.user import User


class TaskStatus(Base):
    """Системный справочник статусов задач."""

    __tablename__ = "task_statuses"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    tasks: Mapped[list["Task"]] = relationship(back_populates="status")


class TaskRecurrenceType(Base):
    """Системный справочник типов повторения задач."""

    __tablename__ = "task_recurrence_types"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    tasks: Mapped[list["Task"]] = relationship(back_populates="recurrence_type")


class Task(Base):
    """Задача пользователя."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "deadline_time IS NULL OR deadline_date IS NOT NULL",
            name="ck_tasks_deadline_time_requires_date",
        ),
        CheckConstraint(
            "recurrence_interval >= 1",
            name="ck_tasks_recurrence_interval_positive",
        ),
        CheckConstraint(
            "recurrence_end_date IS NULL OR recurrence_start_date IS NULL "
            "OR recurrence_end_date >= recurrence_start_date",
            name="ck_tasks_recurrence_dates_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[str] = mapped_column(
        ForeignKey("task_statuses.code", ondelete="RESTRICT"),
        default="todo",
        server_default=text("'todo'"),
        index=True,
    )
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    deadline_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    recurrence_type_code: Mapped[str] = mapped_column(
        ForeignKey("task_recurrence_types.code", ondelete="RESTRICT"),
        default="none",
        server_default=text("'none'"),
        index=True,
    )
    recurrence_interval: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    recurrence_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurrence_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="tasks")
    status: Mapped[TaskStatus] = relationship(back_populates="tasks")
    recurrence_type: Mapped[TaskRecurrenceType] = relationship(back_populates="tasks")
    recurrence_completions: Mapped[list["TaskRecurrenceCompletion"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TaskRecurrenceCompletion(Base):
    """Факт выполнения одного дня повторяющейся задачи."""

    __tablename__ = "task_recurrence_completions"
    __table_args__ = (
        UniqueConstraint("task_id", "occurrence_date", name="uq_task_recurrence_completion"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
    )
    occurrence_date: Mapped[date] = mapped_column(Date)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    task: Mapped[Task] = relationship(back_populates="recurrence_completions")
