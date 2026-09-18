"""Repository для личных проектов и колонок."""

from uuid import UUID

from sqlalchemy import and_, asc, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.domain.tasks import TaskStatusCode
from backend.dto.projects import ProjectSummaryData
from backend.models.project import Project, ProjectColumn
from backend.models.task import Task


class ProjectRepository:
    """Запросы к проектам, колонкам и проектным позициям задач."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_project(
        self,
        *,
        user_id: UUID,
        title: str,
        description: str | None,
    ) -> Project:
        """Создает проект и получает сгенерированные БД поля."""
        project = Project(user_id=user_id, title=title, description=description)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def list_projects_for_user(
        self,
        *,
        user_id: UUID,
        archived: bool,
        q: str | None = None,
    ) -> list[ProjectSummaryData]:
        """Возвращает проекты с агрегатами задач одним запросом."""
        active_task = and_(Task.project_id == Project.id, Task.archived_at.is_(None))
        statement = (
            select(
                Project,
                func.count(Task.id).label("task_count"),
                func.count(Task.id)
                .filter(Task.status_code == TaskStatusCode.done.value)
                .label("completed_task_count"),
            )
            .outerjoin(Task, active_task)
            .where(
                Project.user_id == user_id,
                Project.archived_at.is_not(None) if archived else Project.archived_at.is_(None),
            )
            .group_by(Project.id)
            .order_by(Project.updated_at.desc(), Project.id.desc())
        )
        if q is not None:
            query = f"%{q}%"
            statement = statement.where(
                Project.title.ilike(query) | Project.description.ilike(query)
            )
        rows = (await self.db.execute(statement)).all()
        return [
            ProjectSummaryData(
                project=row.Project,
                task_count=int(row.task_count),
                completed_task_count=int(row.completed_task_count),
            )
            for row in rows
        ]

    async def get_project_for_user(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        with_columns: bool = False,
        for_update: bool = False,
    ) -> Project | None:
        """Возвращает проект пользователя, при необходимости с колонками или блокировкой."""
        statement = select(Project).where(Project.id == project_id, Project.user_id == user_id)
        if with_columns:
            statement = statement.options(selectinload(Project.columns))
        if for_update:
            statement = statement.with_for_update()
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_project_summary(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
    ) -> ProjectSummaryData | None:
        """Возвращает один проект с колонками и агрегатами задач."""
        active_task = and_(Task.project_id == Project.id, Task.archived_at.is_(None))
        statement = (
            select(
                Project,
                func.count(Task.id).label("task_count"),
                func.count(Task.id)
                .filter(Task.status_code == TaskStatusCode.done.value)
                .label("completed_task_count"),
            )
            .outerjoin(Task, active_task)
            .where(Project.id == project_id, Project.user_id == user_id)
            .group_by(Project.id)
            .options(selectinload(Project.columns))
        )
        row = (await self.db.execute(statement)).one_or_none()
        if row is None:
            return None
        return ProjectSummaryData(
            project=row.Project,
            task_count=int(row.task_count),
            completed_task_count=int(row.completed_task_count),
        )

    async def create_column(
        self,
        *,
        project_id: UUID,
        title: str,
        position: int,
        is_completion_column: bool,
    ) -> ProjectColumn:
        """Создает колонку проекта."""
        column = ProjectColumn(
            project_id=project_id,
            title=title,
            position=position,
            is_completion_column=is_completion_column,
        )
        self.db.add(column)
        await self.db.flush()
        await self.db.refresh(column)
        return column

    async def list_columns(self, *, project_id: UUID) -> list[ProjectColumn]:
        """Возвращает колонки проекта в сохраненном порядке."""
        statement = (
            select(ProjectColumn)
            .where(ProjectColumn.project_id == project_id)
            .order_by(asc(ProjectColumn.position), asc(ProjectColumn.id))
        )
        return list((await self.db.execute(statement)).scalars().all())

    async def get_column(
        self,
        *,
        project_id: UUID,
        column_id: UUID,
        for_update: bool = False,
    ) -> ProjectColumn | None:
        """Возвращает колонку конкретного проекта."""
        statement = select(ProjectColumn).where(
            ProjectColumn.id == column_id,
            ProjectColumn.project_id == project_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return (await self.db.execute(statement)).scalar_one_or_none()

    async def get_task_for_move(
        self,
        *,
        task_id: UUID,
        user_id: UUID,
        for_update: bool = False,
    ) -> Task | None:
        """Возвращает принадлежащую пользователю задачу для перемещения."""
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        if for_update:
            statement = statement.with_for_update()
        return (await self.db.execute(statement)).scalar_one_or_none()

    async def list_column_tasks(
        self,
        *,
        project_id: UUID,
        column_id: UUID,
        exclude_task_id: UUID | None = None,
        for_update: bool = False,
    ) -> list[Task]:
        """Возвращает задачи колонки в Kanban-порядке."""
        statement = (
            select(Task)
            .where(Task.project_id == project_id, Task.project_column_id == column_id)
            .order_by(asc(Task.project_position), asc(Task.id))
        )
        if exclude_task_id is not None:
            statement = statement.where(Task.id != exclude_task_id)
        if for_update:
            statement = statement.with_for_update()
        return list((await self.db.execute(statement)).scalars().all())

    async def list_project_tasks(
        self,
        *,
        project_id: UUID,
        task_ids: list[UUID] | None = None,
        for_update: bool = False,
    ) -> list[Task]:
        """Возвращает все или выбранные задачи проекта."""
        statement = select(Task).where(Task.project_id == project_id)
        if task_ids is not None:
            statement = statement.where(Task.id.in_(task_ids))
        if for_update:
            statement = statement.with_for_update()
        return list((await self.db.execute(statement)).scalars().all())

    async def count_column_tasks(self, *, column_id: UUID) -> int:
        """Считает задачи в колонке."""
        count = await self.db.scalar(
            select(func.count()).select_from(Task).where(Task.project_column_id == column_id)
        )
        return int(count or 0)

    async def park_column_positions(self, *, project_id: UUID) -> None:
        """Временно уводит позиции колонок в свободный положительный диапазон."""
        await self.db.execute(
            update(ProjectColumn)
            .where(ProjectColumn.project_id == project_id)
            .values(position=ProjectColumn.position + 1_000_000)
        )
        await self.db.flush()

    async def set_column_positions(
        self,
        *,
        project_id: UUID,
        positions: dict[UUID, int],
    ) -> None:
        """Устанавливает нормализованные позиции колонок одним запросом."""
        position_case = case(positions, value=ProjectColumn.id)
        await self.db.execute(
            update(ProjectColumn)
            .where(ProjectColumn.project_id == project_id, ProjectColumn.id.in_(positions))
            .values(position=position_case)
        )
        await self.db.flush()

    async def clear_completion_column(self, *, project_id: UUID) -> None:
        """Снимает признак завершения у текущей завершающей колонки."""
        await self.db.execute(
            update(ProjectColumn)
            .where(
                ProjectColumn.project_id == project_id,
                ProjectColumn.is_completion_column.is_(True),
            )
            .values(is_completion_column=False)
        )
        await self.db.flush()

    async def clear_project_tasks(self, *, project_id: UUID) -> None:
        """Отвязывает задачи перед удалением проекта."""
        await self.db.execute(
            update(Task)
            .where(Task.project_id == project_id)
            .values(project_id=None, project_column_id=None, project_position=None)
        )
        await self.db.flush()

    async def save_project(self, project: Project) -> Project:
        """Сохраняет изменения проекта."""
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def save_column(self, column: ProjectColumn) -> ProjectColumn:
        """Сохраняет изменения колонки."""
        await self.db.flush()
        await self.db.refresh(column)
        return column

    async def save_tasks(self, tasks: list[Task]) -> None:
        """Сохраняет измененные позиции и статусы задач."""
        if tasks:
            await self.db.flush()

    async def delete_column(self, column: ProjectColumn) -> None:
        """Удаляет пустую колонку."""
        await self.db.delete(column)
        await self.db.flush()

    async def delete_project(self, project: Project) -> None:
        """Удаляет проект после отвязки задач."""
        await self.db.delete(project)
        await self.db.flush()
