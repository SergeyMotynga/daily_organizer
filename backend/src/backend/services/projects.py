"""Бизнес-логика личных проектов и Kanban-колонок."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import utc_now
from backend.domain.tasks import TaskRecurrenceTypeCode, TaskStatusCode
from backend.dto.projects import (
    ProjectColumnCreateData,
    ProjectColumnUpdateData,
    ProjectCreateData,
    ProjectSummaryData,
    ProjectUpdateData,
    TaskMoveData,
)
from backend.exceptions.projects import (
    InvalidProjectColumnOrderError,
    InvalidProjectColumnTitleError,
    InvalidProjectTitleError,
    InvalidTaskProjectError,
    ProjectColumnNotEmptyError,
    ProjectColumnNotFoundError,
    ProjectCompletionColumnRequiredError,
    ProjectNotFoundError,
    RecurringTaskCompletionColumnError,
)
from backend.exceptions.tasks import TaskNotFoundError
from backend.models.project import Project, ProjectColumn
from backend.models.task import Task
from backend.models.user import User
from backend.repositories.projects import ProjectRepository

DEFAULT_PROJECT_COLUMNS = (
    ("Бэклог", False),
    ("К выполнению", False),
    ("В работе", False),
    ("На проверке", False),
    ("Готово", True),
)


class ProjectService:
    """Координирует project-сценарии и транзакции."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.projects = ProjectRepository(db)

    async def list_projects(
        self,
        *,
        user: User,
        archived: bool,
        q: str | None = None,
    ) -> list[ProjectSummaryData]:
        """Возвращает активные или архивные проекты пользователя."""
        return await self.projects.list_projects_for_user(
            user_id=user.id,
            archived=archived,
            q=q,
        )

    async def get_project_summary(self, *, user: User, project_id: UUID) -> ProjectSummaryData:
        """Возвращает проект с колонками и агрегатами или 404."""
        result = await self.projects.get_project_summary(project_id=project_id, user_id=user.id)
        if result is None:
            raise ProjectNotFoundError()
        return result

    async def create_project(self, *, user: User, data: ProjectCreateData) -> Project:
        """Создает проект и пять стандартных колонок одной транзакцией."""
        try:
            project = await self.projects.create_project(
                user_id=user.id,
                title=self._validate_project_title(data.title),
                description=data.description,
            )
            for position, (title, is_completion) in enumerate(DEFAULT_PROJECT_COLUMNS):
                await self.projects.create_column(
                    project_id=project.id,
                    title=title,
                    position=position,
                    is_completion_column=is_completion,
                )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return project

    async def update_project(
        self,
        *,
        user: User,
        project_id: UUID,
        data: ProjectUpdateData,
    ) -> Project:
        """Изменяет основные поля и архивное состояние проекта."""
        project = await self._get_owned_project(user=user, project_id=project_id)
        if data.has("title"):
            project.title = self._validate_project_title(data.title)
        if data.has("description"):
            project.description = data.description
        if data.has("archived"):
            project.archived_at = utc_now() if data.archived else None
        try:
            project = await self.projects.save_project(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return project

    async def delete_project(self, *, user: User, project_id: UUID) -> None:
        """Отвязывает задачи и удаляет проект вместе с колонками."""
        project = await self._get_owned_project(user=user, project_id=project_id, for_update=True)
        try:
            await self.projects.clear_project_tasks(project_id=project.id)
            await self.projects.delete_project(project)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def list_columns(self, *, user: User, project_id: UUID) -> list[ProjectColumn]:
        """Возвращает колонки доступного пользователю проекта."""
        await self._get_owned_project(user=user, project_id=project_id)
        return await self.projects.list_columns(project_id=project_id)

    async def create_column(
        self,
        *,
        user: User,
        project_id: UUID,
        data: ProjectColumnCreateData,
    ) -> ProjectColumn:
        """Добавляет колонку в конец и при необходимости назначает ее завершающей."""
        await self._get_owned_project(user=user, project_id=project_id, for_update=True)
        columns = await self.projects.list_columns(project_id=project_id)
        previous_completion = next(
            (column for column in columns if column.is_completion_column),
            None,
        )
        try:
            if data.is_completion_column:
                await self.projects.clear_completion_column(project_id=project_id)
                if previous_completion is not None:
                    previous_completion.is_completion_column = False
            column = await self.projects.create_column(
                project_id=project_id,
                title=self._validate_column_title(data.title),
                position=len(columns),
                is_completion_column=data.is_completion_column,
            )
            if data.is_completion_column and previous_completion is not None:
                await self._synchronize_column_tasks(previous_completion)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return column

    async def update_column(
        self,
        *,
        user: User,
        project_id: UUID,
        column_id: UUID,
        data: ProjectColumnUpdateData,
    ) -> ProjectColumn:
        """Переименовывает колонку или атомарно назначает ее завершающей."""
        await self._get_owned_project(user=user, project_id=project_id, for_update=True)
        column = await self._get_column(project_id=project_id, column_id=column_id, for_update=True)
        columns_to_synchronize = [column]
        if data.has("title"):
            column.title = self._validate_column_title(data.title)
        if data.has("is_completion_column"):
            if not data.is_completion_column and column.is_completion_column:
                raise ProjectCompletionColumnRequiredError()
            if data.is_completion_column and not column.is_completion_column:
                current_columns = await self.projects.list_columns(project_id=project_id)
                previous_completion = next(
                    (item for item in current_columns if item.is_completion_column),
                    None,
                )
                await self.projects.clear_completion_column(project_id=project_id)
                column.is_completion_column = True
                if previous_completion is not None and previous_completion.id != column.id:
                    previous_completion.is_completion_column = False
                    columns_to_synchronize.append(previous_completion)
        try:
            column = await self.projects.save_column(column)
            for changed_column in columns_to_synchronize:
                await self._synchronize_column_tasks(changed_column)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return column

    async def reorder_columns(
        self,
        *,
        user: User,
        project_id: UUID,
        column_ids: list[UUID],
    ) -> list[ProjectColumn]:
        """Атомарно нормализует порядок всех колонок проекта."""
        await self._get_owned_project(user=user, project_id=project_id, for_update=True)
        columns = await self.projects.list_columns(project_id=project_id)
        current_ids = {column.id for column in columns}
        if len(column_ids) != len(current_ids) or set(column_ids) != current_ids:
            raise InvalidProjectColumnOrderError()
        try:
            await self.projects.park_column_positions(project_id=project_id)
            await self.projects.set_column_positions(
                project_id=project_id,
                positions={column_id: position for position, column_id in enumerate(column_ids)},
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return await self.projects.list_columns(project_id=project_id)

    async def delete_column(
        self,
        *,
        user: User,
        project_id: UUID,
        column_id: UUID,
    ) -> None:
        """Удаляет пустую незавершающую колонку и нормализует порядок."""
        await self._get_owned_project(user=user, project_id=project_id, for_update=True)
        column = await self._get_column(project_id=project_id, column_id=column_id, for_update=True)
        if await self.projects.count_column_tasks(column_id=column.id):
            raise ProjectColumnNotEmptyError()
        if column.is_completion_column:
            raise ProjectCompletionColumnRequiredError()
        remaining_ids = [
            item.id
            for item in await self.projects.list_columns(project_id=project_id)
            if item.id != column.id
        ]
        try:
            await self.projects.delete_column(column)
            if remaining_ids:
                await self.projects.park_column_positions(project_id=project_id)
                await self.projects.set_column_positions(
                    project_id=project_id,
                    positions={item_id: position for position, item_id in enumerate(remaining_ids)},
                )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def move_task(
        self,
        *,
        user: User,
        task_id: UUID,
        data: TaskMoveData,
    ) -> Task:
        """Перемещает карточку и нормализует обе затронутые колонки одной транзакцией."""
        await self._get_owned_project(user=user, project_id=data.project_id, for_update=True)
        target_column = await self._get_column(
            project_id=data.project_id,
            column_id=data.target_column_id,
            for_update=True,
        )
        task = await self.projects.get_task_for_move(
            task_id=task_id,
            user_id=user.id,
            for_update=True,
        )
        if task is None:
            raise TaskNotFoundError()
        if task.project_id != data.project_id or task.project_column_id is None:
            raise InvalidTaskProjectError()
        if (
            target_column.is_completion_column
            and task.recurrence_type_code != TaskRecurrenceTypeCode.none.value
        ):
            raise RecurringTaskCompletionColumnError()

        source_column_id = task.project_column_id
        try:
            source_tasks = await self.projects.list_column_tasks(
                project_id=data.project_id,
                column_id=source_column_id,
                exclude_task_id=task.id,
                for_update=True,
            )
            target_tasks = (
                source_tasks
                if source_column_id == target_column.id
                else await self.projects.list_column_tasks(
                    project_id=data.project_id,
                    column_id=target_column.id,
                    exclude_task_id=task.id,
                    for_update=True,
                )
            )
            target_position = min(data.target_position, len(target_tasks))
            target_tasks.insert(target_position, task)
            task.project_column_id = target_column.id
            self._normalize_task_positions(source_tasks)
            self._normalize_task_positions(target_tasks)
            self._apply_column_status(task, target_column)
            await self.projects.save_tasks([*source_tasks, *target_tasks])
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return task

    async def bulk_move_tasks(
        self,
        *,
        user: User,
        project_id: UUID,
        task_ids: list[UUID],
        target_column_id: UUID,
    ) -> list[Task]:
        """Массово переносит задачи в конец выбранного этапа одной транзакцией."""
        await self._get_owned_project(user=user, project_id=project_id, for_update=True)
        target = await self._get_column(
            project_id=project_id,
            column_id=target_column_id,
            for_update=True,
        )
        tasks = await self.projects.list_project_tasks(
            project_id=project_id,
            task_ids=task_ids,
            for_update=True,
        )
        if len(tasks) != len(set(task_ids)):
            raise InvalidTaskProjectError()
        if target.is_completion_column and any(
            task.recurrence_type_code != TaskRecurrenceTypeCode.none.value for task in tasks
        ):
            raise RecurringTaskCompletionColumnError()
        try:
            affected_column_ids = {task.project_column_id for task in tasks}
            target_tasks = await self.projects.list_column_tasks(
                project_id=project_id,
                column_id=target.id,
                for_update=True,
            )
            selected_ids = {task.id for task in tasks}
            target_tasks = [task for task in target_tasks if task.id not in selected_ids]
            for task in tasks:
                task.project_column_id = target.id
                target_tasks.append(task)
                self._apply_column_status(task, target)
            for column_id in affected_column_ids:
                if column_id is not None and column_id != target.id:
                    source = await self.projects.list_column_tasks(
                        project_id=project_id,
                        column_id=column_id,
                        for_update=True,
                    )
                    source = [task for task in source if task.id not in selected_ids]
                    self._normalize_task_positions(source)
            self._normalize_task_positions(target_tasks)
            await self.projects.save_tasks(tasks)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return tasks

    async def bulk_set_status(
        self,
        *,
        user: User,
        project_id: UUID,
        task_ids: list[UUID],
        status: TaskStatusCode,
    ) -> list[Task]:
        """Массово синхронизирует статус и этап обычных проектных задач."""
        columns = await self.list_columns(user=user, project_id=project_id)
        target = next(
            (
                column
                for column in columns
                if column.is_completion_column == (status == TaskStatusCode.done)
            ),
            None,
        )
        if target is None:
            raise ProjectCompletionColumnRequiredError()
        return await self.bulk_move_tasks(
            user=user,
            project_id=project_id,
            task_ids=task_ids,
            target_column_id=target.id,
        )

    async def _get_owned_project(
        self,
        *,
        user: User,
        project_id: UUID,
        for_update: bool = False,
    ) -> Project:
        project = await self.projects.get_project_for_user(
            project_id=project_id,
            user_id=user.id,
            for_update=for_update,
        )
        if project is None:
            raise ProjectNotFoundError()
        return project

    async def _get_column(
        self,
        *,
        project_id: UUID,
        column_id: UUID,
        for_update: bool = False,
    ) -> ProjectColumn:
        column = await self.projects.get_column(
            project_id=project_id,
            column_id=column_id,
            for_update=for_update,
        )
        if column is None:
            raise ProjectColumnNotFoundError()
        return column

    async def _synchronize_column_tasks(self, column: ProjectColumn) -> None:
        tasks = await self.projects.list_column_tasks(
            project_id=column.project_id,
            column_id=column.id,
            for_update=True,
        )
        if column.is_completion_column and any(
            task.recurrence_type_code != TaskRecurrenceTypeCode.none.value for task in tasks
        ):
            raise RecurringTaskCompletionColumnError()
        for task in tasks:
            self._apply_column_status(task, column)
        await self.projects.save_tasks(tasks)

    def _apply_column_status(self, task: Task, column: ProjectColumn) -> None:
        if task.recurrence_type_code != TaskRecurrenceTypeCode.none.value:
            return
        if column.is_completion_column:
            task.status_code = TaskStatusCode.done.value
            task.completed_at = task.completed_at or utc_now()
        else:
            task.status_code = TaskStatusCode.todo.value
            task.completed_at = None

    def _normalize_task_positions(self, tasks: list[Task]) -> None:
        for position, task in enumerate(tasks):
            task.project_position = position

    def _validate_project_title(self, title: str | None) -> str:
        normalized = title.strip() if title is not None else ""
        if not normalized or len(normalized) > 255:
            raise InvalidProjectTitleError()
        return normalized

    def _validate_column_title(self, title: str | None) -> str:
        normalized = title.strip() if title is not None else ""
        if not normalized or len(normalized) > 255:
            raise InvalidProjectColumnTitleError()
        return normalized
