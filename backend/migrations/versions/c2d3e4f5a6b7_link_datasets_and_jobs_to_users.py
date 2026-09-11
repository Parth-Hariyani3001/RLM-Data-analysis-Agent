"""link datasets and jobs to users

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-09-11 01:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing rows have no owner; clear them before enforcing NOT NULL.
    op.execute(sa.text("DELETE FROM jobs"))
    op.execute(sa.text("DELETE FROM datasets"))

    op.add_column(
        "datasets",
        sa.Column("user_id", sa.UUID(), nullable=False),
    )
    op.create_index(op.f("ix_datasets_user_id"), "datasets", ["user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_datasets_user_id_users"),
        "datasets",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column(
        "jobs",
        sa.Column("user_id", sa.UUID(), nullable=False),
    )
    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_jobs_user_id_users"),
        "jobs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("fk_jobs_user_id_users"), "jobs", type_="foreignkey")
    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_column("jobs", "user_id")

    op.drop_constraint(op.f("fk_datasets_user_id_users"), "datasets", type_="foreignkey")
    op.drop_index(op.f("ix_datasets_user_id"), table_name="datasets")
    op.drop_column("datasets", "user_id")
