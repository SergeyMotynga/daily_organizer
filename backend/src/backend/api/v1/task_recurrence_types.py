"""Endpoint-ы API v1 для типов повторения задач."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user, get_task_service
from backend.models.task import TaskRecurrenceType
from backend.models.user import User
from backend.schemas.task_recurrence_types import TaskRecurrenceTypeResponse
from backend.services.tasks import TaskService

router = APIRouter(prefix="/api/v1/task-recurrence-types", tags=["task-recurrence-types"])


@router.get("", response_model=list[TaskRecurrenceTypeResponse])
async def list_task_recurrence_types(
    _current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> list[TaskRecurrenceType]:
    """Возвращает активные системные типы повторения задач."""
    return await task_service.list_recurrence_types()
