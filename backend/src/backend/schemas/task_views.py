"""HTTP-схемы представлений задач API."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from backend.domain.tasks import TaskRecurrenceTypeCode, TaskStatusCode
from backend.schemas.tasks import TaskResponse


class TodayViewBlocksResponse(BaseModel):
    """Блоки экрана Сегодня."""

    planned_today: list[TaskResponse]
    inbox: list[TaskResponse]
    soon_deadline: list[TaskResponse]
    today_deadline: list[TaskResponse]
    overdue: list[TaskResponse]
    done_today: list[TaskResponse]


class TodayViewSummaryResponse(BaseModel):
    """Сводка экрана Сегодня."""

    total_active: int = Field(ge=0)
    done_today: int = Field(ge=0)
    overdue: int = Field(ge=0)
    today_deadline: int = Field(ge=0)


class TodayViewResponse(BaseModel):
    """Ответ экрана Сегодня."""

    date: date
    summary: TodayViewSummaryResponse
    blocks: TodayViewBlocksResponse


class CalendarTaskResponse(BaseModel):
    """Исходные данные задачи, необходимые календарю."""

    id: UUID
    title: str
    description: str | None
    planned_date: date | None
    planned_time: time | None
    deadline_date: date | None
    deadline_time: time | None
    recurrence_type_code: TaskRecurrenceTypeCode
    recurrence_interval: int
    recurrence_start_date: date | None
    recurrence_end_date: date | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("planned_time", "deadline_time", when_used="json")
    def serialize_local_time(self, value: time | None) -> str | None:
        """Сериализует локальное время без секунд."""
        return value.strftime("%H:%M") if value is not None else None

    model_config = ConfigDict(from_attributes=True)


class CalendarTaskItemResponse(BaseModel):
    """Задача вместе с её контекстом в календаре."""

    task: CalendarTaskResponse
    status: TaskStatusCode
    occurrence_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class CalendarViewResponse(BaseModel):
    """Ответ календаря для диапазона дат."""

    date_from: date
    date_to: date
    planned: list[CalendarTaskItemResponse]
    deadlines: list[CalendarTaskItemResponse]
    recurrences: list[CalendarTaskItemResponse]

    model_config = ConfigDict(from_attributes=True)
