from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Cluster, Project
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


def demo_cluster_id() -> str:
    assert SessionLocal is not None
    with SessionLocal() as db:
        cluster_id = db.scalar(select(Cluster.id).order_by(Cluster.opportunity_score.desc().nullslast()))
        assert cluster_id is not None
        return str(cluster_id)


def test_list_and_get_clusters() -> None:
    list_response = client().get(f"/api/projects/{demo_project_id()}/clusters")
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] >= 2
    assert body["items"][0]["title"]

    detail_response = client().get(f"/api/clusters/{body['items'][0]['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == body["items"][0]["id"]


def test_update_and_archive_cluster() -> None:
    cluster_id = demo_cluster_id()

    update_response = client().put(
        f"/api/clusters/{cluster_id}",
        json={"status": "watching", "description": "Updated by Phase 2 API test"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "watching"

    archive_response = client().post(f"/api/clusters/{cluster_id}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"
