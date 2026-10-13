"""Task endpoint-ы API v1."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.api.deps import get_current_user, get_project_service, get_task_service
from backend.api.query_params import normalize_optional_query_text, parse_csv_enum
from backend.domain.tasks import TaskDeadlinePreset, TaskListPreset, TaskSort, TaskStatusCode
from backend.dto.common import PaginationParams
from backend.dto.projects import TaskMoveData
from backend.dto.tasks import TaskCreateData, TaskListQuery, TaskUpdateData
from backend.models.task import Task, TaskRecurrenceCompletion
from backend.models.user import User
from backend.schemas.common import PaginationMeta
from backend.schemas.projects import TaskMoveRequest
from backend.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskRecurrenceCompletionResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from backend.services.projects import ProjectService
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
            planned_time=payload.planned_time,
            deadline_date=payload.deadline_date,
            deadline_time=payload.deadline_time,
            recurrence_type_code=payload.recurrence_type_code,
            recurrence_interval=payload.recurrence_interval,
            recurrence_start_date=payload.recurrence_start_date,
            recurrence_end_date=payload.recurrence_end_date,
            status=payload.status,
            project_id=payload.project_id,
            project_column_id=payload.project_column_id,
        ),
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    preset: Annotated[TaskListPreset, Query()] = TaskListPreset.all,
    statuses: Annotated[str | None, Query()] = None,
    archived: Annotated[bool, Query()] = False,
    planned_date: Annotated[date | None, Query()] = None,
    planned_from: Annotated[date | None, Query()] = None,
    planned_to: Annotated[date | None, Query()] = None,
    deadline_date: Annotated[date | None, Query()] = None,
    deadline_preset: Annotated[TaskDeadlinePreset | None, Query()] = None,
    timezone: Annotated[str, Query(min_length=1, max_length=255)] = "UTC",
    q: Annotated[str | None, Query()] = None,
    sort: Annotated[TaskSort, Query()] = TaskSort.created_at_desc,
    project_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListResponse:
    """Возвращает список задач текущего пользователя."""
    result = await task_service.list_tasks(
        user=current_user,
        query=TaskListQuery(
            preset=preset,
            statuses=parse_csv_enum(statuses, TaskStatusCode, param_name="statuses"),
            archived=archived,
            planned_date=planned_date,
            planned_from=planned_from,
            planned_to=planned_to,
            deadline_date=deadline_date,
            deadline_preset=deadline_preset,
            timezone=timezone,
            q=normalize_optional_query_text(q),
            sort=sort,
            project_id=project_id,
        ),
        pagination=PaginationParams(limit=limit, offset=offset),
    )
    return TaskListResponse(
        items=[
            TaskResponse.model_validate(item.task).model_copy(
                update={"status": item.status, "occurrence_date": item.occurrence_date}
            )
            for item in result.items
        ],
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
            planned_time=payload.planned_time,
            deadline_date=payload.deadline_date,
            deadline_time=payload.deadline_time,
            recurrence_type_code=payload.recurrence_type_code,
            recurrence_interval=payload.recurrence_interval,
            recurrence_start_date=payload.recurrence_start_date,
            recurrence_end_date=payload.recurrence_end_date,
            status=payload.status,
            archived=payload.archived,
            project_id=payload.project_id,
            project_column_id=payload.project_column_id,
        ),
    )


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: UUID,
    payload: TaskMoveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> Task:
    """Атомарно перемещает карточку внутри проектной доски."""
    return await project_service.move_task(
        user=current_user,
        task_id=task_id,
        data=TaskMoveData(
            project_id=payload.project_id,
            target_column_id=payload.target_column_id,
            target_position=payload.target_position,
        ),
    )


@router.put(
    "/{task_id}/recurrence-completions/{occurrence_date}",
    response_model=TaskRecurrenceCompletionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def complete_task_recurrence(
    task_id: UUID,
    occurrence_date: date,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskRecurrenceCompletion:
    """Отмечает повторяющуюся задачу выполненной за дату."""
    return await task_service.complete_recurrence(
        user=current_user,
        task_id=task_id,
        occurrence_date=occurrence_date,
    )


@router.delete(
    "/{task_id}/recurrence-completions/{occurrence_date}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def uncomplete_task_recurrence(
    task_id: UUID,
    occurrence_date: date,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    """Снимает выполнение повторяющейся задачи за дату."""
    await task_service.uncomplete_recurrence(
        user=current_user,
        task_id=task_id,
        occurrence_date=occurrence_date,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    """Физически удаляет задачу текущего пользователя."""
    await task_service.delete_task(user=current_user, task_id=task_id)
