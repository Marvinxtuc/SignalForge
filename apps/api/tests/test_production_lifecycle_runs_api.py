from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import CollectionJob, CollectionLog, ProductionLifecycleRun, Project
from app.db.session import SessionLocal
from app.main import app
from app.services import production_runs as production_run_service


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
        assert payload["stage"] == "closeout"
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
            "closeout",
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


def test_production_lifecycle_run_honors_reprocess_flag(monkeypatch) -> None:
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE", raising=False)
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_LLM_SMOKE", raising=False)
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE", raising=False)
    project_id = create_project()
    run_ids: list[str] = []
    try:
        first = TestClient(app).post(
            "/api/production/runs",
            json={
                "project_id": project_id,
                "collection_mode": "mock",
                "processing_mode": "fallback_only",
            },
        )
        assert first.status_code == 201
        run_ids.append(first.json()["id"])

        second = TestClient(app).post(
            "/api/production/runs",
            json={
                "project_id": project_id,
                "collection_mode": "mock",
                "processing_mode": "fallback_only",
                "reprocess": True,
            },
        )
        payload = second.json()
        run_ids.append(payload["id"])

        assert second.status_code == 201
        assert payload["stage"] == "closeout"
        assert payload["result_summary"]["processing"]["processed_in_run"] >= 1
    finally:
        for run_id in run_ids:
            delete_run(run_id)
        delete_project(project_id)


def test_production_lifecycle_run_stops_when_collection_fails(monkeypatch) -> None:
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE", raising=False)
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_LLM_SMOKE", raising=False)
    monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE", raising=False)
    project_id = create_project()
    run_id = None

    def fake_execute_collection(db, *, project_id, execution_mode, **_kwargs):
        job = CollectionJob(
            project_id=project_id,
            status="failed",
            trigger_type="manual",
            error_summary="product_hunt: invalid JSON",
        )
        db.add(job)
        db.flush()
        db.add(
            CollectionLog(
                job_id=job.id,
                platform=execution_mode,
                status="failed",
                items_collected=0,
                items_inserted=0,
                items_skipped=0,
                error_message="Product Hunt returned invalid JSON",
            )
        )
        db.commit()
        db.refresh(job)
        return job

    monkeypatch.setattr(production_run_service, "execute_collection", fake_execute_collection)
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
        assert payload["status"] == "failed"
        assert payload["stage"] == "collect"
        assert payload["error_summary"] == "product_hunt: invalid JSON"
        assert payload["result_summary"]["collection"]["status"] == "failed"
        assert [event["stage"] for event in payload["result_summary"]["lifecycle"]] == [
            "preflight",
            "collect",
        ]
        assert "processing" not in payload["result_summary"]
    finally:
        if run_id is not None:
            delete_run(run_id)
        delete_project(project_id)


def test_production_lifecycle_run_real_provider_no_go_without_approvals_or_env(monkeypatch) -> None:
    for name in (
        "SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE",
        "SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE",
        "SIGNALFORGE_ALLOW_REAL_LLM_SMOKE",
        "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "PRODUCT_HUNT_TOKEN",
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


def test_real_llm_classification_preflight_does_not_require_embedding_gate(monkeypatch) -> None:
    for name in (
        "SIGNALFORGE_ALLOW_REAL_LLM_PROCESSING",
        "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "LLM_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    project_id = create_project()
    run_ids: list[str] = []
    client = TestClient(app)

    def create_real_llm_run() -> dict:
        response = client.post(
            "/api/production/runs",
            json={
                "project_id": project_id,
                "collection_mode": "mock",
                "processing_mode": "real_llm_classification",
                "allow_real_llm": True,
                "allow_real_embedding": False,
                "execute": False,
            },
        )
        payload = response.json()
        assert response.status_code == 201
        run_ids.append(payload["id"])
        assert "llm-secret-value" not in response.text
        return payload

    try:
        missing_gate = create_real_llm_run()
        assert missing_gate["status"] == "no_go_real_provider"
        assert "SIGNALFORGE_ALLOW_REAL_LLM_PROCESSING" in missing_gate["env_preflight"]["missing"]
        assert "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE" not in missing_gate["env_preflight"]["missing"]
        assert "allow_real_embedding" not in missing_gate["env_preflight"]["blocked"]

        monkeypatch.setenv("SIGNALFORGE_ALLOW_REAL_LLM_PROCESSING", "true")
        monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
        monkeypatch.setenv("LLM_API_KEY", "llm-secret-value")
        monkeypatch.setenv("LLM_MODEL", "test-model")
        passed = create_real_llm_run()
        assert passed["status"] == "preflight_passed"
        assert passed["env_preflight"]["missing"] == []
        assert passed["env_preflight"]["blocked"] == []
    finally:
        for run_id in run_ids:
            delete_run(run_id)
        delete_project(project_id)


def test_product_hunt_production_run_requires_smoke_write_and_run_approval(monkeypatch) -> None:
    project_id = create_project()
    run_ids: list[str] = []
    secret = "ph-secret-value"
    client = TestClient(app)

    def create_product_hunt_run(*, allow_write: bool) -> dict:
        response = client.post(
            "/api/production/runs",
            json={
                "project_id": project_id,
                "collection_mode": "product_hunt",
                "processing_mode": "fallback_only",
                "allow_real_platform_write": allow_write,
            },
        )
        payload = response.json()
        assert response.status_code == 201
        run_ids.append(payload["id"])
        assert secret not in response.text
        return payload

    try:
        monkeypatch.setenv("PRODUCT_HUNT_TOKEN", secret)
        monkeypatch.setenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE", "true")
        monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE", raising=False)
        missing_smoke = create_product_hunt_run(allow_write=True)
        assert missing_smoke["status"] == "no_go_real_provider"
        assert "SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE" in missing_smoke["env_preflight"]["missing"]

        monkeypatch.setenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE", "true")
        monkeypatch.delenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE", raising=False)
        missing_write_env = create_product_hunt_run(allow_write=True)
        assert missing_write_env["status"] == "no_go_real_provider"
        assert "SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE" in missing_write_env["env_preflight"]["missing"]

        monkeypatch.setenv("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE", "true")
        missing_run_approval = create_product_hunt_run(allow_write=False)
        assert missing_run_approval["status"] == "no_go_real_provider"
        assert "allow_real_platform_write" in missing_run_approval["env_preflight"]["blocked"]
    finally:
        for run_id in run_ids:
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
