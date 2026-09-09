"""Repository для задач и статусов задач."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Date,
    Select,
    and_,
    asc,
    delete,
    desc,
    exists,
    false,
    func,
    literal,
    or_,
    select,
    true,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from backend.domain.tasks import TaskRecurrenceTypeCode, TaskSort, TaskStatusCode
from backend.dto.common import PaginationParams
from backend.dto.tasks import TaskCreateData, TaskListFilters
from backend.models.task import Task, TaskRecurrenceCompletion, TaskRecurrenceType, TaskStatus


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

    async def list_active_recurrence_types(self) -> list[TaskRecurrenceType]:
        """Возвращает активные системные типы повторения задач."""
        statement = (
            select(TaskRecurrenceType)
            .where(TaskRecurrenceType.is_active.is_(True))
            .order_by(asc(TaskRecurrenceType.sort_order))
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_active_recurrence_type_by_code(
        self,
        code: str,
    ) -> TaskRecurrenceType | None:
        """Возвращает активный системный тип повторения по коду."""
        statement = select(TaskRecurrenceType).where(
            TaskRecurrenceType.code == code,
            TaskRecurrenceType.is_active.is_(True),
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
            deadline_time=data.deadline_time,
            recurrence_type_code=data.recurrence_type_code.value,
            recurrence_interval=data.recurrence_interval,
            recurrence_start_date=data.recurrence_start_date,
            recurrence_end_date=data.recurrence_end_date,
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
                Task.archived_at.is_(None),
                or_(
                    and_(
                        Task.recurrence_type_code == TaskRecurrenceTypeCode.none.value,
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
                    ),
                    and_(
                        Task.recurrence_type_code != TaskRecurrenceTypeCode.none.value,
                        Task.recurrence_start_date.is_not(None),
                        Task.recurrence_start_date <= today,
                        or_(
                            Task.recurrence_end_date.is_(None),
                            Task.recurrence_end_date >= today,
                        ),
                    ),
                ),
            )
            .order_by(
                asc(Task.deadline_date).nulls_last(),
                asc(Task.deadline_time).nulls_last(),
                desc(Task.created_at),
                desc(Task.id),
            )
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def list_completed_recurrence_task_ids(
        self,
        *,
        task_ids: list[UUID],
        occurrence_date: date,
    ) -> set[UUID]:
        """Возвращает id повторяющихся задач, выполненных в указанную дату."""
        if not task_ids:
            return set()

        statement = select(TaskRecurrenceCompletion.task_id).where(
            TaskRecurrenceCompletion.task_id.in_(task_ids),
            TaskRecurrenceCompletion.occurrence_date == occurrence_date,
        )
        result = await self.db.execute(statement)
        return set(result.scalars().all())

    async def get_recurrence_completion(
        self,
        *,
        task_id: UUID,
        occurrence_date: date,
    ) -> TaskRecurrenceCompletion | None:
        """Возвращает факт выполнения повторения задачи за дату."""
        statement = select(TaskRecurrenceCompletion).where(
            TaskRecurrenceCompletion.task_id == task_id,
            TaskRecurrenceCompletion.occurrence_date == occurrence_date,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_recurrence_completion(
        self,
        *,
        task_id: UUID,
        occurrence_date: date,
        completed_at: datetime,
    ) -> TaskRecurrenceCompletion:
        """Создает факт выполнения повторяющейся задачи."""
        completion = TaskRecurrenceCompletion(
            task_id=task_id,
            occurrence_date=occurrence_date,
            completed_at=completed_at,
        )
        self.db.add(completion)
        await self.db.flush()
        await self.db.refresh(completion)
        return completion

    async def delete_recurrence_completion(
        self,
        completion: TaskRecurrenceCompletion,
    ) -> None:
        """Удаляет факт выполнения повторяющейся задачи."""
        await self.db.delete(completion)
        await self.db.flush()

    async def delete_recurrence_completions_for_task(self, *, task_id: UUID) -> None:
        """Удаляет всю историю выполнений задачи одним запросом."""
        await self.db.execute(
            delete(TaskRecurrenceCompletion).where(TaskRecurrenceCompletion.task_id == task_id)
        )

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
        status_values = [status.value for status in filters.statuses]
        regular_conditions: list[ColumnElement[bool]] = [
            Task.recurrence_type_code == TaskRecurrenceTypeCode.none.value,
            Task.status_code.in_(status_values),
        ]
        if filters.planned_date_is_null:
            regular_conditions.append(Task.planned_date.is_(None))
        else:
            if filters.planned_date_from is not None:
                regular_conditions.append(Task.planned_date >= filters.planned_date_from)
            if filters.planned_date_to is not None:
                regular_conditions.append(Task.planned_date <= filters.planned_date_to)

        if filters.recurrence_date is not None:
            completion_exists = exists().where(
                TaskRecurrenceCompletion.task_id == Task.id,
                TaskRecurrenceCompletion.occurrence_date == filters.recurrence_date,
            )
            recurring_status_conditions: list[ColumnElement[bool]] = []
            if TaskStatusCode.todo.value in status_values:
                recurring_status_conditions.append(~completion_exists)
            if TaskStatusCode.done.value in status_values:
                recurring_status_conditions.append(completion_exists)
            recurring_status_filter = (
                or_(*recurring_status_conditions) if recurring_status_conditions else false()
            )
            task_context_filter = or_(
                and_(*regular_conditions),
                and_(
                    self._recurrence_due_clause(filters.recurrence_date),
                    recurring_status_filter,
                ),
            )
        elif filters.archived:
            task_context_filter = or_(
                and_(*regular_conditions),
                and_(
                    Task.recurrence_type_code != TaskRecurrenceTypeCode.none.value,
                    Task.status_code.in_(status_values),
                ),
            )
        else:
            task_context_filter = and_(*regular_conditions)

        statement = statement.where(
            task_context_filter,
            Task.archived_at.is_not(None) if filters.archived else Task.archived_at.is_(None),
        )

        if filters.deadline_date is not None:
            statement = statement.where(Task.deadline_date == filters.deadline_date)
        elif filters.overdue_date is not None and filters.overdue_time is not None:
            statement = statement.where(
                or_(
                    Task.deadline_date < filters.overdue_date,
                    and_(
                        Task.deadline_date == filters.overdue_date,
                        Task.deadline_time.is_not(None),
                        Task.deadline_time < filters.overdue_time,
                    ),
                )
            )
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

    def _recurrence_due_clause(self, occurrence_date: date) -> ColumnElement[bool]:
        """Строит SQL-условие простого повторения для одной даты."""
        occurrence = literal(occurrence_date, type_=Date())
        days_since_start = occurrence - Task.recurrence_start_date
        weekdays_due = true() if occurrence_date.weekday() < 5 else false()
        return and_(
            Task.recurrence_type_code != TaskRecurrenceTypeCode.none.value,
            Task.recurrence_start_date.is_not(None),
            Task.recurrence_start_date <= occurrence_date,
            or_(
                Task.recurrence_end_date.is_(None),
                Task.recurrence_end_date >= occurrence_date,
            ),
            or_(
                and_(
                    Task.recurrence_type_code == TaskRecurrenceTypeCode.daily.value,
                    days_since_start % Task.recurrence_interval == 0,
                ),
                and_(
                    Task.recurrence_type_code == TaskRecurrenceTypeCode.weekdays.value,
                    weekdays_due,
                ),
                and_(
                    Task.recurrence_type_code == TaskRecurrenceTypeCode.weekly.value,
                    days_since_start % (Task.recurrence_interval * 7) == 0,
                ),
            ),
        )

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
            return statement.order_by(
                asc(Task.deadline_date).nulls_last(),
                asc(Task.deadline_time).nulls_last(),
                asc(Task.created_at),
                asc(Task.id),
            )

        return statement.order_by(desc(Task.created_at), desc(Task.id))
