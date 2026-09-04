"""Endpoint-ы API v1 для системных статусов задач."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user, get_task_service
from backend.models.task import TaskStatus
from backend.models.user import User
from backend.schemas.task_statuses import TaskStatusResponse
from backend.services.tasks import TaskService

router = APIRouter(prefix="/api/v1/task-statuses", tags=["task-statuses"])


@router.get("", response_model=list[TaskStatusResponse])
async def list_task_statuses(
    _current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> list[TaskStatus]:
    """Возвращает активные системные статусы задач."""
    return await task_service.list_statuses()
