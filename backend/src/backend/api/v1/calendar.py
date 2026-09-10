"""Calendar endpoint API v1."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_current_user, get_task_service
from backend.models.user import User
from backend.schemas.task_views import CalendarViewResponse
from backend.services.tasks import TaskService

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])


@router.get("", response_model=CalendarViewResponse)
async def get_calendar_view(
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    date_from: Annotated[date, Query()],
    date_to: Annotated[date, Query()],
) -> CalendarViewResponse:
    """Возвращает календарные данные текущего пользователя."""
    result = await task_service.get_calendar_view(
        user=current_user,
        date_from=date_from,
        date_to=date_to,
    )
    return CalendarViewResponse.model_validate(result)
