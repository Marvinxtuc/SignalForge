from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base, TimestampMixin


def uuid_pk() -> Any:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    platforms_enabled: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    collection_frequency: Mapped[str] = mapped_column(Text, nullable=False, server_default="manual")


class Keyword(TimestampMixin, Base):
    __tablename__ = "keywords"
    __table_args__ = (
        CheckConstraint(
            "keyword_type IN ('main', 'related', 'exclude')",
            name="keyword_type_allowed",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    keyword_type: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(Text, nullable=False, server_default="all")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class PlatformCredential(TimestampMixin, Base):
    __tablename__ = "platform_credentials"

    id: Mapped[uuid.UUID] = uuid_pk()
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    credential_name: Mapped[str | None] = mapped_column(Text)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProductionLifecycleRun(TimestampMixin, Base):
    __tablename__ = "production_lifecycle_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    collection_mode: Mapped[str] = mapped_column(Text, nullable=False)
    processing_mode: Mapped[str] = mapped_column(Text, nullable=False)
    allow_real_platform_write: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    allow_real_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    allow_real_embedding: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    env_preflight: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    error_summary: Mapped[str | None] = mapped_column(Text)
    rollback_hint: Mapped[str | None] = mapped_column(Text)
    redacted_logs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default="[]")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CollectionJob(Base):
    __tablename__ = "collection_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'success', 'failed', 'partial_failed', 'rate_limited')",
            name="status_allowed",
        ),
        CheckConstraint(
            "trigger_type IN ('manual', 'scheduled')",
            name="trigger_type_allowed",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_type: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CollectionLog(Base):
    __tablename__ = "collection_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("collection_jobs.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    items_collected: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    items_inserted: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    items_skipped: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RawItem(Base):
    __tablename__ = "raw_items"
    __table_args__ = (
        UniqueConstraint("platform", "platform_item_id", name="uq_raw_items_platform_platform_item_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    platform_item_id: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    author_hash: Mapped[str | None] = mapped_column(Text)
    content_text: Mapped[str | None] = mapped_column(Text)
    content_excerpt: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    engagement: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    keyword_hits: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    deleted_at_source: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at_source: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Signal(TimestampMixin, Base):
    __tablename__ = "signals"
    __table_args__ = (
        CheckConstraint(
            "signal_type IS NULL OR signal_type IN ("
            "'complaint', 'feature_request', 'alternative_search', 'pricing_issue', "
            "'security_concern', 'workflow_pain', 'integration_need', 'learning_barrier', "
            "'positive_feedback', 'noise')",
            name="signal_type_allowed",
        ),
        CheckConstraint(
            "status IN ('new', 'saved', 'ignored', 'reviewed')",
            name="status_allowed",
        ),
        CheckConstraint("pain_level IS NULL OR (pain_level >= 0 AND pain_level <= 100)", name="pain_level_range"),
        CheckConstraint("clarity_score IS NULL OR (clarity_score >= 0 AND clarity_score <= 100)", name="clarity_score_range"),
        CheckConstraint("urgency_score IS NULL OR (urgency_score >= 0 AND urgency_score <= 100)", name="urgency_score_range"),
        CheckConstraint(
            "business_relevance IS NULL OR (business_relevance >= 0 AND business_relevance <= 100)",
            name="business_relevance_range",
        ),
        CheckConstraint("model_confidence IS NULL OR (model_confidence >= 0 AND model_confidence <= 100)", name="model_confidence_range"),
        CheckConstraint("signal_confidence IS NULL OR (signal_confidence >= 0 AND signal_confidence <= 100)", name="signal_confidence_range"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    raw_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("raw_items.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    is_need_signal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    signal_type: Mapped[str | None] = mapped_column(Text)
    pain_level: Mapped[int | None] = mapped_column(Integer)
    clarity_score: Mapped[int | None] = mapped_column(Integer)
    urgency_score: Mapped[int | None] = mapped_column(Integer)
    business_relevance: Mapped[int | None] = mapped_column(Integer)
    model_confidence: Mapped[int | None] = mapped_column(Integer)
    signal_confidence: Mapped[int | None] = mapped_column(Integer)
    summary_zh: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    user_feedback: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="new")


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = uuid_pk()
    signal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Cluster(TimestampMixin, Base):
    __tablename__ = "clusters"
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'watching', 'validating', 'archived')",
            name="status_allowed",
        ),
        CheckConstraint(
            "opportunity_score IS NULL OR (opportunity_score >= 0 AND opportunity_score <= 100)",
            name="opportunity_score_range",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opportunity_score: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="new")
    source_diversity: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClusterSignal(Base):
    __tablename__ = "cluster_signals"
    __table_args__ = (
        PrimaryKeyConstraint("cluster_id", "signal_id", name="pk_cluster_signals"),
    )

    cluster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    signal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("signals.id", ondelete="CASCADE"), nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'watching', 'validating', 'build_candidate', 'content_candidate', 'archived')",
            name="status_allowed",
        ),
        CheckConstraint(
            "opportunity_score IS NULL OR (opportunity_score >= 0 AND opportunity_score <= 100)",
            name="opportunity_score_range",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clusters.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="new")
    opportunity_score: Mapped[int | None] = mapped_column(Integer)
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    platform_distribution: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
