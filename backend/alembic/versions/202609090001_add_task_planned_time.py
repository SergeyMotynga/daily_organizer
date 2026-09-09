"""Добавить плановое время задачи."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202609090001"
down_revision: str | None = "202609030001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Добавляет nullable плановое время задачи."""
    op.add_column("tasks", sa.Column("planned_time", sa.Time(), nullable=True))


def downgrade() -> None:
    """Удаляет плановое время задачи."""
    op.drop_column("tasks", "planned_time")
