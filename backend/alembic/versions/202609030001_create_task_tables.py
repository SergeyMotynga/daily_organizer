"""Создать справочник статусов и таблицу задач."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202609030001"
down_revision: str | None = "202608300001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создает task_statuses, seed-значения и таблицу задач."""
    op.create_table(
        "task_statuses",
        sa.Column("code", sa.String(length=32), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute(
        """
        CREATE TRIGGER trg_task_statuses_updated_at
        BEFORE UPDATE ON task_statuses
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )
    op.bulk_insert(
        sa.table(
            "task_statuses",
            sa.column("code", sa.String),
            sa.column("title", sa.String),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"code": "todo", "title": "Активная", "sort_order": 10},
            {"code": "done", "title": "Выполненная", "sort_order": 20},
            {"code": "archived", "title": "Архивная", "sort_order": 30},
        ],
    )

    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status_code",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'todo'"),
        ),
        sa.Column("planned_date", sa.Date(), nullable=True),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["status_code"], ["task_statuses.code"], ondelete="RESTRICT"),
    )
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_index("ix_tasks_status_code", "tasks", ["status_code"])
    op.create_index("ix_tasks_planned_date", "tasks", ["planned_date"])
    op.create_index("ix_tasks_deadline_date", "tasks", ["deadline_date"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])
    op.execute(
        """
        CREATE TRIGGER trg_tasks_updated_at
        BEFORE UPDATE ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )


def downgrade() -> None:
    """Удаляет таблицу задач и справочник статусов."""
    op.execute("DROP TRIGGER IF EXISTS trg_tasks_updated_at ON tasks")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
    op.drop_index("ix_tasks_deadline_date", table_name="tasks")
    op.drop_index("ix_tasks_planned_date", table_name="tasks")
    op.drop_index("ix_tasks_status_code", table_name="tasks")
    op.drop_index("ix_tasks_user_id", table_name="tasks")
    op.drop_table("tasks")

    op.execute("DROP TRIGGER IF EXISTS trg_task_statuses_updated_at ON task_statuses")
    op.drop_table("task_statuses")
