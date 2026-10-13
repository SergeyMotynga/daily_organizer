"""Unit-тесты транзакционной логики ProjectService."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.tasks import TaskStatusCode
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
from backend.services.projects import DEFAULT_PROJECT_COLUMNS, ProjectService


def make_user() -> User:
    """Создает минимального пользователя без сохранения в БД."""
    return User(
        id=uuid4(),
        login="tester",
        name="Тестировщик",
        password_hash="hash",
        deleted_at=None,
    )


def make_project(user: User, *, project_id: UUID | None = None) -> Project:
    """Создает проект для unit-сценария."""
    return Project(
        id=project_id or uuid4(),
        user_id=user.id,
        title="Проект",
        description=None,
        archived_at=None,
    )


def make_column(
    project: Project,
    *,
    position: int,
    completion: bool = False,
) -> ProjectColumn:
    """Создает колонку проекта для unit-сценария."""
    return ProjectColumn(
        id=uuid4(),
        project_id=project.id,
        title=f"Колонка {position}",
        position=position,
        is_completion_column=completion,
    )


def make_task(
    user: User,
    project: Project,
    column: ProjectColumn,
    *,
    position: int,
    recurrence: str = "none",
) -> Task:
    """Создает проектную задачу с нужными полями синхронизации."""
    return Task(
        id=uuid4(),
        user_id=user.id,
        title=f"Задача {position}",
        description=None,
        status_code="todo",
        recurrence_type_code=recurrence,
        recurrence_interval=1,
        recurrence_start_date=None,
        recurrence_end_date=None,
        project_id=project.id,
        project_column_id=column.id,
        project_position=position,
        completed_at=None,
        archived_at=None,
    )


def make_service(**repository_methods: object) -> tuple[ProjectService, AsyncMock, SimpleNamespace]:
    """Создает сервис с управляемыми async-mock зависимостями."""
    db = AsyncMock(spec=AsyncSession)
    repository = SimpleNamespace(**repository_methods)
    service = ProjectService(cast(AsyncSession, db))
    cast(Any, service).projects = repository
    return service, db, repository


@pytest.mark.anyio
async def test_list_and_get_project_summary() -> None:
    """Сервис возвращает агрегаты и преобразует отсутствие проекта в доменную ошибку."""
    user = make_user()
    project = make_project(user)
    summary = ProjectSummaryData(project=project, task_count=3, completed_task_count=1)
    service, _, repository = make_service(
        list_projects_for_user=AsyncMock(return_value=[summary]),
        get_project_summary=AsyncMock(side_effect=[summary, None]),
    )

    result = await service.list_projects(user=user, archived=False, q="про")
    assert result == [summary]
    repository.list_projects_for_user.assert_awaited_once_with(
        user_id=user.id,
        archived=False,
        q="про",
    )
    assert await service.get_project_summary(user=user, project_id=project.id) is summary
    with pytest.raises(ProjectNotFoundError):
        await service.get_project_summary(user=user, project_id=uuid4())


@pytest.mark.anyio
async def test_create_project_defaults_and_rolls_back_on_failure() -> None:
    """Создание сохраняет пять этапов и откатывает неполную транзакцию."""
    user = make_user()
    project = make_project(user)
    service, db, repository = make_service(
        create_project=AsyncMock(return_value=project),
        create_column=AsyncMock(),
    )

    result = await service.create_project(
        user=user,
        data=ProjectCreateData(title="  Новый проект  ", description="Описание"),
    )
    assert result is project
    repository.create_project.assert_awaited_once_with(
        user_id=user.id,
        title="Новый проект",
        description="Описание",
    )
    assert repository.create_column.await_count == len(DEFAULT_PROJECT_COLUMNS)
    db.commit.assert_awaited_once()

    failed_service, failed_db, _ = make_service(
        create_project=AsyncMock(return_value=project),
        create_column=AsyncMock(side_effect=RuntimeError("database error")),
    )
    with pytest.raises(RuntimeError, match="database error"):
        await failed_service.create_project(user=user, data=ProjectCreateData(title="Проект"))
    failed_db.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_update_delete_and_list_columns() -> None:
    """Основные операции проходят через repository и завершаются commit."""
    user = make_user()
    project = make_project(user)
    columns = [make_column(project, position=0), make_column(project, position=1, completion=True)]
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        save_project=AsyncMock(return_value=project),
        clear_project_tasks=AsyncMock(),
        delete_project=AsyncMock(),
        list_columns=AsyncMock(return_value=columns),
    )

    updated = await service.update_project(
        user=user,
        project_id=project.id,
        data=ProjectUpdateData(
            fields_set=frozenset({"title", "description", "archived"}),
            title="  Новое имя  ",
            description="Описание",
            archived=True,
        ),
    )
    assert updated.title == "Новое имя"
    assert updated.description == "Описание"
    assert updated.archived_at is not None
    assert await service.list_columns(user=user, project_id=project.id) == columns
    await service.delete_project(user=user, project_id=project.id)
    repository.clear_project_tasks.assert_awaited_once_with(project_id=project.id)
    repository.delete_project.assert_awaited_once_with(project)
    assert db.commit.await_count == 2


@pytest.mark.anyio
async def test_project_mutations_roll_back_repository_errors() -> None:
    """Ошибки сохранения проекта и удаления не оставляют открытую транзакцию."""
    user = make_user()
    project = make_project(user)
    update_service, update_db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        save_project=AsyncMock(side_effect=RuntimeError("save")),
    )
    with pytest.raises(RuntimeError, match="save"):
        await update_service.update_project(
            user=user,
            project_id=project.id,
            data=ProjectUpdateData(fields_set=frozenset()),
        )
    update_db.rollback.assert_awaited_once()

    delete_service, delete_db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        clear_project_tasks=AsyncMock(side_effect=RuntimeError("delete")),
        delete_project=AsyncMock(),
    )
    with pytest.raises(RuntimeError, match="delete"):
        await delete_service.delete_project(user=user, project_id=project.id)
    delete_db.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_create_completion_column_reopens_previous_tasks() -> None:
    """Новая completion-колонка снимает выполнение с карточек прежней."""
    user = make_user()
    project = make_project(user)
    old_done = make_column(project, position=0, completion=True)
    new_done = make_column(project, position=1, completion=True)
    task = make_task(user, project, old_done, position=0)
    task.status_code = "done"
    task.completed_at = datetime.now(UTC)
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        list_columns=AsyncMock(return_value=[old_done]),
        clear_completion_column=AsyncMock(),
        create_column=AsyncMock(return_value=new_done),
        list_column_tasks=AsyncMock(return_value=[task]),
        save_tasks=AsyncMock(),
    )

    result = await service.create_column(
        user=user,
        project_id=project.id,
        data=ProjectColumnCreateData(title="Закрыто", is_completion_column=True),
    )
    assert result is new_done
    assert old_done.is_completion_column is False
    assert task.status_code == "todo"
    assert cast(Any, task).completed_at is None
    repository.save_tasks.assert_awaited_once_with([task])
    db.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_create_column_rolls_back_and_validates_title() -> None:
    """Создание этапа валидирует имя и откатывает ошибку repository."""
    user = make_user()
    project = make_project(user)
    service, db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        list_columns=AsyncMock(return_value=[]),
        create_column=AsyncMock(side_effect=RuntimeError("column")),
    )
    with pytest.raises(RuntimeError, match="column"):
        await service.create_column(
            user=user,
            project_id=project.id,
            data=ProjectColumnCreateData(title="Этап"),
        )
    db.rollback.assert_awaited_once()

    with pytest.raises(InvalidProjectColumnTitleError):
        await service.create_column(
            user=user,
            project_id=project.id,
            data=ProjectColumnCreateData(title="   "),
        )


@pytest.mark.anyio
async def test_update_completion_column_synchronizes_both_sides() -> None:
    """Смена completion-признака обновляет старые и новые завершенные задачи."""
    user = make_user()
    project = make_project(user)
    active = make_column(project, position=0)
    old_done = make_column(project, position=1, completion=True)
    active_task = make_task(user, project, active, position=0)
    old_task = make_task(user, project, old_done, position=0)
    old_task.status_code = "done"
    old_task.completed_at = datetime.now(UTC)
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=active),
        list_columns=AsyncMock(return_value=[active, old_done]),
        clear_completion_column=AsyncMock(),
        save_column=AsyncMock(return_value=active),
        list_column_tasks=AsyncMock(side_effect=[[active_task], [old_task]]),
        save_tasks=AsyncMock(),
    )

    result = await service.update_column(
        user=user,
        project_id=project.id,
        column_id=active.id,
        data=ProjectColumnUpdateData(
            fields_set=frozenset({"title", "is_completion_column"}),
            title="  Готово теперь  ",
            is_completion_column=True,
        ),
    )
    assert result.title == "Готово теперь"
    assert result.is_completion_column is True
    assert old_done.is_completion_column is False
    assert active_task.status_code == "done"
    assert old_task.status_code == "todo"
    assert repository.save_tasks.await_count == 2
    db.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_update_column_guards_and_rollback() -> None:
    """Completion-этап нельзя снять, а ошибка синхронизации откатывается."""
    user = make_user()
    project = make_project(user)
    done = make_column(project, position=0, completion=True)
    guarded, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
    )
    with pytest.raises(ProjectCompletionColumnRequiredError):
        await guarded.update_column(
            user=user,
            project_id=project.id,
            column_id=done.id,
            data=ProjectColumnUpdateData(
                fields_set=frozenset({"is_completion_column"}),
                is_completion_column=False,
            ),
        )

    recurring = make_task(user, project, done, position=0, recurrence="daily")
    failing, db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        save_column=AsyncMock(return_value=done),
        list_column_tasks=AsyncMock(return_value=[recurring]),
    )
    with pytest.raises(RecurringTaskCompletionColumnError):
        await failing.update_column(
            user=user,
            project_id=project.id,
            column_id=done.id,
            data=ProjectColumnUpdateData(fields_set=frozenset({"title"}), title="Готово"),
        )
    db.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_reorder_columns_success_invalid_order_and_rollback() -> None:
    """Порядок требует полный набор UUID и меняется одной транзакцией."""
    user = make_user()
    project = make_project(user)
    first = make_column(project, position=0)
    second = make_column(project, position=1, completion=True)
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        list_columns=AsyncMock(side_effect=[[first, second], [second, first]]),
        park_column_positions=AsyncMock(),
        set_column_positions=AsyncMock(),
    )
    result = await service.reorder_columns(
        user=user,
        project_id=project.id,
        column_ids=[second.id, first.id],
    )
    assert result == [second, first]
    repository.set_column_positions.assert_awaited_once_with(
        project_id=project.id,
        positions={second.id: 0, first.id: 1},
    )
    db.commit.assert_awaited_once()

    invalid, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        list_columns=AsyncMock(return_value=[first, second]),
    )
    with pytest.raises(InvalidProjectColumnOrderError):
        await invalid.reorder_columns(
            user=user,
            project_id=project.id,
            column_ids=[first.id],
        )

    failed, failed_db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        list_columns=AsyncMock(return_value=[first, second]),
        park_column_positions=AsyncMock(side_effect=RuntimeError("order")),
    )
    with pytest.raises(RuntimeError, match="order"):
        await failed.reorder_columns(
            user=user,
            project_id=project.id,
            column_ids=[first.id, second.id],
        )
    failed_db.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_delete_column_success_and_guards() -> None:
    """Удаляется только пустой обычный этап с нормализацией оставшихся."""
    user = make_user()
    project = make_project(user)
    first = make_column(project, position=0)
    removable = make_column(project, position=1)
    done = make_column(project, position=2, completion=True)
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=removable),
        count_column_tasks=AsyncMock(return_value=0),
        list_columns=AsyncMock(return_value=[first, removable, done]),
        delete_column=AsyncMock(),
        park_column_positions=AsyncMock(),
        set_column_positions=AsyncMock(),
    )
    await service.delete_column(user=user, project_id=project.id, column_id=removable.id)
    repository.set_column_positions.assert_awaited_once_with(
        project_id=project.id,
        positions={first.id: 0, done.id: 1},
    )
    db.commit.assert_awaited_once()

    nonempty, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=first),
        count_column_tasks=AsyncMock(return_value=1),
    )
    with pytest.raises(ProjectColumnNotEmptyError):
        await nonempty.delete_column(user=user, project_id=project.id, column_id=first.id)

    completion, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        count_column_tasks=AsyncMock(return_value=0),
    )
    with pytest.raises(ProjectCompletionColumnRequiredError):
        await completion.delete_column(user=user, project_id=project.id, column_id=done.id)

    failed, failed_db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=removable),
        count_column_tasks=AsyncMock(return_value=0),
        list_columns=AsyncMock(return_value=[removable]),
        delete_column=AsyncMock(side_effect=RuntimeError("delete column")),
    )
    with pytest.raises(RuntimeError, match="delete column"):
        await failed.delete_column(user=user, project_id=project.id, column_id=removable.id)
    failed_db.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_move_task_between_columns_and_inside_one_column() -> None:
    """Move нормализует обе колонки, ограничивает позицию и меняет статус."""
    user = make_user()
    project = make_project(user)
    source = make_column(project, position=0)
    done = make_column(project, position=1, completion=True)
    moved = make_task(user, project, source, position=1)
    source_task = make_task(user, project, source, position=0)
    target_task = make_task(user, project, done, position=0)
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        get_task_for_move=AsyncMock(return_value=moved),
        list_column_tasks=AsyncMock(side_effect=[[source_task], [target_task]]),
        save_tasks=AsyncMock(),
    )
    result = await service.move_task(
        user=user,
        task_id=moved.id,
        data=TaskMoveData(
            project_id=project.id,
            target_column_id=done.id,
            target_position=50,
        ),
    )
    assert result.project_column_id == done.id
    assert result.project_position == 1
    assert result.status_code == "done"
    assert result.completed_at is not None
    repository.save_tasks.assert_awaited_once()
    db.commit.assert_awaited_once()

    sibling = make_task(user, project, source, position=0)
    moved.project_column_id = source.id
    moved.project_position = 1
    same, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=source),
        get_task_for_move=AsyncMock(return_value=moved),
        list_column_tasks=AsyncMock(return_value=[sibling]),
        save_tasks=AsyncMock(),
    )
    await same.move_task(
        user=user,
        task_id=moved.id,
        data=TaskMoveData(project_id=project.id, target_column_id=source.id, target_position=0),
    )
    assert moved.project_position == 0
    assert sibling.project_position == 1
    assert moved.status_code == "todo"


@pytest.mark.anyio
async def test_move_task_validation_errors() -> None:
    """Move возвращает точные доменные ошибки до начала транзакции."""
    user = make_user()
    project = make_project(user)
    source = make_column(project, position=0)
    done = make_column(project, position=1, completion=True)
    missing, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        get_task_for_move=AsyncMock(return_value=None),
    )
    with pytest.raises(TaskNotFoundError):
        await missing.move_task(
            user=user,
            task_id=uuid4(),
            data=TaskMoveData(project_id=project.id, target_column_id=done.id, target_position=0),
        )

    detached = make_task(user, project, source, position=0)
    detached.project_column_id = None
    invalid, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=source),
        get_task_for_move=AsyncMock(return_value=detached),
    )
    with pytest.raises(InvalidTaskProjectError):
        await invalid.move_task(
            user=user,
            task_id=detached.id,
            data=TaskMoveData(project_id=project.id, target_column_id=source.id, target_position=0),
        )

    recurring = make_task(user, project, source, position=0, recurrence="daily")
    blocked, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        get_task_for_move=AsyncMock(return_value=recurring),
    )
    with pytest.raises(RecurringTaskCompletionColumnError):
        await blocked.move_task(
            user=user,
            task_id=recurring.id,
            data=TaskMoveData(project_id=project.id, target_column_id=done.id, target_position=0),
        )

    task = make_task(user, project, source, position=0)
    failed, failed_db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=source),
        get_task_for_move=AsyncMock(return_value=task),
        list_column_tasks=AsyncMock(side_effect=RuntimeError("move")),
    )
    with pytest.raises(RuntimeError, match="move"):
        await failed.move_task(
            user=user,
            task_id=task.id,
            data=TaskMoveData(project_id=project.id, target_column_id=source.id, target_position=0),
        )
    failed_db.rollback.assert_awaited_once()

    status_before = recurring.status_code
    blocked._apply_column_status(recurring, source)
    assert recurring.status_code == status_before


@pytest.mark.anyio
async def test_bulk_move_and_bulk_status() -> None:
    """Bulk-перенос обновляет источники, цель и поддерживает смену статуса."""
    user = make_user()
    project = make_project(user)
    source = make_column(project, position=0)
    done = make_column(project, position=1, completion=True)
    first = make_task(user, project, source, position=0)
    second = make_task(user, project, source, position=1)
    existing = make_task(user, project, done, position=0)
    service, db, repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        list_project_tasks=AsyncMock(return_value=[first, second]),
        list_column_tasks=AsyncMock(side_effect=[[existing], []]),
        save_tasks=AsyncMock(),
    )
    result = await service.bulk_move_tasks(
        user=user,
        project_id=project.id,
        task_ids=[first.id, second.id],
        target_column_id=done.id,
    )
    assert result == [first, second]
    assert [first.project_position, second.project_position] == [1, 2]
    assert {first.status_code, second.status_code} == {"done"}
    db.commit.assert_awaited_once()

    todo_service, _, todo_repository = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        list_columns=AsyncMock(return_value=[source, done]),
        get_column=AsyncMock(return_value=source),
        list_project_tasks=AsyncMock(return_value=[first]),
        list_column_tasks=AsyncMock(side_effect=[[], []]),
        save_tasks=AsyncMock(),
    )
    reopened = await todo_service.bulk_set_status(
        user=user,
        project_id=project.id,
        task_ids=[first.id],
        status=TaskStatusCode.todo,
    )
    assert reopened == [first]
    assert first.status_code == "todo"
    todo_repository.get_column.assert_awaited_once()


@pytest.mark.anyio
async def test_bulk_move_validation_and_rollback() -> None:
    """Bulk-перенос запрещает неполный набор, recurring completion и откатывает ошибки."""
    user = make_user()
    project = make_project(user)
    source = make_column(project, position=0)
    done = make_column(project, position=1, completion=True)
    task = make_task(user, project, source, position=0)
    invalid, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        list_project_tasks=AsyncMock(return_value=[]),
    )
    with pytest.raises(InvalidTaskProjectError):
        await invalid.bulk_move_tasks(
            user=user,
            project_id=project.id,
            task_ids=[task.id],
            target_column_id=done.id,
        )

    recurring = make_task(user, project, source, position=0, recurrence="daily")
    blocked, _, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=done),
        list_project_tasks=AsyncMock(return_value=[recurring]),
    )
    with pytest.raises(RecurringTaskCompletionColumnError):
        await blocked.bulk_move_tasks(
            user=user,
            project_id=project.id,
            task_ids=[recurring.id],
            target_column_id=done.id,
        )

    failed, db, _ = make_service(
        get_project_for_user=AsyncMock(return_value=project),
        get_column=AsyncMock(return_value=source),
        list_project_tasks=AsyncMock(return_value=[task]),
        list_column_tasks=AsyncMock(side_effect=RuntimeError("bulk")),
    )
    with pytest.raises(RuntimeError, match="bulk"):
        await failed.bulk_move_tasks(
            user=user,
            project_id=project.id,
            task_ids=[task.id],
            target_column_id=source.id,
        )
    db.rollback.assert_awaited_once()


@pytest.mark.anyio
async def test_owned_entities_status_target_and_validators() -> None:
    """Внутренние guards покрывают 404, отсутствие completion и граничные названия."""
    user = make_user()
    project = make_project(user)
    service, _, repository = make_service(
        get_project_for_user=AsyncMock(return_value=None),
        get_column=AsyncMock(return_value=None),
        list_columns=AsyncMock(return_value=[]),
    )
    with pytest.raises(ProjectNotFoundError):
        await service._get_owned_project(user=user, project_id=uuid4())
    with pytest.raises(ProjectColumnNotFoundError):
        await service._get_column(project_id=uuid4(), column_id=uuid4())
    repository.get_project_for_user.return_value = project
    with pytest.raises(ProjectCompletionColumnRequiredError):
        await service.bulk_set_status(
            user=user,
            project_id=uuid4(),
            task_ids=[uuid4()],
            status=TaskStatusCode.done,
        )

    for invalid_title in (None, " ", "x" * 256):
        with pytest.raises(InvalidProjectTitleError):
            service._validate_project_title(invalid_title)
        with pytest.raises(InvalidProjectColumnTitleError):
            service._validate_column_title(invalid_title)
