"""Отделить архивацию задачи от статуса выполнения."""

from collections.abc import Sequence

from alembic import op

revision: str = "202609090002"
down_revision: str | None = "202609090001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Переносит архивные задачи в todo/done и удаляет архивный статус."""
    op.execute(
        """
        UPDATE tasks
        SET status_code = CASE
            WHEN completed_at IS NOT NULL THEN 'done'
            ELSE 'todo'
        END
        WHERE status_code = 'archived'
        """
    )
    op.execute("DELETE FROM task_statuses WHERE code = 'archived'")


def downgrade() -> None:
    """Возвращает архивный статус и прежнее представление архивных задач."""
    op.execute(
        """
        INSERT INTO task_statuses (code, title, sort_order)
        VALUES ('archived', 'Архивная', 30)
        """
    )
    op.execute(
        """
        UPDATE tasks
        SET status_code = 'archived'
        WHERE archived_at IS NOT NULL
        """
    )
