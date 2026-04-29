from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_projects_crud() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/projects",
        json={
            "name": "Worker B Project",
            "description": "Project API test",
            "platforms_enabled": {"reddit": True, "product_hunt": True},
            "collection_frequency": "manual",
        },
    )
    assert created.status_code == 201
    project = created.json()
    assert project["id"]
    assert project["name"] == "Worker B Project"

    listed = client.get("/api/projects")
    assert listed.status_code == 200
    payload = listed.json()
    assert set(payload) == {"items", "page", "page_size", "total"}
    assert payload["total"] >= 1

    fetched = client.get(f"/api/projects/{project['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == project["id"]

    updated = client.put(
        f"/api/projects/{project['id']}",
        json={"name": "Worker B Project Updated", "collection_frequency": "daily"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Worker B Project Updated"
    assert updated.json()["collection_frequency"] == "daily"

    deleted = client.delete(f"/api/projects/{project['id']}")
    assert deleted.status_code == 200
    assert deleted.json() == {"id": project["id"], "deleted": True}


def test_project_not_found_uses_error_envelope() -> None:
    client = TestClient(app)

    response = client.get("/api/projects/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
