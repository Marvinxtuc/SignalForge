#!/usr/bin/env python3
from __future__ import annotations

import importlib
import inspect
import os
import socket
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

try:
    from pydantic import ValidationError
    from sqlalchemy import func, select
    from sqlalchemy.exc import SQLAlchemyError
except ImportError as exc:
    print(f"FAIL: missing required dependency: {exc}")
    sys.exit(1)


ROOT = Path(__file__).resolve().parents[1]
API_ROOT_CANDIDATES = (ROOT, ROOT / "apps" / "api")
for candidate in API_ROOT_CANDIDATES:
    if (candidate / "app" / "connectors").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


EXTERNAL_API_MARKERS = (
    "import requests",
    "from requests",
    "aiohttp",
    "urllib.request",
    "socket.create_connection",
    "discord.com/api",
    "api.x.com",
    "api.twitter.com",
    "openai",
    "anthropic",
    "selenium",
    "playwright",
    "puppeteer",
    "webdriver",
)

TOKEN_ENV_KEYS = (
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_REFRESH_TOKEN",
    "PRODUCT_HUNT_TOKEN",
    "PRODUCTHUNT_TOKEN",
    "DISCORD_BOT_TOKEN",
    "X_BEARER_TOKEN",
    "TWITTER_BEARER_TOKEN",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)


class ValidationFailure(Exception):
    pass


def _fail(message: str) -> None:
    raise ValidationFailure(message)


def _pass(message: str) -> None:
    print(f"PASS: {message}")


def _api_root() -> Path:
    for candidate in API_ROOT_CANDIDATES:
        if (candidate / "app" / "connectors").is_dir():
            return candidate
    _fail("Unable to locate API app root")


def _count(db: Any, model: Any, *criteria: Any) -> int:
    statement = select(func.count()).select_from(model)
    for criterion in criteria:
        statement = statement.where(criterion)
    return int(db.scalar(statement) or 0)


@contextmanager
def _without_real_tokens() -> Any:
    original = {key: os.environ.get(key) for key in TOKEN_ENV_KEYS}
    for key in TOKEN_ENV_KEYS:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def _block_external_api_calls() -> Any:
    patches: list[tuple[Any, str, Any]] = []

    def patch(target: Any, attribute: str) -> None:
        if not hasattr(target, attribute):
            return
        original = getattr(target, attribute)

        def blocked(*args: Any, **kwargs: Any) -> Any:
            raise ValidationFailure(f"External API call attempted via {target.__name__}.{attribute}")

        setattr(target, attribute, blocked)
        patches.append((target, attribute, original))

    def patch_socket_create_connection() -> None:
        original = socket.create_connection
        allowed_hosts = {"postgres", "localhost", "127.0.0.1", "::1"}

        def guarded(address: Any, *args: Any, **kwargs: Any) -> Any:
            host = address[0] if isinstance(address, tuple) and address else address
            if str(host) in allowed_hosts:
                return original(address, *args, **kwargs)
            raise ValidationFailure("External API call attempted via socket.create_connection")

        socket.create_connection = guarded
        patches.append((socket, "create_connection", original))

    def patch_optional(module_name: str, class_name: str | None, attribute: str) -> None:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return
        target = getattr(module, class_name) if class_name else module
        patch(target, attribute)

    import urllib.request

    patch(urllib.request, "urlopen")
    patch_socket_create_connection()
    patch_optional("requests", "Session", "request")
    patch_optional("httpx", "Client", "request")
    patch_optional("httpx", "AsyncClient", "request")
    patch_optional("aiohttp", "ClientSession", "_request")

    try:
        yield
    finally:
        for target, attribute, original in reversed(patches):
            setattr(target, attribute, original)


def validate_base_connector_contract() -> None:
    from app.connectors.base import BaseConnector

    if not inspect.isclass(BaseConnector) or not inspect.isabstract(BaseConnector):
        _fail("BaseConnector must be an abstract class")
    if not hasattr(BaseConnector, "collect"):
        _fail("BaseConnector.collect is missing")

    collect = BaseConnector.__dict__.get("collect")
    if collect is None or not getattr(collect, "__isabstractmethod__", False):
        _fail("BaseConnector.collect must be abstract")

    signature = inspect.signature(BaseConnector.collect)
    if list(signature.parameters) != ["self", "config"]:
        _fail(f"BaseConnector.collect signature is unexpected: {signature}")

    _pass("BaseConnector contract exists")


def validate_normalized_raw_item_contract() -> None:
    from app.connectors.types import NormalizedRawItem

    invalid_cases = (
        {"platform": "reddit", "platform_item_id": "abc"},
        {"platform": "reddit", "platform_item_id": "abc", "source_url": None},
        {"platform": "reddit", "platform_item_id": "abc", "source_url": ""},
        {"platform": "reddit", "platform_item_id": "abc", "source_url": "   "},
    )
    for payload in invalid_cases:
        try:
            NormalizedRawItem(**payload)
        except ValidationError:
            continue
        _fail(f"NormalizedRawItem accepted invalid source_url payload: {payload}")

    item = NormalizedRawItem(
        platform="reddit",
        platform_item_id="abc",
        source_url="https://example.local/reddit/abc",
    )
    if item.source_url != "https://example.local/reddit/abc":
        _fail("NormalizedRawItem changed valid source_url unexpectedly")

    _pass("NormalizedRawItem requires non-empty source_url")


def validate_connector_contracts_without_tokens() -> None:
    from app.connectors.disabled import DisabledConnector
    from app.connectors.mock import MockConnector
    from app.connectors.registry import ConnectorRegistry
    from app.connectors.types import ConnectorStatus, ProjectCollectionConfig

    with _without_real_tokens(), _block_external_api_calls():
        mock_config = ProjectCollectionConfig(project_id=uuid4(), platform="mock")
        mock_result = MockConnector().collect(mock_config)
        if mock_result.status != ConnectorStatus.SUCCESS:
            _fail(f"MockConnector returned unexpected status: {mock_result.status}")
        if not mock_result.items or any(not item.source_url for item in mock_result.items):
            _fail("MockConnector did not return source_url on every item")
        _pass("MockConnector returns source_url")

        for platform in ("reddit", "product_hunt"):
            config = ProjectCollectionConfig(project_id=uuid4(), platform=platform)
            disabled_result = DisabledConnector(platform).collect(config)
            if disabled_result.status != ConnectorStatus.DISABLED:
                _fail(f"DisabledConnector({platform}) returned {disabled_result.status}")
            if disabled_result.items or disabled_result.items_collected:
                _fail(f"DisabledConnector({platform}) returned collected items")
        _pass("DisabledConnector returns disabled without exception")

        registry = ConnectorRegistry()
        for platform in ("reddit", "product_hunt"):
            connector = registry.get(platform)
            result = connector.collect(ProjectCollectionConfig(project_id=uuid4(), platform=platform))
            if connector.platform != platform or result.status != ConnectorStatus.DISABLED:
                _fail(f"ConnectorRegistry safe degradation failed for {platform}")
        _pass("ConnectorRegistry returns safely disabled P0 connectors without credentials")

    _pass("No external API call or real token is required for connector contracts")


def validate_external_api_marker_scan() -> None:
    api_root = _api_root()
    scan_roots = (
        api_root / "app" / "connectors",
        api_root / "app" / "services",
        api_root / "app" / "api" / "routes",
    )
    files: list[Path] = []
    for scan_root in scan_roots:
        if scan_root.is_dir():
            files.extend(path for path in scan_root.rglob("*.py") if path.is_file())
        elif scan_root.is_file():
            files.append(scan_root)

    hits: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for marker in EXTERNAL_API_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(api_root)}: {marker}")

    if hits:
        _fail(f"Forbidden external integration markers found in runtime code: {hits}")

    _pass(f"External API marker scan covers {len(EXTERNAL_API_MARKERS)} forbidden markers and found no hits")


def _create_project() -> UUID:
    from app.db.models import Keyword, Project
    from app.db.session import SessionLocal

    if SessionLocal is None:
        _fail("DATABASE_URL is not configured")

    with SessionLocal() as db:
        project = Project(
            name=f"Connector Abstraction Validation {uuid4()}",
            description="Temporary project created by validate_connector_abstraction.py",
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
        return project.id


def _delete_project(project_id: UUID) -> None:
    from app.db.models import Project
    from app.db.session import SessionLocal

    if SessionLocal is None:
        return

    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is not None:
            db.delete(project)
            db.commit()


def validate_collection_jobs() -> None:
    from app.db.models import Cluster, CollectionLog, Opportunity, RawItem, Signal
    from app.db.session import SessionLocal
    from app.services.collection_executor import execute_collection

    if SessionLocal is None:
        _fail("DATABASE_URL is not configured")

    project_id = _create_project()
    try:
        with SessionLocal() as db, _without_real_tokens(), _block_external_api_calls():
            signal_count_before = _count(db, Signal)
            cluster_count_before = _count(db, Cluster)
            opportunity_count_before = _count(db, Opportunity)

            mock_job = execute_collection(db, project_id=project_id, execution_mode="mock")
            mock_raw_count = _count(db, RawItem, RawItem.project_id == project_id)
            mock_log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == mock_job.id))
            raw_items = list(db.scalars(select(RawItem).where(RawItem.project_id == project_id)))

            if mock_job.status != "success":
                _fail(f"Mock collection job returned {mock_job.status}")
            if mock_raw_count != 3:
                _fail(f"Mock collection job inserted {mock_raw_count} raw_items, expected 3")
            if any(not item.source_url for item in raw_items):
                _fail("Mock collection job inserted raw_items without source_url")
            if mock_log is None or mock_log.status != "success" or mock_log.items_inserted != 3:
                _fail(f"Mock collection job did not write expected collection_log: {mock_log}")
            _pass("Mock collection job inserts raw_items")

            if (
                _count(db, Signal) != signal_count_before
                or _count(db, Cluster) != cluster_count_before
                or _count(db, Opportunity) != opportunity_count_before
            ):
                _fail("Mock collection created signals, clusters, or opportunities")
            _pass("Connector abstraction creates no signals / clusters / opportunities")

            duplicate_job = execute_collection(db, project_id=project_id, execution_mode="mock")
            duplicate_log = db.scalar(select(CollectionLog).where(CollectionLog.job_id == duplicate_job.id))
            duplicate_raw_count = _count(db, RawItem, RawItem.project_id == project_id)
            if duplicate_raw_count != 3:
                _fail(f"Duplicate collection changed raw_items count to {duplicate_raw_count}")
            if duplicate_log is None or duplicate_log.items_inserted != 0 or duplicate_log.items_skipped != 3:
                _fail(f"Duplicate raw_items were not skipped as expected: {duplicate_log}")
            _pass("Duplicate raw_items are skipped")

            disabled_job = execute_collection(db, project_id=project_id, connectors=["reddit", "product_hunt"])
            disabled_logs = list(
                db.scalars(
                    select(CollectionLog)
                    .where(CollectionLog.job_id == disabled_job.id)
                    .order_by(CollectionLog.platform.asc())
                )
            )
            disabled_by_platform = {log.platform: log for log in disabled_logs}
            for platform in ("product_hunt", "reddit"):
                log = disabled_by_platform.get(platform)
                if log is None or log.status != "disabled" or log.error_message is None:
                    _fail(f"Disabled collection job did not write expected log for {platform}: {log}")
            _pass("Disabled collection job writes logs")

            validation_log_count = _count(
                db,
                CollectionLog,
                CollectionLog.job_id.in_([mock_job.id, duplicate_job.id, disabled_job.id]),
            )
            if validation_log_count != 4:
                _fail(f"Expected 4 validation collection_logs, found {validation_log_count}")
            _pass("collection_logs are written")
    except SQLAlchemyError as exc:
        _fail(f"Database validation failed: {exc}")
    finally:
        _delete_project(project_id)


def main() -> int:
    try:
        validate_base_connector_contract()
        validate_normalized_raw_item_contract()
        validate_connector_contracts_without_tokens()
        validate_external_api_marker_scan()
        validate_collection_jobs()
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    except Exception as exc:
        print(f"FAIL: unexpected validation error: {exc}")
        return 1

    print("PASS: connector abstraction validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
