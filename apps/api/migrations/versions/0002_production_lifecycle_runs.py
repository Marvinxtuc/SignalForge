"""add production lifecycle runs

Revision ID: 0002_production_lifecycle_runs
Revises: 0001_initial_data_model
Create Date: 2026-05-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_production_lifecycle_runs"
down_revision: str | None = "0001_initial_data_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "production_lifecycle_runs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("collection_mode", sa.Text(), nullable=False),
        sa.Column("processing_mode", sa.Text(), nullable=False),
        sa.Column("allow_real_platform_write", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("allow_real_llm", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("allow_real_embedding", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("env_preflight", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("result_summary", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("rollback_hint", sa.Text(), nullable=True),
        sa.Column("redacted_logs", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_production_lifecycle_runs_project_id_projects"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_production_lifecycle_runs")),
    )


def downgrade() -> None:
    op.drop_table("production_lifecycle_runs")
