from __future__ import annotations

import time
from collections.abc import Generator
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwk, jwt

from app.core.config import Settings, get_settings
from app.core.jwks import JWKSCache
from app.core.rate_limit import _rate_limiter, reset_rate_limit_config_cache
from app.core.security import get_jwks_cache, reset_jwks_cache
from app.main import create_app

SUPABASE_URL = "https://example.supabase.co"
KID = "test-kid"


def _settings() -> Settings:
    return Settings(
        supabase_url=SUPABASE_URL,
        supabase_jwt_audience="authenticated",
        supabase_jwt_secret=None,
        supabase_jwks_cache_ttl_seconds=60,
        api_version="0.1.0",
    )


def _generate_rsa_keypair() -> tuple[str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


RSA_PRIVATE_KEY, RSA_PUBLIC_KEY = _generate_rsa_keypair()


def _build_jwks() -> dict[str, object]:
    key = jwk.construct(RSA_PUBLIC_KEY, "RS256")
    public_jwk = key.to_dict()
    public_jwk["kid"] = KID
    public_jwk["use"] = "sig"
    return {"keys": [public_jwk]}


def _make_token(client_id: str, sub: str) -> str:
    issuer = f"{SUPABASE_URL}/auth/v1"
    payload = {
        "sub": sub,
        "client_id": client_id,
        "aud": "authenticated",
        "iss": issuer,
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(
        payload, RSA_PRIVATE_KEY, algorithm="RS256", headers={"kid": KID}
    )
    return cast(str, token)


@pytest.fixture()
def fastapi_app(monkeypatch: pytest.MonkeyPatch) -> Generator[FastAPI, None, None]:
    monkeypatch.setenv("API_RATE_LIMIT_DEFAULT_MAX", "2")
    monkeypatch.setenv("API_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.delenv("API_RATE_LIMIT_OVERRIDES", raising=False)
    reset_rate_limit_config_cache()
    reset_jwks_cache()
    _rate_limiter._events.clear()

    app = create_app()
    jwks = _build_jwks()

    async def fetcher() -> dict[str, object]:
        return jwks

    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_jwks_cache] = lambda: JWKSCache(
        fetcher=fetcher,
        ttl_seconds=60,
    )
    yield app
    app.dependency_overrides.clear()
    _rate_limiter._events.clear()
    reset_rate_limit_config_cache()
    reset_jwks_cache()


def test_rate_limit_returns_429_and_retry_after(fastapi_app: FastAPI) -> None:
    token = _make_token(
        client_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        sub="11111111-1111-1111-1111-111111111111",
    )
    client = TestClient(fastapi_app)
    headers = {"Authorization": f"Bearer {token}"}

    response_1 = client.get("/api/v1/protected/ping", headers=headers)
    response_2 = client.get("/api/v1/protected/ping", headers=headers)
    response_3 = client.get("/api/v1/protected/ping", headers=headers)

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert response_3.status_code == 429
    assert "Retry-After" in response_3.headers
    assert int(response_3.headers["Retry-After"]) >= 1
    assert response_3.json()["error"]["code"] == "rate_limited"


def test_rate_limit_scopes_by_client_and_user_pair(fastapi_app: FastAPI) -> None:
    token_a = _make_token(
        client_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        sub="11111111-1111-1111-1111-111111111111",
    )
    token_b = _make_token(
        client_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        sub="11111111-1111-1111-1111-111111111111",
    )
    client = TestClient(fastapi_app)

    response_a1 = client.get(
        "/api/v1/protected/ping", headers={"Authorization": f"Bearer {token_a}"}
    )
    response_a2 = client.get(
        "/api/v1/protected/ping", headers={"Authorization": f"Bearer {token_a}"}
    )
    response_a3 = client.get(
        "/api/v1/protected/ping", headers={"Authorization": f"Bearer {token_a}"}
    )
    response_b1 = client.get(
        "/api/v1/protected/ping", headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response_a1.status_code == 200
    assert response_a2.status_code == 200
    assert response_a3.status_code == 429
    assert response_b1.status_code == 200


def test_rate_limit_records_audit_log_event(
    fastapi_app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.main as app_main

    captured: list[dict[str, object]] = []

    def fake_write_api_audit_log(**kwargs: object) -> None:
        captured.append(kwargs)

    monkeypatch.setattr(app_main, "write_api_audit_log", fake_write_api_audit_log)

    token = _make_token(
        client_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        sub="11111111-1111-1111-1111-111111111111",
    )
    client = TestClient(fastapi_app)
    headers = {"Authorization": f"Bearer {token}"}

    client.get("/api/v1/protected/ping", headers=headers)
    client.get("/api/v1/protected/ping", headers=headers)
    response = client.get("/api/v1/protected/ping", headers=headers)

    assert response.status_code == 429
    assert captured
    event = captured[-1]
    assert event["status"] == 429
    assert event["method"] == "GET"
    assert event["path"] == "/api/v1/protected/ping"
