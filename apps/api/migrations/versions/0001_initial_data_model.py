"""initial data model

Revision ID: 0001_initial_data_model
Revises:
Create Date: 2026-04-29
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_data_model"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


uuid_type = postgresql.UUID(as_uuid=True)


def timestamp_columns(include_updated: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]
    if include_updated:
        columns.append(sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    return columns


def score_check(column: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(
        f"{column} IS NULL OR ({column} >= 0 AND {column} <= 100)",
        name=op.f(f"ck_{column}_range"),
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "projects",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("platforms_enabled", postgresql.JSONB(), nullable=True),
        sa.Column("collection_frequency", sa.Text(), server_default="manual", nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )

    op.create_table(
        "keywords",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("keyword_type", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), server_default="all", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint("keyword_type IN ('main', 'related', 'exclude')", name=op.f("ck_keywords_keyword_type_allowed")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_keywords_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_keywords")),
    )

    op.create_table(
        "platform_credentials",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("credential_name", sa.Text(), nullable=True),
        sa.Column("encrypted_payload", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_platform_credentials")),
    )

    op.create_table(
        "collection_jobs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("trigger_type", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        *timestamp_columns(include_updated=False),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'success', 'failed', 'partial_failed', 'rate_limited')",
            name=op.f("ck_collection_jobs_status_allowed"),
        ),
        sa.CheckConstraint("trigger_type IN ('manual', 'scheduled')", name=op.f("ck_collection_jobs_trigger_type_allowed")),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_collection_jobs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection_jobs")),
    )

    op.create_table(
        "collection_logs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("job_id", uuid_type, nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("items_collected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_inserted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_skipped", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("rate_limit_remaining", sa.Integer(), nullable=True),
        sa.Column("rate_limit_reset_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(include_updated=False),
        sa.ForeignKeyConstraint(["job_id"], ["collection_jobs.id"], name=op.f("fk_collection_logs_job_id_collection_jobs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection_logs")),
    )

    op.create_table(
        "raw_items",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("platform_item_id", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("author_hash", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_excerpt", sa.Text(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("engagement", postgresql.JSONB(), nullable=True),
        sa.Column("keyword_hits", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("deleted_at_source", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at_source", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_raw_items_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_items")),
        sa.UniqueConstraint("platform", "platform_item_id", name="uq_raw_items_platform_platform_item_id"),
    )

    op.create_table(
        "signals",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("raw_item_id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=False),
        sa.Column("is_need_signal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("signal_type", sa.Text(), nullable=True),
        sa.Column("pain_level", sa.Integer(), nullable=True),
        sa.Column("clarity_score", sa.Integer(), nullable=True),
        sa.Column("urgency_score", sa.Integer(), nullable=True),
        sa.Column("business_relevance", sa.Integer(), nullable=True),
        sa.Column("model_confidence", sa.Integer(), nullable=True),
        sa.Column("signal_confidence", sa.Integer(), nullable=True),
        sa.Column("summary_zh", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("user_feedback", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="new", nullable=False),
        *timestamp_columns(),
        sa.CheckConstraint(
            "signal_type IS NULL OR signal_type IN ("
            "'complaint', 'feature_request', 'alternative_search', 'pricing_issue', "
            "'security_concern', 'workflow_pain', 'integration_need', 'learning_barrier', "
            "'positive_feedback', 'noise')",
            name=op.f("ck_signals_signal_type_allowed"),
        ),
        sa.CheckConstraint("status IN ('new', 'saved', 'ignored', 'reviewed')", name=op.f("ck_signals_status_allowed")),
        score_check("pain_level"),
        score_check("clarity_score"),
        score_check("urgency_score"),
        score_check("business_relevance"),
        score_check("model_confidence"),
        score_check("signal_confidence"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_signals_project_id_projects"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_item_id"], ["raw_items.id"], name=op.f("fk_signals_raw_item_id_raw_items"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_signals")),
    )

    op.create_table(
        "embeddings",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("signal_id", uuid_type, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        *timestamp_columns(include_updated=False),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"], name=op.f("fk_embeddings_signal_id_signals"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_embeddings")),
    )

    op.create_table(
        "clusters",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("opportunity_score", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), server_default="new", nullable=False),
        sa.Column("source_diversity", postgresql.JSONB(), nullable=True),
        sa.Column("evidence_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint("status IN ('new', 'watching', 'validating', 'archived')", name=op.f("ck_clusters_status_allowed")),
        score_check("opportunity_score"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_clusters_project_id_projects"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clusters")),
    )

    op.create_table(
        "cluster_signals",
        sa.Column("cluster_id", uuid_type, nullable=False),
        sa.Column("signal_id", uuid_type, nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        *timestamp_columns(include_updated=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], name=op.f("fk_cluster_signals_cluster_id_clusters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"], name=op.f("fk_cluster_signals_signal_id_signals"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cluster_id", "signal_id", name="pk_cluster_signals"),
    )

    op.create_table(
        "opportunities",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("project_id", uuid_type, nullable=False),
        sa.Column("cluster_id", uuid_type, nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="new", nullable=False),
        sa.Column("opportunity_score", sa.Integer(), nullable=True),
        sa.Column("evidence_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("platform_distribution", postgresql.JSONB(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.CheckConstraint(
            "status IN ('new', 'watching', 'validating', 'build_candidate', 'content_candidate', 'archived')",
            name=op.f("ck_opportunities_status_allowed"),
        ),
        score_check("opportunity_score"),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], name=op.f("fk_opportunities_cluster_id_clusters"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_opportunities_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunities")),
    )


def downgrade() -> None:
    op.drop_table("opportunities")
    op.drop_table("cluster_signals")
    op.drop_table("clusters")
    op.drop_table("embeddings")
    op.drop_table("signals")
    op.drop_table("raw_items")
    op.drop_table("collection_logs")
    op.drop_table("collection_jobs")
    op.drop_table("platform_credentials")
    op.drop_table("keywords")
    op.drop_table("projects")
