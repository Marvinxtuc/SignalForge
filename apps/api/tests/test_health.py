from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_signalforge_status() -> None:
    client = TestClient(app)

    response = client.get("/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["service"] == "signalforge-api"
    assert payload["phase"].startswith("phase-")
