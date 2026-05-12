from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import ProductionLifecycleRun, Project
from app.db.session import SessionLocal
from app.main import app


def create_project() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project = Project(
            name=f"Production Run API Test {uuid4()}",
            description="Production lifecycle API integration test",
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


def delete_run(run_id: str) -> None:
    assert SessionLocal is not None
    with SessionLocal() as db:
        run = db.get(ProductionLifecycleRun, UUID(run_id))
        if run is not None:
            db.delete(run)
            db.commit()


def test_production_lifecycle_run_mock_success(monkeypatch) -> None:
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE", raising=False)
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_LLM_SMOKE", raising=False)
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE", raising=False)
    project_id = create_project()
    run_id = None
    try:
        response = TestClient(app).post(
            "/api/production/runs",
            json={
                "project_id": project_id,
                "collection_mode": "mock",
                "processing_mode": "fallback_only",
            },
        )
        payload = response.json()
        run_id = payload["id"]

        assert response.status_code == 201
        assert payload["project_id"] == project_id
        assert payload["status"] == "success"
        assert payload["stage"] == "report"
        assert payload["collection_mode"] == "mock"
        assert payload["processing_mode"] == "fallback_only"
        assert payload["allow_real_platform_write"] is False
        assert payload["allow_real_llm"] is False
        assert payload["allow_real_embedding"] is False
        assert payload["env_preflight"]["safe_execution"] is True
        assert payload["result_summary"]["collection"]["status"] == "success"
        assert [event["stage"] for event in payload["result_summary"]["lifecycle"]] == [
            "preflight",
            "collect",
            "process",
            "review",
            "report",
        ]

        fetched = TestClient(app).get(f"/api/production/runs/{run_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == run_id

        closed = TestClient(app).post(
            f"/api/production/runs/{run_id}/closeout",
            json={"rollback_hint": "Delete this run record if needed."},
        )
        assert closed.status_code == 200
        assert closed.json()["status"] == "closed"
        assert closed.json()["stage"] == "closeout"
        assert closed.json()["result_summary"]["lifecycle"][-1]["stage"] == "closeout"
    finally:
        if run_id is not None:
            delete_run(run_id)
        delete_project(project_id)


def test_production_lifecycle_run_real_provider_no_go_without_approvals_or_env(monkeypatch) -> None:
    for name in (
        "SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE",
        "SIGNALFORGE_ALLOW_REAL_LLM_SMOKE",
        "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    project_id = create_project()
    run_id = None
    try:
        response = TestClient(app).post(
            "/api/production/runs",
            json={
                "project_id": project_id,
                "collection_mode": "p0_real",
                "processing_mode": "real_llm_embedding",
                "allow_real_platform_write": False,
                "allow_real_llm": False,
                "allow_real_embedding": False,
                "redacted_logs": [{"message": "token=super-secret-token"}],
            },
        )
        payload = response.json()
        run_id = payload["id"]

        assert response.status_code == 201
        assert payload["status"] == "no_go_real_provider"
        assert payload["stage"] == "preflight"
        assert payload["result_summary"]["lifecycle"][0]["stage"] == "preflight"
        assert payload["error_summary"] == "Real provider mode blocked by missing approval or environment flags."
        assert "missing" in payload["env_preflight"]
        assert "super-secret-token" not in response.text
        assert "REDDIT_CLIENT_SECRET" in response.text
    finally:
        if run_id is not None:
            delete_run(run_id)
        delete_project(project_id)


def test_production_lifecycle_runs_list_recent() -> None:
    project_id = create_project()
    run_id = None
    try:
        created = TestClient(app).post(
            "/api/production/runs",
            json={"project_id": project_id, "collection_mode": "mock", "processing_mode": "mock"},
        )
        assert created.status_code == 201
        run_id = created.json()["id"]

        listed = TestClient(app).get("/api/production/runs?page_size=5")

        assert listed.status_code == 200
        assert any(item["id"] == run_id for item in listed.json()["items"])
    finally:
        if run_id is not None:
            delete_run(run_id)
        delete_project(project_id)
