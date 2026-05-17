from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_owner_auth_disabled_by_default_allows_api_without_token(monkeypatch) -> None:
    monkeypatch.delenv("SIGNALFORGE_REQUIRE_OWNER_AUTH", raising=False)
    monkeypatch.delenv("SIGNALFORGE_OWNER_API_TOKEN", raising=False)

    response = TestClient(app).post("/api/settings/platforms/mock/test")

    assert response.status_code == 200
    assert response.json()["status"] == "available"


def test_owner_auth_required_rejects_api_without_matching_token(monkeypatch) -> None:
    monkeypatch.setenv("SIGNALFORGE_REQUIRE_OWNER_AUTH", "true")
    monkeypatch.setenv("SIGNALFORGE_OWNER_API_TOKEN", "owner-secret")
    client = TestClient(app)

    missing = client.post("/api/settings/platforms/mock/test")
    wrong = client.post("/api/settings/platforms/mock/test", headers={"X-SignalForge-Owner-Token": "wrong"})
    allowed = client.post("/api/settings/platforms/mock/test", headers={"X-SignalForge-Owner-Token": "owner-secret"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert allowed.status_code == 200
    assert "owner-secret" not in missing.text
    assert "wrong" not in wrong.text


def test_health_remains_public_when_owner_auth_required(monkeypatch) -> None:
    monkeypatch.setenv("SIGNALFORGE_REQUIRE_OWNER_AUTH", "true")
    monkeypatch.setenv("SIGNALFORGE_OWNER_API_TOKEN", "owner-secret")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
