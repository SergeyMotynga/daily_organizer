"""Бизнес-логика task-модуля."""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import utc_now
from backend.domain.tasks import TaskListPreset, TaskStatusCode
from backend.dto.common import PaginationParams
from backend.dto.tasks import TaskCreateData, TaskListFilters, TaskListQuery, TaskUpdateData
from backend.exceptions.tasks import TaskNotFoundError, TaskStatusNotFoundError
from backend.models.task import Task, TaskStatus
from backend.models.user import User
from backend.repositories.tasks import TaskRepository
from backend.validators.tasks import validate_task_title


@dataclass(frozen=True)
class TaskListResult:
    """Результат получения страницы задач."""

    items: list[Task]
    total: int


class TaskService:
    """Координирует task-сценарии и транзакции."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.tasks = TaskRepository(db)

    async def list_statuses(self) -> list[TaskStatus]:
        """Возвращает активные системные статусы задач."""
        return await self.tasks.list_active_statuses()

    async def create_task(self, *, user: User, data: TaskCreateData) -> Task:
        """Создает задачу пользователя с учетом статуса и timestamp-ов."""
        status = await self._get_active_status_code(data.status or TaskStatusCode.todo)
        create_data = TaskCreateData(
            title=validate_task_title(data.title),
            description=data.description,
            planned_date=data.planned_date,
            deadline_date=data.deadline_date,
            status=status,
        )

        try:
            task = await self.tasks.create_task(user_id=user.id, data=create_data)
            self._apply_status_timestamps(task, status)
            task = await self.tasks.save_task(task)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return task

    async def get_task(self, *, user: User, task_id: UUID) -> Task:
        """Возвращает задачу пользователя или выбрасывает 404."""
        task = await self.tasks.get_task_for_user(task_id=task_id, user_id=user.id)
        if task is None:
            raise TaskNotFoundError()

        return task

    async def list_tasks(
        self,
        *,
        user: User,
        query: TaskListQuery,
        pagination: PaginationParams,
    ) -> TaskListResult:
        """Возвращает страницу задач пользователя."""
        filters = self._build_filters(query, utc_now().date())
        items, total = await self.tasks.list_tasks_for_user(
            user_id=user.id,
            filters=filters,
            pagination=pagination,
        )
        return TaskListResult(items=items, total=total)

    async def update_task(self, *, user: User, task_id: UUID, data: TaskUpdateData) -> Task:
        """Частично изменяет задачу пользователя."""
        task = await self.get_task(user=user, task_id=task_id)

        if data.has("title"):
            task.title = validate_task_title(data.title)
        if data.has("description"):
            task.description = data.description
        if data.has("planned_date"):
            task.planned_date = data.planned_date
        if data.has("deadline_date"):
            task.deadline_date = data.deadline_date
        if data.has("status"):
            if data.status is None:
                raise TaskStatusNotFoundError()
            status = await self._get_active_status_code(data.status)
            task.status_code = status.value
            self._apply_status_timestamps(task, status)

        try:
            task = await self.tasks.save_task(task)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return task

    async def delete_task(self, *, user: User, task_id: UUID) -> None:
        """Физически удаляет задачу пользователя."""
        task = await self.get_task(user=user, task_id=task_id)

        try:
            await self.tasks.delete_task(task)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def _get_active_status_code(self, status: TaskStatusCode) -> TaskStatusCode:
        """Проверяет, что статус есть в активном системном справочнике."""
        existing_status = await self.tasks.get_active_status_by_code(status.value)
        if existing_status is None:
            raise TaskStatusNotFoundError()

        return status

    def _build_filters(self, query: TaskListQuery, today: date) -> TaskListFilters:
        """Преобразует продуктовый query в технические фильтры repository."""
        statuses = query.statuses or [TaskStatusCode.todo, TaskStatusCode.done]
        planned_date_from = None
        planned_date_to = None
        planned_date_is_null = False

        if query.preset == TaskListPreset.today:
            planned_date_from = today
            planned_date_to = today
        elif query.preset == TaskListPreset.tomorrow:
            tomorrow = today + timedelta(days=1)
            planned_date_from = tomorrow
            planned_date_to = tomorrow
        elif query.preset == TaskListPreset.week:
            planned_date_from = today
            planned_date_to = today + timedelta(days=6)
        elif query.preset == TaskListPreset.no_date:
            planned_date_is_null = True

        if query.planned_date is not None:
            planned_date_from = query.planned_date
            planned_date_to = query.planned_date
            planned_date_is_null = False

        return TaskListFilters(
            statuses=statuses,
            planned_date_from=planned_date_from,
            planned_date_to=planned_date_to,
            planned_date_is_null=planned_date_is_null,
            deadline_date=query.deadline_date,
            q=query.q,
            sort=query.sort,
        )

    def _apply_status_timestamps(self, task: Task, status: TaskStatusCode) -> None:
        """Применяет timestamp-правила при изменении статуса."""
        now = utc_now()
        if status == TaskStatusCode.done:
            task.completed_at = now
        elif status == TaskStatusCode.archived:
            task.archived_at = now
        elif status == TaskStatusCode.todo:
            task.completed_at = None
            task.archived_at = None
