from __future__ import annotations

from fastapi.testclient import TestClient

from app.connectors.credential_resolver import PRODUCT_HUNT_ENV_VARS, REDDIT_ENV_VARS
from app.main import app


def test_settings_platforms_include_all_project_phases() -> None:
    client = TestClient(app)

    response = client.get("/api/settings/platforms")

    assert response.status_code == 200
    platforms = response.json()["platforms"]
    by_platform = {item["platform"]: item for item in platforms}
    assert set(by_platform) == {"reddit", "product_hunt", "x", "discord"}
    assert by_platform["reddit"]["phase"] == "P0"
    assert by_platform["product_hunt"]["phase"] == "P0"
    assert by_platform["x"]["phase"] == "P1"
    assert by_platform["discord"]["phase"] == "P2"


def test_credential_status_does_not_return_secret_payload() -> None:
    client = TestClient(app)

    response = client.get("/api/settings/credentials/status")

    assert response.status_code == 200
    body = response.json()
    assert "encrypted_payload" not in str(body)
    assert "token" not in str(body).lower()
    credentials = body["credentials"]
    assert {item["platform"] for item in credentials} == {"reddit", "product_hunt", "x", "discord"}


def test_platform_env_test_reports_missing_required_env(monkeypatch) -> None:
    client = TestClient(app)
    for name in REDDIT_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    response = client.post("/api/settings/platforms/reddit/test")

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "reddit"
    assert body["status"] == "missing_env"
    assert body["required_env_missing"] == list(REDDIT_ENV_VARS)
    assert body["checked_at"]


def test_platform_env_test_reports_mock_as_available() -> None:
    client = TestClient(app)

    response = client.post("/api/settings/platforms/mock/test")

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "mock"
    assert body["status"] == "available"
    assert body["required_env_missing"] == []


def test_platform_env_test_reports_configured_unverified_without_secret_values(monkeypatch) -> None:
    client = TestClient(app)
    secret = "ph-test-token"
    for name in PRODUCT_HUNT_ENV_VARS:
        monkeypatch.setenv(name, secret)

    response = client.post("/api/settings/platforms/product_hunt/test")

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "product_hunt"
    assert body["status"] == "configured_unverified"
    assert body["required_env_missing"] == []
    assert secret not in str(body)
    assert "Bearer" not in str(body)


def test_platform_env_test_reports_future_platforms_as_coming_soon() -> None:
    client = TestClient(app)

    response = client.post("/api/settings/platforms/x/test")

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "x"
    assert body["status"] == "coming_soon"
    assert body["required_env_missing"] == []


def test_platform_env_test_rejects_unsupported_platform() -> None:
    client = TestClient(app)

    response = client.post("/api/settings/platforms/unknown/test")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
