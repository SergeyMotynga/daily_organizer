"""Repository для задач и статусов задач."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Select, and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.tasks import TaskSort, TaskStatusCode
from backend.dto.common import PaginationParams
from backend.dto.tasks import TaskCreateData, TaskListFilters
from backend.models.task import Task, TaskStatus


class TaskRepository:
    """CRUD и запросы для задач."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_active_statuses(self) -> list[TaskStatus]:
        """Возвращает активные системные статусы задач."""
        statement = (
            select(TaskStatus)
            .where(TaskStatus.is_active.is_(True))
            .order_by(asc(TaskStatus.sort_order))
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_active_status_by_code(self, code: str) -> TaskStatus | None:
        """Возвращает активный системный статус задачи по коду."""
        statement = select(TaskStatus).where(
            TaskStatus.code == code,
            TaskStatus.is_active.is_(True),
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_task(self, *, user_id: UUID, data: TaskCreateData) -> Task:
        """Создает задачу и подтягивает значения, сгенерированные БД."""
        task = Task(
            user_id=user_id,
            title=data.title,
            description=data.description,
            status_code=data.status.value if data.status is not None else None,
            planned_date=data.planned_date,
            planned_time=data.planned_time,
            deadline_date=data.deadline_date,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_for_user(self, *, task_id: UUID, user_id: UUID) -> Task | None:
        """Возвращает задачу пользователя или None."""
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def list_tasks_for_user(
        self,
        *,
        user_id: UUID,
        filters: TaskListFilters,
        pagination: PaginationParams,
    ) -> tuple[list[Task], int]:
        """Возвращает страницу задач пользователя и общее количество."""
        base_statement = self._apply_filters(
            select(Task).where(Task.user_id == user_id),
            filters,
        )

        total_statement = select(func.count()).select_from(base_statement.subquery())
        total = await self.db.scalar(total_statement)

        list_statement = (
            self._apply_sorting(base_statement, filters.sort)
            .limit(pagination.limit)
            .offset(pagination.offset)
        )
        result = await self.db.execute(list_statement)
        return list(result.scalars().all()), int(total or 0)

    async def list_today_view_candidates_for_user(
        self,
        *,
        user_id: UUID,
        today: date,
        deadline_to: date,
        completed_at_from: datetime,
        completed_at_to: datetime,
    ) -> list[Task]:
        """Возвращает задачи пользователя, которые могут попасть в экран Сегодня."""
        statement = (
            select(Task)
            .where(
                Task.user_id == user_id,
                or_(
                    and_(
                        Task.status_code == TaskStatusCode.todo.value,
                        or_(
                            Task.planned_date == today,
                            Task.planned_date.is_(None),
                            and_(
                                Task.deadline_date.is_not(None),
                                Task.deadline_date <= deadline_to,
                            ),
                        ),
                    ),
                    and_(
                        Task.status_code == TaskStatusCode.done.value,
                        Task.completed_at >= completed_at_from,
                        Task.completed_at < completed_at_to,
                    ),
                ),
            )
            .order_by(asc(Task.deadline_date).nulls_last(), desc(Task.created_at), desc(Task.id))
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def save_task(self, task: Task) -> Task:
        """Сохраняет изменения задачи и обновляет значения из БД."""
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task: Task) -> None:
        """Физически удаляет задачу."""
        await self.db.delete(task)
        await self.db.flush()

    def _apply_filters(
        self,
        statement: Select[tuple[Task]],
        filters: TaskListFilters,
    ) -> Select[tuple[Task]]:
        """Применяет технические фильтры списка задач."""
        statement = statement.where(
            Task.status_code.in_([status.value for status in filters.statuses])
        )

        if filters.planned_date_is_null:
            statement = statement.where(Task.planned_date.is_(None))
        else:
            if filters.planned_date_from is not None:
                statement = statement.where(Task.planned_date >= filters.planned_date_from)
            if filters.planned_date_to is not None:
                statement = statement.where(Task.planned_date <= filters.planned_date_to)

        if filters.deadline_date is not None:
            statement = statement.where(Task.deadline_date == filters.deadline_date)
        else:
            if filters.deadline_date_from is not None:
                statement = statement.where(Task.deadline_date >= filters.deadline_date_from)
            if filters.deadline_date_to is not None:
                statement = statement.where(Task.deadline_date <= filters.deadline_date_to)

        if filters.q is not None:
            query = f"%{filters.q}%"
            statement = statement.where(
                or_(
                    Task.title.ilike(query),
                    Task.description.ilike(query),
                )
            )

        return statement

    def _apply_sorting(
        self,
        statement: Select[tuple[Task]],
        sort: TaskSort,
    ) -> Select[tuple[Task]]:
        """Применяет сортировку списка задач."""
        if sort == TaskSort.created_at_asc:
            return statement.order_by(asc(Task.created_at), asc(Task.id))
        if sort == TaskSort.planned_date_asc:
            return statement.order_by(
                asc(Task.planned_date).nulls_last(),
                asc(Task.planned_time).nulls_last(),
                asc(Task.created_at),
            )
        if sort == TaskSort.deadline_date_asc:
            return statement.order_by(asc(Task.deadline_date).nulls_last(), asc(Task.created_at))

        return statement.order_by(desc(Task.created_at), desc(Task.id))
