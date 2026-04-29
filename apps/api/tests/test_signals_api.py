from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Project, Signal
from app.db.session import SessionLocal
from app.main import app


def client() -> TestClient:
    return TestClient(app)


def demo_project_id() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        project_id = db.scalar(select(Project.id).where(Project.name == "Polymarket Opportunity Radar"))
        assert project_id is not None
        return str(project_id)


def demo_signal_id() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        signal_id = db.scalar(select(Signal.id).order_by(Signal.pain_level.desc().nullslast()))
        assert signal_id is not None
        return str(signal_id)


def test_list_signals_preserves_source_url_and_filters_high_value() -> None:
    response = client().get(f"/api/projects/{demo_project_id()}/signals", params={"min_pain_level": 70})

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["total"] >= 2
    assert body["items"]
    assert all(item["pain_level"] >= 70 for item in body["items"])
    assert all(item["source_url"] for item in body["items"])
    assert all(item["platform"] for item in body["items"])


def test_get_signal_detail_includes_source_url() -> None:
    response = client().get(f"/api/signals/{demo_signal_id()}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["source_url"].startswith("https://example.com/")
    assert body["summary_zh"]


def test_update_signal_feedback_and_status() -> None:
    signal_id = demo_signal_id()

    feedback_response = client().put(f"/api/signals/{signal_id}/feedback", json={"user_feedback": "valuable"})
    assert feedback_response.status_code == 200
    assert feedback_response.json()["user_feedback"] == "valuable"

    status_response = client().put(f"/api/signals/{signal_id}/status", json={"status": "saved"})
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "saved"
