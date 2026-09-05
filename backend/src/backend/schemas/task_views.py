"""HTTP-схемы представлений задач API."""

from datetime import date

from pydantic import BaseModel, Field

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
