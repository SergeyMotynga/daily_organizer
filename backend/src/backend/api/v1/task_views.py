"""Endpoint-ы представлений задач API v1."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_current_user, get_task_service
from backend.models.user import User
from backend.schemas.task_views import (
    TodayViewBlocksResponse,
    TodayViewResponse,
    TodayViewSummaryResponse,
)
from backend.schemas.tasks import TaskResponse
from backend.services.tasks import TaskService, TodayTaskResult, TodayViewResult

router = APIRouter(prefix="/api/v1/task-views", tags=["task-views"])


@router.get("/today", response_model=TodayViewResponse)
async def get_today_view(
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    timezone: Annotated[str, Query(min_length=1, max_length=255)],
) -> TodayViewResponse:
    """Возвращает экран Сегодня для задач текущего пользователя."""
    result = await task_service.get_today_view(user=current_user, timezone_name=timezone)
    return _today_view_response(result)


def _today_view_response(result: TodayViewResult) -> TodayViewResponse:
    """Преобразует результат сервиса в HTTP-схему экрана Сегодня."""
    return TodayViewResponse(
        date=result.date,
        summary=TodayViewSummaryResponse(
            total_active=result.summary.total_active,
            done_today=result.summary.done_today,
            overdue=result.summary.overdue,
            today_deadline=result.summary.today_deadline,
        ),
        blocks=TodayViewBlocksResponse(
            planned_today=_task_responses(result.blocks.planned_today),
            inbox=_task_responses(result.blocks.inbox),
            soon_deadline=_task_responses(result.blocks.soon_deadline),
            today_deadline=_task_responses(result.blocks.today_deadline),
            overdue=_task_responses(result.blocks.overdue),
            done_today=_task_responses(result.blocks.done_today),
        ),
    )


def _task_responses(tasks: list[TodayTaskResult]) -> list[TaskResponse]:
    """Преобразует задачи дня в HTTP-схемы с вычисленным статусом."""
    return [
        TaskResponse.model_validate(item.task).model_copy(
            update={"status": item.status, "occurrence_date": item.occurrence_date}
        )
        for item in tasks
    ]
