from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Cluster, Opportunity, Project, Signal
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


def demo_cluster_id() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        cluster_id = db.scalar(select(Cluster.id).order_by(Cluster.opportunity_score.desc().nullslast()))
        assert cluster_id is not None
        return str(cluster_id)


def demo_opportunity_id() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        opportunity_id = db.scalar(select(Opportunity.id).order_by(Opportunity.created_at.asc()))
        assert opportunity_id is not None
        return str(opportunity_id)


def test_list_and_get_opportunities() -> None:
    list_response = client().get(f"/api/projects/{demo_project_id()}/opportunities")
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] >= 1
    assert body["items"][0]["title"]

    detail_response = client().get(f"/api/opportunities/{body['items'][0]['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == body["items"][0]["id"]


def test_create_opportunity_from_signal_and_cluster() -> None:
    signal_response = client().post(f"/api/signals/{demo_signal_id()}/create-opportunity")
    assert signal_response.status_code == 200
    signal_body = signal_response.json()
    assert signal_body["title"]
    assert signal_body["evidence_count"] == 1

    cluster_response = client().post(f"/api/clusters/{demo_cluster_id()}/create-opportunity")
    assert cluster_response.status_code == 200
    cluster_body = cluster_response.json()
    assert cluster_body["cluster_id"] == demo_cluster_id()
    assert cluster_body["title"]


def test_update_and_archive_opportunity() -> None:
    opportunity_id = demo_opportunity_id()

    update_response = client().put(
        f"/api/opportunities/{opportunity_id}",
        json={"status": "validating", "title": "Updated opportunity"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "validating"
    assert update_response.json()["title"] == "Updated opportunity"

    archive_response = client().post(f"/api/opportunities/{opportunity_id}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"
