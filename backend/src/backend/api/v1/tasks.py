"""Task endpoint-ы API v1."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.api.deps import get_current_user, get_task_service
from backend.api.query_params import normalize_optional_query_text, parse_csv_enum
from backend.domain.tasks import TaskDeadlinePreset, TaskListPreset, TaskSort, TaskStatusCode
from backend.dto.common import PaginationParams
from backend.dto.tasks import TaskCreateData, TaskListQuery, TaskUpdateData
from backend.models.task import Task
from backend.models.user import User
from backend.schemas.common import PaginationMeta
from backend.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from backend.services.tasks import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    """Создает задачу текущего пользователя."""
    return await task_service.create_task(
        user=current_user,
        data=TaskCreateData(
            title=payload.title,
            description=payload.description,
            planned_date=payload.planned_date,
            deadline_date=payload.deadline_date,
            status=payload.status,
        ),
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    preset: Annotated[TaskListPreset, Query()] = TaskListPreset.all,
    statuses: Annotated[str | None, Query()] = None,
    planned_date: Annotated[date | None, Query()] = None,
    deadline_date: Annotated[date | None, Query()] = None,
    deadline_preset: Annotated[TaskDeadlinePreset | None, Query()] = None,
    timezone: Annotated[str, Query(min_length=1, max_length=255)] = "UTC",
    q: Annotated[str | None, Query()] = None,
    sort: Annotated[TaskSort, Query()] = TaskSort.created_at_desc,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListResponse:
    """Возвращает список задач текущего пользователя."""
    result = await task_service.list_tasks(
        user=current_user,
        query=TaskListQuery(
            preset=preset,
            statuses=parse_csv_enum(statuses, TaskStatusCode, param_name="statuses"),
            planned_date=planned_date,
            deadline_date=deadline_date,
            deadline_preset=deadline_preset,
            timezone=timezone,
            q=normalize_optional_query_text(q),
            sort=sort,
        ),
        pagination=PaginationParams(limit=limit, offset=offset),
    )
    return TaskListResponse(
        items=[TaskResponse.model_validate(task) for task in result.items],
        pagination=PaginationMeta(limit=limit, offset=offset, total=result.total),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    """Возвращает задачу текущего пользователя."""
    return await task_service.get_task(user=current_user, task_id=task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> Task:
    """Частично изменяет задачу текущего пользователя."""
    return await task_service.update_task(
        user=current_user,
        task_id=task_id,
        data=TaskUpdateData(
            fields_set=frozenset(payload.model_fields_set),
            title=payload.title,
            description=payload.description,
            planned_date=payload.planned_date,
            deadline_date=payload.deadline_date,
            status=payload.status,
        ),
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    """Физически удаляет задачу текущего пользователя."""
    await task_service.delete_task(user=current_user, task_id=task_id)
