from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import CollectionJob, CollectionLog, Project, RawItem
from app.db.session import SessionLocal
from app.main import app


EXPECTED_MOCK_ITEMS = 5


def create_project() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = Project(
            name=f"Collection API Test {uuid4()}",
            description="Collection API integration test",
            platforms_enabled={"mock": True},
            collection_frequency="manual",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return str(project.id)


def delete_project(project_id: str) -> None:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = db.get(Project, UUID(project_id))
        if project is not None:
            db.delete(project)
            db.commit()


def raw_item_count(project_id: str) -> int:
    assert SessionLocal is not None
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(RawItem).where(RawItem.project_id == UUID(project_id)))
        assert count is not None
        return count


def collection_logs(project_id: str) -> list[CollectionLog]:
    assert SessionLocal is not None
    with SessionLocal() as db:
        logs = list(
            db.scalars(
                select(CollectionLog)
                .join(CollectionJob, CollectionLog.job_id == CollectionJob.id)
                .where(CollectionJob.project_id == UUID(project_id))
                .order_by(CollectionLog.platform.asc())
            )
        )
        for log in logs:
            db.expunge(log)
        return logs


def clear_p0_env(monkeypatch) -> None:
    for name in (
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "PRODUCT_HUNT_TOKEN",
        "SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_collect_mock_executes_and_inserts_raw_items() -> None:
    project_id = create_project()
    try:
        before_count = raw_item_count(project_id)
        response = TestClient(app).post(f"/api/projects/{project_id}/collect", json={"execution_mode": "mock"})
        payload = response.json()

        assert response.status_code == 200
        assert payload["project_id"] == project_id
        assert payload["status"] == "success"
        assert payload["trigger_type"] == "manual"
        assert payload["collector_execution"] == "mock"
        assert payload["log"]["platform"] == "mock"
        assert payload["log"]["status"] == "success"
        assert payload["log"]["items_collected"] == EXPECTED_MOCK_ITEMS
        assert raw_item_count(project_id) == before_count + EXPECTED_MOCK_ITEMS
    finally:
        delete_project(project_id)


def test_collect_disabled_only_logs_disabled_without_raw_items() -> None:
    project_id = create_project()
    try:
        before_count = raw_item_count(project_id)
        response = TestClient(app).post(
            f"/api/projects/{project_id}/collect",
            json={"execution_mode": "disabled_only", "token": "secret-token-must-not-leak"},
        )
        payload = response.json()

        assert response.status_code == 200
        assert payload["project_id"] == project_id
        assert payload["status"] == "success"
        assert payload["collector_execution"] == "disabled_only"
        assert payload["log"]["status"] == "disabled"
        assert raw_item_count(project_id) == before_count
        assert "secret-token-must-not-leak" not in response.text
    finally:
        delete_project(project_id)


def test_collect_default_safe_disabled_logs_disabled_without_raw_items() -> None:
    project_id = create_project()
    try:
        before_count = raw_item_count(project_id)
        response = TestClient(app).post(f"/api/projects/{project_id}/collect")
        payload = response.json()

        assert response.status_code == 200
        assert payload["project_id"] == project_id
        assert payload["status"] == "success"
        assert payload["collector_execution"] == "safe_disabled"
        assert payload["log"]["status"] == "disabled"
        assert raw_item_count(project_id) == before_count
    finally:
        delete_project(project_id)


def test_collect_p0_modes_degrade_without_credentials(monkeypatch) -> None:
    clear_p0_env(monkeypatch)
    project_id = create_project()
    try:
        client = TestClient(app)
        for execution_mode, expected_platforms in {
            "reddit": {"reddit"},
            "product_hunt": {"product_hunt"},
            "p0_real": {"reddit", "product_hunt"},
        }.items():
            before_count = raw_item_count(project_id)
            response = client.post(f"/api/projects/{project_id}/collect", json={"execution_mode": execution_mode})
            payload = response.json()

            assert response.status_code == 200
            assert payload["status"] == "success"
            assert payload["collector_execution"] == execution_mode
            assert payload["log"]["status"] == "disabled"
            assert raw_item_count(project_id) == before_count

            logs = collection_logs(project_id)
            platforms = {log.platform for log in logs if log.status == "disabled"}
            assert expected_platforms <= platforms
    finally:
        delete_project(project_id)


def test_collect_future_and_forbidden_modes_return_phase_not_available() -> None:
    project_id = create_project()
    try:
        client = TestClient(app)
        for execution_mode in ["reddit_real", "product_hunt_real", "x_real", "discord_real", "llm", "pipeline", "unexpected"]:
            response = client.post(f"/api/projects/{project_id}/collect", json={"execution_mode": execution_mode})
            payload = response.json()

            assert response.status_code == 409
            assert payload["error"]["code"] == "phase_not_available"
            assert payload["error"]["message"] == "Requested connector execution mode is not available in Phase 4."
            assert payload["error"]["details"] == {}
    finally:
        delete_project(project_id)


def test_get_collection_job() -> None:
    project_id = create_project()
    try:
        client = TestClient(app)
        created = client.post(f"/api/projects/{project_id}/collect")
        assert created.status_code == 200

        response = client.get(f"/api/jobs/{created.json()['id']}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == created.json()["id"]
        assert payload["project_id"] == project_id
    finally:
        delete_project(project_id)


def test_project_collection_logs_are_paginated() -> None:
    project_id = create_project()
    try:
        client = TestClient(app)
        created = client.post(f"/api/projects/{project_id}/collect", json={"execution_mode": "disabled_only"})
        assert created.status_code == 200

        response = client.get(f"/api/projects/{project_id}/collection-logs")
        payload = response.json()

        assert response.status_code == 200
        assert payload["page"] == 1
        assert payload["page_size"] == 20
        assert payload["total"] >= 1
        assert payload["items"][0]["status"] == "disabled"
    finally:
        delete_project(project_id)
