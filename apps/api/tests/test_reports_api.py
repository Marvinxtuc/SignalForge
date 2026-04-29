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


def test_markdown_report_preserves_source_url_and_omits_secrets() -> None:
    response = TestClient(app).post(f"/api/projects/{demo_project_id()}/reports/markdown", json={})
    payload = response.json()

    assert response.status_code == 200
    assert payload["format"] == "markdown"
    assert "source_url: https://example.com/" in payload["content"]
    assert "encrypted_payload" not in payload["content"]
    assert "token" not in payload["content"].lower()


def test_csv_report_contains_required_signal_fields_and_source_url() -> None:
    response = TestClient(app).post(f"/api/projects/{demo_project_id()}/reports/csv", json={})
    payload = response.json()

    assert response.status_code == 200
    assert payload["format"] == "csv"
    assert payload["content_type"] == "text/csv"
    assert "signal_id,platform,signal_type,pain_level,summary_zh,source_url,created_at" in payload["content"]
    assert "https://example.com/" in payload["content"]
    assert "encrypted_payload" not in payload["content"]
