"""Добавить время дедлайна и простые повторения задач."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202609100001"
down_revision: str | None = "202609090002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создает справочник повторений, completion history и новые поля задач."""
    op.create_table(
        "task_recurrence_types",
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
        CREATE TRIGGER trg_task_recurrence_types_updated_at
        BEFORE UPDATE ON task_recurrence_types
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )
    op.bulk_insert(
        sa.table(
            "task_recurrence_types",
            sa.column("code", sa.String),
            sa.column("title", sa.String),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"code": "none", "title": "Не повторять", "sort_order": 10},
            {"code": "daily", "title": "По дням", "sort_order": 20},
            {"code": "weekdays", "title": "По будням", "sort_order": 30},
            {"code": "weekly", "title": "По неделям", "sort_order": 40},
        ],
    )

    op.add_column("tasks", sa.Column("deadline_time", sa.Time(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column(
            "recurrence_type_code",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'none'"),
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "recurrence_interval",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column("tasks", sa.Column("recurrence_start_date", sa.Date(), nullable=True))
    op.add_column("tasks", sa.Column("recurrence_end_date", sa.Date(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_recurrence_type_code_task_recurrence_types",
        "tasks",
        "task_recurrence_types",
        ["recurrence_type_code"],
        ["code"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_tasks_deadline_time_requires_date",
        "tasks",
        "deadline_time IS NULL OR deadline_date IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_tasks_recurrence_interval_positive",
        "tasks",
        "recurrence_interval >= 1",
    )
    op.create_check_constraint(
        "ck_tasks_recurrence_dates_order",
        "tasks",
        "recurrence_end_date IS NULL OR recurrence_start_date IS NULL "
        "OR recurrence_end_date >= recurrence_start_date",
    )
    op.create_index("ix_tasks_recurrence_type_code", "tasks", ["recurrence_type_code"])

    op.create_table(
        "task_recurrence_completions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_date", sa.Date(), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "task_id",
            "occurrence_date",
            name="uq_task_recurrence_completion",
        ),
    )
    op.create_index(
        "ix_task_recurrence_completions_task_id",
        "task_recurrence_completions",
        ["task_id"],
    )


def downgrade() -> None:
    """Удаляет completion history, новые поля и справочник повторений."""
    op.drop_index(
        "ix_task_recurrence_completions_task_id",
        table_name="task_recurrence_completions",
    )
    op.drop_table("task_recurrence_completions")

    op.drop_index("ix_tasks_recurrence_type_code", table_name="tasks")
    op.drop_constraint("ck_tasks_recurrence_dates_order", "tasks", type_="check")
    op.drop_constraint("ck_tasks_recurrence_interval_positive", "tasks", type_="check")
    op.drop_constraint("ck_tasks_deadline_time_requires_date", "tasks", type_="check")
    op.drop_constraint(
        "fk_tasks_recurrence_type_code_task_recurrence_types",
        "tasks",
        type_="foreignkey",
    )
    op.drop_column("tasks", "recurrence_end_date")
    op.drop_column("tasks", "recurrence_start_date")
    op.drop_column("tasks", "recurrence_interval")
    op.drop_column("tasks", "recurrence_type_code")
    op.drop_column("tasks", "deadline_time")

    op.execute(
        "DROP TRIGGER IF EXISTS trg_task_recurrence_types_updated_at ON task_recurrence_types"
    )
    op.drop_table("task_recurrence_types")
