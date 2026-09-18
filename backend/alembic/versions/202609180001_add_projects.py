"""Добавить личные проекты, колонки и связь задач с проектами."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202609180001"
down_revision: str | None = "202609100001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создает проекты и добавляет проектные поля к задачам."""
    op.create_table(
        "projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_user_archived", "projects", ["user_id", "archived_at"])
    op.execute(
        """
        CREATE TRIGGER trg_projects_updated_at
        BEFORE UPDATE ON projects
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )

    op.create_table(
        "project_columns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "is_completion_column",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
        sa.CheckConstraint("position >= 0", name="ck_project_columns_position_nonnegative"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "id", name="uq_project_columns_project_id_id"),
        sa.UniqueConstraint("project_id", "position", name="uq_project_columns_project_position"),
    )
    op.create_index("ix_project_columns_project_id", "project_columns", ["project_id"])
    op.create_index(
        "uq_project_columns_one_completion",
        "project_columns",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("is_completion_column"),
    )
    op.execute(
        """
        CREATE TRIGGER trg_project_columns_updated_at
        BEFORE UPDATE ON project_columns
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )

    op.add_column("tasks", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("project_column_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("tasks", sa.Column("project_position", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_tasks_project_fields_consistent",
        "tasks",
        "(project_id IS NULL AND project_column_id IS NULL AND project_position IS NULL) OR "
        "(project_id IS NOT NULL AND project_column_id IS NOT NULL AND project_position >= 0)",
    )
    op.create_foreign_key(
        "fk_tasks_project_id_projects",
        "tasks",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_tasks_project_column_membership",
        "tasks",
        "project_columns",
        ["project_id", "project_column_id"],
        ["project_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_project_column_id", "tasks", ["project_column_id"])
    op.create_index(
        "ix_tasks_project_column_position",
        "tasks",
        ["project_id", "project_column_id", "project_position"],
    )


def downgrade() -> None:
    """Удаляет проектные поля, колонки и проекты."""
    op.drop_index("ix_tasks_project_column_position", table_name="tasks")
    op.drop_index("ix_tasks_project_column_id", table_name="tasks")
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.drop_constraint("fk_tasks_project_column_membership", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_project_id_projects", "tasks", type_="foreignkey")
    op.drop_constraint("ck_tasks_project_fields_consistent", "tasks", type_="check")
    op.drop_column("tasks", "project_position")
    op.drop_column("tasks", "project_column_id")
    op.drop_column("tasks", "project_id")

    op.execute("DROP TRIGGER IF EXISTS trg_project_columns_updated_at ON project_columns")
    op.drop_index("uq_project_columns_one_completion", table_name="project_columns")
    op.drop_index("ix_project_columns_project_id", table_name="project_columns")
    op.drop_table("project_columns")

    op.execute("DROP TRIGGER IF EXISTS trg_projects_updated_at ON projects")
    op.drop_index("ix_projects_user_archived", table_name="projects")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")
