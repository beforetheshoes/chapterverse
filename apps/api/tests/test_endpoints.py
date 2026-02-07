from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}, "error": None}


def test_version_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json() == {"data": {"version": "0.1.0"}, "error": None}
