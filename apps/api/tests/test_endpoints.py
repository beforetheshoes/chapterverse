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


def test_cors_preflight_for_library_endpoint() -> None:
    client = TestClient(create_app())
    response = client.options(
        "/api/v1/library/items?limit=10",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_preflight_for_library_endpoint_staging_origin() -> None:
    client = TestClient(create_app())
    response = client.options(
        "/api/v1/library/items?limit=10",
        headers={
            "Origin": "https://staging.theseedbed.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://staging.theseedbed.app"
    )
