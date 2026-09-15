"""Бизнес-логика task-модуля."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import utc_now
from backend.domain.tasks import (
    TaskDeadlinePreset,
    TaskListPreset,
    TaskRecurrenceTypeCode,
    TaskStatusCode,
)
from backend.dto.common import PaginationParams
from backend.dto.tasks import (
    CalendarTaskItem,
    CalendarViewResult,
    TaskCreateData,
    TaskListFilters,
    TaskListQuery,
    TaskUpdateData,
)
from backend.exceptions.tasks import (
    InvalidTaskRecurrenceCompletionError,
    InvalidTaskScheduleError,
    InvalidTimezoneError,
    TaskNotFoundError,
    TaskRecurrenceTypeNotFoundError,
    TaskStatusNotFoundError,
)
from backend.models.task import Task, TaskRecurrenceCompletion, TaskRecurrenceType, TaskStatus
from backend.models.user import User
from backend.repositories.tasks import TaskRepository
from backend.validators.tasks import validate_calendar_range, validate_task_title


@dataclass(frozen=True)
class TaskListItemResult:
    """Задача списка с контекстным статусом occurrence."""

    task: Task
    status: TaskStatusCode
    occurrence_date: date | None = None


@dataclass(frozen=True)
class TaskListResult:
    """Результат получения страницы задач."""

    items: list[TaskListItemResult]
    total: int


@dataclass(frozen=True)
class TodayTaskResult:
    """Задача в контексте конкретного локального дня."""

    task: Task
    status: TaskStatusCode
    occurrence_date: date | None = None


@dataclass(frozen=True)
class TodayViewBlocksResult:
    """Блоки задач для экрана Сегодня."""

    planned_today: list[TodayTaskResult]
    inbox: list[TodayTaskResult]
    soon_deadline: list[TodayTaskResult]
    today_deadline: list[TodayTaskResult]
    overdue: list[TodayTaskResult]
    done_today: list[TodayTaskResult]


@dataclass(frozen=True)
class TodayViewSummaryResult:
    """Сводка задач для экрана Сегодня."""

    total_active: int
    done_today: int
    overdue: int
    today_deadline: int


@dataclass(frozen=True)
class TodayViewResult:
    """Результат получения экрана Сегодня."""

    date: date
    summary: TodayViewSummaryResult
    blocks: TodayViewBlocksResult


class TaskService:
    """Координирует task-сценарии и транзакции."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.tasks = TaskRepository(db)

    async def list_statuses(self) -> list[TaskStatus]:
        """Возвращает активные системные статусы задач."""
        return await self.tasks.list_active_statuses()

    async def list_recurrence_types(self) -> list[TaskRecurrenceType]:
        """Возвращает активные системные типы повторения задач."""
        return await self.tasks.list_active_recurrence_types()

    async def create_task(self, *, user: User, data: TaskCreateData) -> Task:
        """Создает задачу пользователя с учетом статуса и timestamp-ов."""
        recurrence_type = await self._get_active_recurrence_type_code(data.recurrence_type_code)
        status = await self._get_active_status_code(data.status or TaskStatusCode.todo)
        self._validate_schedule(
            deadline_date=data.deadline_date,
            deadline_time=data.deadline_time,
            recurrence_type=recurrence_type,
            recurrence_interval=data.recurrence_interval,
            recurrence_start_date=data.recurrence_start_date,
            recurrence_end_date=data.recurrence_end_date,
        )
        if recurrence_type != TaskRecurrenceTypeCode.none and status != TaskStatusCode.todo:
            raise InvalidTaskScheduleError()
        create_data = TaskCreateData(
            title=validate_task_title(data.title),
            description=data.description,
            planned_date=data.planned_date,
            planned_time=data.planned_time,
            deadline_date=data.deadline_date,
            deadline_time=data.deadline_time,
            recurrence_type_code=recurrence_type,
            recurrence_interval=data.recurrence_interval,
            recurrence_start_date=data.recurrence_start_date,
            recurrence_end_date=data.recurrence_end_date,
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
        timezone = self._get_timezone(query.timezone)
        local_now = utc_now().astimezone(timezone)
        filters = self._build_filters(query, local_now)
        items, total = await self.tasks.list_tasks_for_user(
            user_id=user.id,
            filters=filters,
            pagination=pagination,
        )
        recurring_task_ids = [
            task.id
            for task in items
            if filters.recurrence_date is not None
            and task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
        ]
        completed_recurring_task_ids = (
            await self.tasks.list_completed_recurrence_task_ids(
                task_ids=recurring_task_ids,
                occurrence_date=filters.recurrence_date,
            )
            if filters.recurrence_date is not None
            else set()
        )
        result_items = [
            TaskListItemResult(
                task=task,
                status=(
                    TaskStatusCode.done
                    if task.id in completed_recurring_task_ids
                    else TaskStatusCode(task.status_code)
                ),
                occurrence_date=(
                    filters.recurrence_date
                    if task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
                    else None
                ),
            )
            for task in items
        ]
        return TaskListResult(items=result_items, total=total)

    async def get_today_view(self, *, user: User, timezone_name: str) -> TodayViewResult:
        """Возвращает собранный экран Сегодня для задач пользователя."""
        timezone = self._get_timezone(timezone_name)
        local_now = utc_now().astimezone(timezone)
        today = local_now.date()
        deadline_to = today + timedelta(days=3)
        completed_at_from, completed_at_to = self._local_day_bounds_utc(today, timezone)

        tasks = await self.tasks.list_today_view_candidates_for_user(
            user_id=user.id,
            today=today,
            deadline_to=deadline_to,
            completed_at_from=completed_at_from,
            completed_at_to=completed_at_to,
        )
        recurring_task_ids = [
            task.id
            for task in tasks
            if task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
        ]
        completed_recurring_task_ids = await self.tasks.list_completed_recurrence_task_ids(
            task_ids=recurring_task_ids,
            occurrence_date=today,
        )
        blocks = self._build_today_view_blocks(
            tasks,
            today,
            deadline_to,
            local_now.time(),
            completed_recurring_task_ids,
        )
        active_tasks = (
            blocks.planned_today
            + blocks.inbox
            + blocks.soon_deadline
            + blocks.today_deadline
            + blocks.overdue
        )
        summary = TodayViewSummaryResult(
            total_active=len({item.task.id for item in active_tasks}),
            done_today=len(blocks.done_today),
            overdue=len(blocks.overdue),
            today_deadline=len(blocks.today_deadline),
        )

        return TodayViewResult(date=today, summary=summary, blocks=blocks)

    async def get_calendar_view(
        self,
        *,
        user: User,
        date_from: date,
        date_to: date,
    ) -> CalendarViewResult:
        """Собирает задачи, дедлайны и повторения календарного диапазона."""
        validate_calendar_range(date_from, date_to)
        tasks = await self.tasks.list_calendar_candidates_for_user(
            user_id=user.id,
            date_from=date_from,
            date_to=date_to,
        )
        recurring_task_ids = [
            task.id
            for task in tasks
            if task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
        ]
        completion_rows = await self.tasks.list_recurrence_completions_for_range(
            task_ids=recurring_task_ids,
            date_from=date_from,
            date_to=date_to,
        )
        completed_occurrences = {
            (completion.task_id, completion.occurrence_date) for completion in completion_rows
        }

        planned: list[CalendarTaskItem] = []
        deadlines: list[CalendarTaskItem] = []
        recurrences: list[CalendarTaskItem] = []
        for task in tasks:
            status = TaskStatusCode(task.status_code)
            is_recurring = task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
            if (
                not is_recurring
                and task.planned_date is not None
                and date_from <= task.planned_date <= date_to
            ):
                planned.append(CalendarTaskItem(task=task, status=status))
            if task.deadline_date is not None and date_from <= task.deadline_date <= date_to:
                deadlines.append(CalendarTaskItem(task=task, status=status))
            if not is_recurring:
                continue

            occurrence_date = max(date_from, task.recurrence_start_date or date_from)
            recurrence_end = min(date_to, task.recurrence_end_date or date_to)
            while occurrence_date <= recurrence_end:
                if self._is_recurrence_due(task, occurrence_date):
                    occurrence_status = (
                        TaskStatusCode.done
                        if (task.id, occurrence_date) in completed_occurrences
                        else TaskStatusCode.todo
                    )
                    recurrences.append(
                        CalendarTaskItem(
                            task=task,
                            status=occurrence_status,
                            occurrence_date=occurrence_date,
                        )
                    )
                occurrence_date += timedelta(days=1)

        planned.sort(
            key=lambda item: (
                item.task.planned_date or date.max,
                item.task.planned_time or time.max,
                item.task.created_at,
                str(item.task.id),
            )
        )
        deadlines.sort(
            key=lambda item: (
                item.task.deadline_date or date.max,
                item.task.deadline_time or time.max,
                item.task.created_at,
                str(item.task.id),
            )
        )
        recurrences.sort(
            key=lambda item: (
                item.occurrence_date or date.max,
                item.task.planned_time or time.max,
                item.task.created_at,
                str(item.task.id),
            )
        )
        return CalendarViewResult(
            date_from=date_from,
            date_to=date_to,
            planned=planned,
            deadlines=deadlines,
            recurrences=recurrences,
        )

    async def update_task(self, *, user: User, task_id: UUID, data: TaskUpdateData) -> Task:
        """Частично изменяет задачу пользователя."""
        task = await self.get_task(user=user, task_id=task_id)
        was_recurring = task.recurrence_type_code != TaskRecurrenceTypeCode.none.value

        recurrence_type = TaskRecurrenceTypeCode(task.recurrence_type_code)
        if data.has("recurrence_type_code"):
            if data.recurrence_type_code is None:
                raise TaskRecurrenceTypeNotFoundError()
            recurrence_type = await self._get_active_recurrence_type_code(data.recurrence_type_code)

        recurrence_interval = (
            data.recurrence_interval
            if data.has("recurrence_interval")
            else task.recurrence_interval
        )
        if recurrence_interval is None:
            raise InvalidTaskScheduleError()
        recurrence_start_date = (
            data.recurrence_start_date
            if data.has("recurrence_start_date")
            else task.recurrence_start_date
        )
        recurrence_end_date = (
            data.recurrence_end_date
            if data.has("recurrence_end_date")
            else task.recurrence_end_date
        )
        deadline_date = data.deadline_date if data.has("deadline_date") else task.deadline_date
        deadline_time = data.deadline_time if data.has("deadline_time") else task.deadline_time
        self._validate_schedule(
            deadline_date=deadline_date,
            deadline_time=deadline_time,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_start_date=recurrence_start_date,
            recurrence_end_date=recurrence_end_date,
        )

        if data.has("title"):
            task.title = validate_task_title(data.title)
        if data.has("description"):
            task.description = data.description
        if data.has("planned_date"):
            task.planned_date = data.planned_date
        if data.has("planned_time"):
            task.planned_time = data.planned_time
        if data.has("deadline_date"):
            task.deadline_date = data.deadline_date
        if data.has("deadline_time"):
            task.deadline_time = data.deadline_time
        if data.has("recurrence_type_code"):
            task.recurrence_type_code = recurrence_type.value
        if data.has("recurrence_interval"):
            task.recurrence_interval = recurrence_interval
        if data.has("recurrence_start_date"):
            task.recurrence_start_date = data.recurrence_start_date
        if data.has("recurrence_end_date"):
            task.recurrence_end_date = data.recurrence_end_date
        if data.has("status"):
            if data.status is None:
                raise TaskStatusNotFoundError()
            if recurrence_type != TaskRecurrenceTypeCode.none:
                if data.status != TaskStatusCode.todo:
                    raise InvalidTaskScheduleError()
            else:
                status = await self._get_active_status_code(data.status)
                task.status_code = status.value
                self._apply_status_timestamps(task, status)
        if recurrence_type != TaskRecurrenceTypeCode.none:
            task.status_code = TaskStatusCode.todo.value
            task.completed_at = None
        if data.has("archived"):
            task.archived_at = utc_now() if data.archived else None

        try:
            if was_recurring and recurrence_type == TaskRecurrenceTypeCode.none:
                await self.tasks.delete_recurrence_completions_for_task(task_id=task.id)
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

    async def complete_recurrence(
        self,
        *,
        user: User,
        task_id: UUID,
        occurrence_date: date,
    ) -> TaskRecurrenceCompletion:
        """Отмечает повторяющуюся задачу выполненной в указанную дату."""
        task = await self.get_task(user=user, task_id=task_id)
        self._validate_recurrence_completion(task, occurrence_date)
        existing_completion = await self.tasks.get_recurrence_completion(
            task_id=task.id,
            occurrence_date=occurrence_date,
        )
        if existing_completion is not None:
            return existing_completion

        try:
            completion = await self.tasks.create_recurrence_completion(
                task_id=task.id,
                occurrence_date=occurrence_date,
                completed_at=utc_now(),
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return completion

    async def uncomplete_recurrence(
        self,
        *,
        user: User,
        task_id: UUID,
        occurrence_date: date,
    ) -> None:
        """Снимает выполнение повторяющейся задачи за указанную дату."""
        task = await self.get_task(user=user, task_id=task_id)
        self._validate_recurrence_completion(task, occurrence_date)
        completion = await self.tasks.get_recurrence_completion(
            task_id=task.id,
            occurrence_date=occurrence_date,
        )
        if completion is None:
            return

        try:
            await self.tasks.delete_recurrence_completion(completion)
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

    async def _get_active_recurrence_type_code(
        self,
        recurrence_type: TaskRecurrenceTypeCode,
    ) -> TaskRecurrenceTypeCode:
        """Проверяет тип повторения по активному системному справочнику."""
        existing_type = await self.tasks.get_active_recurrence_type_by_code(recurrence_type.value)
        if existing_type is None:
            raise TaskRecurrenceTypeNotFoundError()

        return recurrence_type

    def _build_filters(self, query: TaskListQuery, local_now: datetime) -> TaskListFilters:
        """Преобразует продуктовый query в технические фильтры repository."""
        today = local_now.date()
        statuses = query.statuses or [TaskStatusCode.todo, TaskStatusCode.done]
        planned_date_from = None
        planned_date_to = None
        planned_date_is_null = False
        deadline_date_from = None
        deadline_date_to = None
        overdue_date = None
        overdue_time = None
        recurrence_date = None

        if query.preset == TaskListPreset.today:
            planned_date_from = today
            planned_date_to = today
            recurrence_date = today
        elif query.preset == TaskListPreset.tomorrow:
            tomorrow = today + timedelta(days=1)
            planned_date_from = tomorrow
            planned_date_to = tomorrow
            recurrence_date = tomorrow
        elif query.preset == TaskListPreset.week:
            planned_date_from = today
            planned_date_to = today + timedelta(days=6)
            recurrence_date = today
        elif query.preset == TaskListPreset.no_date:
            planned_date_is_null = True

        if query.planned_date is not None:
            planned_date_from = query.planned_date
            planned_date_to = query.planned_date
            planned_date_is_null = False
            recurrence_date = query.planned_date
        elif query.planned_from is not None or query.planned_to is not None:
            planned_date_from = query.planned_from
            planned_date_to = query.planned_to
            planned_date_is_null = False
            recurrence_date = None

        if query.deadline_preset is not None and query.deadline_date is None:
            statuses = [status for status in statuses if status == TaskStatusCode.todo]
            if query.deadline_preset == TaskDeadlinePreset.overdue:
                overdue_date = today
                overdue_time = local_now.time()
            elif query.deadline_preset == TaskDeadlinePreset.today:
                deadline_date_from = today
                deadline_date_to = today
            elif query.deadline_preset == TaskDeadlinePreset.soon:
                deadline_date_from = today + timedelta(days=1)
                deadline_date_to = today + timedelta(days=3)

        if query.deadline_date is not None:
            deadline_date_from = None
            deadline_date_to = None
            overdue_date = None
            overdue_time = None

        return TaskListFilters(
            statuses=statuses,
            archived=query.archived,
            planned_date_from=planned_date_from,
            planned_date_to=planned_date_to,
            planned_date_is_null=planned_date_is_null,
            deadline_date=query.deadline_date,
            deadline_date_from=deadline_date_from,
            deadline_date_to=deadline_date_to,
            overdue_date=overdue_date,
            overdue_time=overdue_time,
            recurrence_date=recurrence_date,
            q=query.q,
            sort=query.sort,
        )

    def _apply_status_timestamps(self, task: Task, status: TaskStatusCode) -> None:
        """Применяет timestamp-правила при изменении статуса."""
        now = utc_now()
        if status == TaskStatusCode.done:
            task.completed_at = now
        elif status == TaskStatusCode.todo:
            task.completed_at = None

    def _build_today_view_blocks(
        self,
        tasks: list[Task],
        today: date,
        deadline_to: date,
        current_time: time,
        completed_recurring_task_ids: set[UUID],
    ) -> TodayViewBlocksResult:
        """Раскладывает задачи по блокам Сегодня без лишнего дублирования."""
        planned_today: list[TodayTaskResult] = []
        inbox: list[TodayTaskResult] = []
        soon_deadline: list[TodayTaskResult] = []
        today_deadline: list[TodayTaskResult] = []
        overdue: list[TodayTaskResult] = []
        done_today: list[TodayTaskResult] = []

        for task in tasks:
            is_recurring = task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
            if is_recurring and not self._is_recurrence_due(task, today):
                continue

            status = (
                TaskStatusCode.done
                if is_recurring and task.id in completed_recurring_task_ids
                else TaskStatusCode(task.status_code)
            )
            item = TodayTaskResult(
                task=task,
                status=status,
                occurrence_date=today if is_recurring else None,
            )

            if status == TaskStatusCode.done:
                done_today.append(item)
                continue

            if is_recurring or task.planned_date == today or task.deadline_date == today:
                planned_today.append(item)

            is_overdue_today = (
                task.deadline_date == today
                and task.deadline_time is not None
                and task.deadline_time < current_time
            )
            if task.deadline_date is not None and (task.deadline_date < today or is_overdue_today):
                overdue.append(item)
                continue
            elif task.deadline_date == today:
                today_deadline.append(item)
                continue

            if is_recurring or task.planned_date == today:
                continue

            if task.deadline_date is not None and task.deadline_date <= deadline_to:
                soon_deadline.append(item)
            elif task.planned_date is None:
                inbox.append(item)

        return TodayViewBlocksResult(
            planned_today=self._sort_tasks_by_created_desc(planned_today),
            inbox=self._sort_tasks_by_created_desc(inbox),
            soon_deadline=self._sort_tasks_by_deadline_asc(soon_deadline),
            today_deadline=self._sort_tasks_by_created_desc(today_deadline),
            overdue=self._sort_tasks_by_deadline_asc(overdue),
            done_today=self._sort_tasks_by_created_desc(done_today),
        )

    def _sort_tasks_by_created_desc(
        self,
        tasks: list[TodayTaskResult],
    ) -> list[TodayTaskResult]:
        """Сортирует задачи от новых к старым."""
        return sorted(
            tasks,
            key=lambda item: (item.task.created_at, str(item.task.id)),
            reverse=True,
        )

    def _sort_tasks_by_deadline_asc(
        self,
        tasks: list[TodayTaskResult],
    ) -> list[TodayTaskResult]:
        """Сортирует задачи по срочности дедлайна."""
        return sorted(
            tasks,
            key=lambda item: (
                item.task.deadline_date or date.max,
                item.task.deadline_time or time.max,
                -item.task.created_at.timestamp(),
                str(item.task.id),
            ),
        )

    def _validate_schedule(
        self,
        *,
        deadline_date: date | None,
        deadline_time: time | None,
        recurrence_type: TaskRecurrenceTypeCode,
        recurrence_interval: int,
        recurrence_start_date: date | None,
        recurrence_end_date: date | None,
    ) -> None:
        """Проверяет связанные поля дедлайна и простого повторения."""
        if deadline_time is not None and deadline_date is None:
            raise InvalidTaskScheduleError()
        if recurrence_interval < 1:
            raise InvalidTaskScheduleError()
        if recurrence_type == TaskRecurrenceTypeCode.weekdays and recurrence_interval != 1:
            raise InvalidTaskScheduleError()
        if recurrence_type != TaskRecurrenceTypeCode.none and recurrence_start_date is None:
            raise InvalidTaskScheduleError()
        if (
            recurrence_start_date is not None
            and recurrence_end_date is not None
            and recurrence_end_date < recurrence_start_date
        ):
            raise InvalidTaskScheduleError()

    def _validate_recurrence_completion(self, task: Task, occurrence_date: date) -> None:
        """Проверяет, что задача активна и повторяется в указанную дату."""
        if task.archived_at is not None or not self._is_recurrence_due(task, occurrence_date):
            raise InvalidTaskRecurrenceCompletionError()

    def _is_recurrence_due(self, task: Task, occurrence_date: date) -> bool:
        """Проверяет попадание даты в простое правило повторения задачи."""
        recurrence_type = TaskRecurrenceTypeCode(task.recurrence_type_code)
        start_date = task.recurrence_start_date
        if recurrence_type == TaskRecurrenceTypeCode.none or start_date is None:
            return False
        if occurrence_date < start_date:
            return False
        if task.recurrence_end_date is not None and occurrence_date > task.recurrence_end_date:
            return False

        days_since_start = (occurrence_date - start_date).days
        if recurrence_type == TaskRecurrenceTypeCode.daily:
            return days_since_start % task.recurrence_interval == 0
        if recurrence_type == TaskRecurrenceTypeCode.weekdays:
            return occurrence_date.weekday() < 5
        return days_since_start % (7 * task.recurrence_interval) == 0

    def _get_timezone(self, timezone_name: str) -> ZoneInfo:
        """Возвращает IANA timezone или выбрасывает доменную ошибку."""
        try:
            return ZoneInfo(timezone_name.strip())
        except ZoneInfoNotFoundError as error:
            raise InvalidTimezoneError() from error

    def _local_day_bounds_utc(self, today: date, timezone: ZoneInfo) -> tuple[datetime, datetime]:
        """Считает UTC-границы локального дня пользователя."""
        local_day_start = datetime.combine(today, time.min, tzinfo=timezone)
        local_next_day_start = datetime.combine(
            today + timedelta(days=1),
            time.min,
            tzinfo=timezone,
        )
        return local_day_start.astimezone(UTC), local_next_day_start.astimezone(UTC)
