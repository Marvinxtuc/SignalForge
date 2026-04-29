from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Project
from app.db.session import SessionLocal
from app.main import app


def demo_project_id() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project_id = db.scalar(select(Project.id).where(Project.name == "Polymarket Opportunity Radar"))
        assert project_id is not None
        return str(project_id)


def test_collect_creates_pending_job_without_connector() -> None:
    project_id = demo_project_id()
    response = TestClient(app).post(f"/api/projects/{project_id}/collect")
    payload = response.json()

    assert response.status_code == 200
    assert payload["project_id"] == project_id
    assert payload["status"] == "pending"
    assert payload["trigger_type"] == "manual"
    assert payload["collector_execution"] == "not_available_until_phase_3_or_later"
    assert payload["log"]["platform"] == "system"
    assert payload["log"]["items_collected"] == 0


def test_get_collection_job() -> None:
    project_id = demo_project_id()
    client = TestClient(app)
    created = client.post(f"/api/projects/{project_id}/collect")
    assert created.status_code == 200

    response = client.get(f"/api/jobs/{created.json()['id']}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == created.json()["id"]
    assert payload["project_id"] == project_id


def test_project_collection_logs_are_paginated() -> None:
    project_id = demo_project_id()
    client = TestClient(app)
    created = client.post(f"/api/projects/{project_id}/collect")
    assert created.status_code == 200

    response = client.get(f"/api/projects/{project_id}/collection-logs")
    payload = response.json()

    assert response.status_code == 200
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total"] >= 1
    assert payload["items"][0]["platform"] == "system"
