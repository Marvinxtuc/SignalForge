from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def create_project(client: TestClient) -> str:
    response = client.post(
        "/api/projects",
        json={
            "name": "Worker B Keywords Project",
            "platforms_enabled": {"reddit": True},
            "collection_frequency": "manual",
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def test_keywords_crud() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    created = client.post(
        f"/api/projects/{project_id}/keywords",
        json={"keyword": "polymarket", "keyword_type": "main"},
    )
    assert created.status_code == 201
    keyword = created.json()
    assert keyword["project_id"] == project_id
    assert keyword["language"] == "all"
    assert keyword["enabled"] is True

    listed = client.get(f"/api/projects/{project_id}/keywords")
    assert listed.status_code == 200
    assert any(item["id"] == keyword["id"] for item in listed.json())

    updated = client.put(
        f"/api/keywords/{keyword['id']}",
        json={"keyword_type": "related", "enabled": False},
    )
    assert updated.status_code == 200
    assert updated.json()["keyword_type"] == "related"
    assert updated.json()["enabled"] is False

    deleted = client.delete(f"/api/keywords/{keyword['id']}")
    assert deleted.status_code == 200
    assert deleted.json() == {"id": keyword["id"], "deleted": True}


def test_keyword_invalid_type_is_validation_error() -> None:
    client = TestClient(app)
    project_id = create_project(client)

    response = client.post(
        f"/api/projects/{project_id}/keywords",
        json={"keyword": "invalid", "keyword_type": "seed"},
    )

    assert response.status_code == 422
