from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import func, select

from app.connectors.base import BaseConnector
from app.connectors.types import (
    ConnectorResult,
    ConnectorStatus,
    NormalizedRawItem,
    ProjectCollectionConfig,
    RateLimitState,
)
from app.db.models import CollectionJob, CollectionLog, Keyword, Project, RawItem
from app.db.session import SessionLocal
from app.services.collection_executor import execute_collection


class DuplicateConnector(BaseConnector):
    platform = "duplicate_test"

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        items = [
            _normalized_item(self.platform, "duplicate-001"),
            _normalized_item(self.platform, "duplicate-001"),
            _normalized_item(self.platform, "duplicate-002"),
        ]
        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.SUCCESS,
            items=items,
            items_collected=len(items),
        )


class MissingSourceUrlConnector(BaseConnector):
    platform = "missing_source_test"

    def collect(self, config: ProjectCollectionConfig) -> SimpleNamespace:
        return SimpleNamespace(
            platform=self.platform,
            status=ConnectorStatus.SUCCESS,
            items=[
                {"platform": self.platform, "platform_item_id": "missing-001"},
                {"platform": self.platform, "platform_item_id": "missing-002", "source_url": None},
                {"platform": self.platform, "platform_item_id": "missing-003", "source_url": "   "},
                {
                    "platform": self.platform,
                    "platform_item_id": "missing-004",
                    "source_url": "https://example.local/missing-source/missing-004",
                },
            ],
            items_collected=4,
            items_skipped=0,
            error_message=None,
            rate_limit_state=None,
        )


class FailingConnector(BaseConnector):
    platform = "failing_test"

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.FAILED,
            items_collected=0,
            error_message="synthetic connector failure",
        )


class RateLimitedConnector(BaseConnector):
    platform = "rate_limited_test"

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.RATE_LIMITED,
            items_collected=0,
            error_message="rate limit reached",
            rate_limit_state=RateLimitState(
                remaining=0,
                reset_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            ),
        )


def _normalized_item(platform: str, platform_item_id: str) -> NormalizedRawItem:
    return NormalizedRawItem(
        platform=platform,
        platform_item_id=platform_item_id,
        source_url=f"https://example.local/{platform}/{platform_item_id}",
        content_text=f"content for {platform_item_id}",
        keyword_hits=["wallet"],
        raw_payload={"test": True},
        created_at_source=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _create_project() -> Project:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = Project(
            name=f"Collection Executor Test {uuid4()}",
            description="Phase 3 collection executor test project",
            platforms_enabled={},
            collection_frequency="manual",
        )
        db.add(project)
        db.flush()
        db.add_all(
            [
                Keyword(project_id=project.id, keyword="wallet", keyword_type="main", language="en"),
                Keyword(project_id=project.id, keyword="checkout", keyword_type="related", language="en"),
                Keyword(project_id=project.id, keyword="spam", keyword_type="exclude", language="zh"),
            ]
        )
        db.commit()
        db.refresh(project)
        return project


def _delete_project(project_id) -> None:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is not None:
            db.delete(project)
            db.commit()


def test_mock_connector_job_inserts_raw_items_and_success_log() -> None:
    project = _create_project()
    try:
        assert SessionLocal is not None
        with SessionLocal() as db:
            job = execute_collection(db, project_id=project.id, execution_mode="mock")

            raw_count = db.scalar(select(func.count()).select_from(RawItem).where(RawItem.project_id == project.id))
            log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == job.id))

            assert job.status == "success"
            assert raw_count == 3
            assert log is not None
            assert log.platform == "mock"
            assert log.status == "success"
            assert log.items_collected == 3
            assert log.items_inserted == 3
            assert log.items_skipped == 0
    finally:
        _delete_project(project.id)


def test_disabled_connector_job_logs_readably_without_raw_items() -> None:
    project = _create_project()
    try:
        assert SessionLocal is not None
        with SessionLocal() as db:
            job = execute_collection(db, project_id=project.id, connectors=["reddit"])

            raw_count = db.scalar(select(func.count()).select_from(RawItem).where(RawItem.project_id == project.id))
            log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == job.id))

            assert job.status == "success"
            assert raw_count == 0
            assert log is not None
            assert log.platform == "reddit"
            assert log.status == "disabled"
            assert log.items_collected == 0
            assert log.items_inserted == 0
            assert log.items_skipped == 0
            assert log.error_message
    finally:
        _delete_project(project.id)


def test_duplicate_raw_items_are_skipped_without_crashing_job() -> None:
    project = _create_project()
    try:
        assert SessionLocal is not None
        with SessionLocal() as db:
            job = execute_collection(db, project_id=project.id, connectors=[DuplicateConnector()])

            raw_count = db.scalar(select(func.count()).select_from(RawItem).where(RawItem.project_id == project.id))
            log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == job.id))

            assert job.status == "success"
            assert raw_count == 2
            assert log is not None
            assert log.items_collected == 3
            assert log.items_inserted == 2
            assert log.items_skipped == 1
    finally:
        _delete_project(project.id)


def test_missing_source_url_items_are_skipped() -> None:
    project = _create_project()
    try:
        assert SessionLocal is not None
        with SessionLocal() as db:
            job = execute_collection(db, project_id=project.id, connectors=[MissingSourceUrlConnector()])

            raw_count = db.scalar(select(func.count()).select_from(RawItem).where(RawItem.project_id == project.id))
            log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == job.id))

            assert job.status == "success"
            assert raw_count == 1
            assert log is not None
            assert log.items_collected == 4
            assert log.items_inserted == 1
            assert log.items_skipped == 3
    finally:
        _delete_project(project.id)


def test_collection_logs_and_job_status_for_partial_failed_and_rate_limit() -> None:
    partial_project = _create_project()
    rate_project = _create_project()
    try:
        assert SessionLocal is not None
        with SessionLocal() as db:
            partial_job = execute_collection(
                db,
                project_id=partial_project.id,
                connectors=[DuplicateConnector(), FailingConnector()],
            )
            partial_logs = list(
                db.scalars(
                    select(CollectionLog)
                    .where(CollectionLog.job_id == partial_job.id)
                    .order_by(CollectionLog.platform.asc())
                )
            )

            assert partial_job.status == "partial_failed"
            assert len(partial_logs) == 2
            assert sum(log.items_collected for log in partial_logs) == 3
            assert sum(log.items_inserted for log in partial_logs) == 2
            assert sum(log.items_skipped for log in partial_logs) == 1

        with SessionLocal() as db:
            existing_job = CollectionJob(project_id=rate_project.id, status="pending", trigger_type="manual")
            db.add(existing_job)
            db.commit()
            db.refresh(existing_job)

            rate_job = execute_collection(
                db,
                project_id=rate_project.id,
                connectors=[RateLimitedConnector()],
                job=existing_job,
            )
            rate_log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == rate_job.id))

            assert rate_job.status == "rate_limited"
            assert rate_log is not None
            assert rate_log.status == "rate_limited"
            assert rate_log.rate_limit_remaining == 0
            assert rate_log.rate_limit_reset_at is not None
    finally:
        _delete_project(partial_project.id)
        _delete_project(rate_project.id)
