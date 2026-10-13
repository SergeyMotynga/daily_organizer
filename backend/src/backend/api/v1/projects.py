"""Project endpoint-ы API v1."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.api.deps import get_current_user, get_project_service
from backend.api.query_params import normalize_optional_query_text
from backend.dto.projects import (
    ProjectColumnCreateData,
    ProjectColumnUpdateData,
    ProjectCreateData,
    ProjectSummaryData,
    ProjectUpdateData,
)
from backend.models.project import ProjectColumn
from backend.models.task import Task
from backend.models.user import User
from backend.schemas.projects import (
    ProjectColumnCreateRequest,
    ProjectColumnResponse,
    ProjectColumnsReorderRequest,
    ProjectColumnUpdateRequest,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectTasksBulkMoveRequest,
    ProjectTasksBulkStatusRequest,
    ProjectUpdateRequest,
)
from backend.schemas.tasks import TaskResponse
from backend.services.projects import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _project_response(summary: ProjectSummaryData) -> ProjectResponse:
    """Преобразует проектный DTO в HTTP-ответ."""
    progress = (
        round(summary.completed_task_count * 100 / summary.task_count) if summary.task_count else 0
    )
    return ProjectResponse.model_validate(summary.project).model_copy(
        update={
            "task_count": summary.task_count,
            "completed_task_count": summary.completed_task_count,
            "progress_percent": progress,
        }
    )


def _project_detail_response(summary: ProjectSummaryData) -> ProjectDetailResponse:
    """Добавляет колонки проекта к его агрегатам."""
    base = _project_response(summary)
    return ProjectDetailResponse(
        **base.model_dump(),
        columns=[ProjectColumnResponse.model_validate(item) for item in summary.project.columns],
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    archived: Annotated[bool, Query()] = False,
    q: Annotated[str | None, Query()] = None,
) -> ProjectListResponse:
    """Возвращает активные или архивные проекты текущего пользователя."""
    items = await project_service.list_projects(
        user=current_user,
        archived=archived,
        q=normalize_optional_query_text(q),
    )
    return ProjectListResponse(items=[_project_response(item) for item in items])


@router.post("", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectDetailResponse:
    """Создает проект со стандартными колонками."""
    project = await project_service.create_project(
        user=current_user,
        data=ProjectCreateData(title=payload.title, description=payload.description),
    )
    summary = await project_service.get_project_summary(user=current_user, project_id=project.id)
    return _project_detail_response(summary)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectDetailResponse:
    """Возвращает проект с колонками и агрегатами."""
    summary = await project_service.get_project_summary(user=current_user, project_id=project_id)
    return _project_detail_response(summary)


@router.patch("/{project_id}", response_model=ProjectDetailResponse)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectDetailResponse:
    """Изменяет проект или его архивное состояние."""
    await project_service.update_project(
        user=current_user,
        project_id=project_id,
        data=ProjectUpdateData(
            fields_set=frozenset(payload.model_fields_set),
            title=payload.title,
            description=payload.description,
            archived=payload.archived,
        ),
    )
    summary = await project_service.get_project_summary(user=current_user, project_id=project_id)
    return _project_detail_response(summary)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Удаляет проект, предварительно отвязав его задачи."""
    await project_service.delete_project(user=current_user, project_id=project_id)


@router.get("/{project_id}/columns", response_model=list[ProjectColumnResponse])
async def list_project_columns(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectColumn]:
    """Возвращает колонки проекта."""
    return await project_service.list_columns(user=current_user, project_id=project_id)


@router.post(
    "/{project_id}/columns",
    response_model=ProjectColumnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_column(
    project_id: UUID,
    payload: ProjectColumnCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectColumn:
    """Добавляет колонку в конец доски."""
    return await project_service.create_column(
        user=current_user,
        project_id=project_id,
        data=ProjectColumnCreateData(
            title=payload.title,
            is_completion_column=payload.is_completion_column,
        ),
    )


@router.put("/{project_id}/columns/order", response_model=list[ProjectColumnResponse])
async def reorder_project_columns(
    project_id: UUID,
    payload: ProjectColumnsReorderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectColumn]:
    """Атомарно изменяет порядок всех колонок проекта."""
    return await project_service.reorder_columns(
        user=current_user,
        project_id=project_id,
        column_ids=payload.column_ids,
    )


@router.patch(
    "/{project_id}/columns/{column_id}",
    response_model=ProjectColumnResponse,
)
async def update_project_column(
    project_id: UUID,
    column_id: UUID,
    payload: ProjectColumnUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectColumn:
    """Изменяет название или назначение колонки."""
    return await project_service.update_column(
        user=current_user,
        project_id=project_id,
        column_id=column_id,
        data=ProjectColumnUpdateData(
            fields_set=frozenset(payload.model_fields_set),
            title=payload.title,
            is_completion_column=payload.is_completion_column,
        ),
    )


@router.delete(
    "/{project_id}/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project_column(
    project_id: UUID,
    column_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Удаляет пустую незавершающую колонку."""
    await project_service.delete_column(
        user=current_user,
        project_id=project_id,
        column_id=column_id,
    )


@router.post("/{project_id}/tasks/bulk-move", response_model=list[TaskResponse])
async def bulk_move_project_tasks(
    project_id: UUID,
    payload: ProjectTasksBulkMoveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[Task]:
    """Массово перемещает задачи в выбранную колонку."""
    return await project_service.bulk_move_tasks(
        user=current_user,
        project_id=project_id,
        task_ids=payload.task_ids,
        target_column_id=payload.target_column_id,
    )


@router.post("/{project_id}/tasks/bulk-status", response_model=list[TaskResponse])
async def bulk_set_project_task_status(
    project_id: UUID,
    payload: ProjectTasksBulkStatusRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[Task]:
    """Массово синхронизирует выполнение и проектный этап."""
    return await project_service.bulk_set_status(
        user=current_user,
        project_id=project_id,
        task_ids=payload.task_ids,
        status=payload.status,
    )
