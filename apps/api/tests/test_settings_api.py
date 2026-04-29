from __future__ import annotations

from fastapi.testclient import TestClient

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
