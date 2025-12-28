import asyncio
import base64
import json
import time
from collections.abc import Generator
from typing import cast

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwk, jwt

from app.core.config import Settings, get_settings
from app.core.jwks import JWKSCache
from app.core.security import (
    AuthError,
    _build_issuer,
    _build_jwks_url,
    _fetch_jwks,
    _find_jwk,
    decode_jwt,
    get_jwks_cache,
    require_jwt,
    reset_jwks_cache,
)
from app.main import create_app

SUPABASE_URL = "https://example.supabase.co"
KID = "test-kid"
JWT_SECRET = "local-jwt-secret"


def _generate_rsa_keypair() -> tuple[str, str]:
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


def _generate_ec_keypair() -> tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
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


EC_PRIVATE_KEY, EC_PUBLIC_KEY = _generate_ec_keypair()


def _settings() -> Settings:
    return Settings(
        supabase_url=SUPABASE_URL,
        supabase_jwt_audience="authenticated",
        supabase_jwt_secret=None,
        supabase_jwks_cache_ttl_seconds=60,
        api_version="0.1.0",
    )


def _settings_with_secret() -> Settings:
    return Settings(
        supabase_url=SUPABASE_URL,
        supabase_jwt_audience="authenticated",
        supabase_jwt_secret=JWT_SECRET,
        supabase_jwks_cache_ttl_seconds=60,
        api_version="0.1.0",
    )


def _build_jwks() -> dict[str, object]:
    key = jwk.construct(RSA_PUBLIC_KEY, "RS256")
    public_jwk = key.to_dict()
    public_jwk["kid"] = KID
    public_jwk["use"] = "sig"
    return {"keys": [public_jwk]}


def _build_ec_jwks() -> dict[str, object]:
    key = jwk.construct(EC_PUBLIC_KEY, "ES256")
    public_jwk = key.to_dict()
    public_jwk["kid"] = KID
    public_jwk["use"] = "sig"
    return {"keys": [public_jwk]}


def _make_token(audience: str = "authenticated") -> str:
    issuer = f"{SUPABASE_URL}/auth/v1"
    payload = {
        "sub": "user-123",
        "aud": audience,
        "iss": issuer,
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(
        payload, RSA_PRIVATE_KEY, algorithm="RS256", headers={"kid": KID}
    )
    return cast(str, token)


def _make_es256_token(audience: str = "authenticated") -> str:
    issuer = f"{SUPABASE_URL}/auth/v1"
    payload = {
        "sub": "user-123",
        "aud": audience,
        "iss": issuer,
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, EC_PRIVATE_KEY, algorithm="ES256", headers={"kid": KID})
    return cast(str, token)


def _make_hs256_token(audience: str = "authenticated") -> str:
    issuer = f"{SUPABASE_URL}/auth/v1"
    payload = {
        "sub": "user-123",
        "aud": audience,
        "iss": issuer,
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return cast(str, token)


def _make_token_without_alg() -> str:
    header = {"typ": "JWT"}
    payload = {"sub": "user-123"}
    header_b64 = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    return f"{header_b64}.{payload_b64}.sig"


def _make_token_with_alg(alg: str) -> str:
    header = {"typ": "JWT", "alg": alg}
    payload = {"sub": "user-123"}
    header_b64 = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    return f"{header_b64}.{payload_b64}.sig"


@pytest.fixture()
def fastapi_app() -> Generator[FastAPI, None, None]:
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def test_decode_jwt_success() -> None:
    jwks = _build_jwks()

    async def fetcher() -> dict[str, object]:
        return jwks

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_token()
    payload = asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert payload["sub"] == "user-123"


def test_decode_jwt_es256_success() -> None:
    jwks = _build_ec_jwks()

    async def fetcher() -> dict[str, object]:
        return jwks

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_es256_token()
    payload = asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert payload["sub"] == "user-123"


def test_decode_jwt_hs256_success() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_hs256_token()
    payload = asyncio.run(
        decode_jwt(token, settings=_settings_with_secret(), jwks_cache=cache)
    )
    assert payload["sub"] == "user-123"


def test_decode_jwt_hs256_missing_secret() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_hs256_token()
    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "config_error"


def test_decode_jwt_hs256_invalid_secret() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_hs256_token()
    bad_settings = Settings(
        supabase_url=SUPABASE_URL,
        supabase_jwt_audience="authenticated",
        supabase_jwt_secret="wrong-secret",
        supabase_jwks_cache_ttl_seconds=60,
        api_version="0.1.0",
    )
    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=bad_settings, jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_decode_jwt_missing_alg() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_token_without_alg()
    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_decode_jwt_unsupported_alg() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_token_with_alg("RS512")
    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_decode_jwt_missing_kid() -> None:
    issuer = f"{SUPABASE_URL}/auth/v1"
    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated", "iss": issuer, "exp": 9999999999},
        RSA_PRIVATE_KEY,
        algorithm="RS256",
    )

    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_decode_jwt_invalid_header() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt("not-a.jwt", settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_decode_jwt_jwks_unavailable() -> None:
    async def fetcher() -> dict[str, object]:
        raise httpx.HTTPError("boom")

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_token()

    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "jwks_unavailable"


def test_protected_endpoint_requires_auth(fastapi_app: FastAPI) -> None:
    client = TestClient(fastapi_app)
    response = client.get("/api/v1/protected/ping")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "missing_token"


def test_protected_endpoint_rejects_invalid_token(fastapi_app: FastAPI) -> None:
    fastapi_app.dependency_overrides[get_settings] = _settings

    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    fastapi_app.dependency_overrides[get_jwks_cache] = lambda: JWKSCache(
        fetcher=fetcher,
        ttl_seconds=60,
    )

    client = TestClient(fastapi_app)
    response = client.get(
        "/api/v1/protected/ping",
        headers={"Authorization": "Bearer not-a.jwt"},
    )
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "invalid_token"


def test_protected_endpoint_accepts_valid_token(fastapi_app: FastAPI) -> None:
    jwks = _build_jwks()

    async def fetcher() -> dict[str, object]:
        return jwks

    fastapi_app.dependency_overrides[get_settings] = _settings
    fastapi_app.dependency_overrides[get_jwks_cache] = lambda: JWKSCache(
        fetcher=fetcher,
        ttl_seconds=60,
    )

    token = _make_token()
    client = TestClient(fastapi_app)
    response = client.get(
        "/api/v1/protected/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"data": {"pong": True}, "error": None}


def test_protected_endpoint_accepts_hs256_token(fastapi_app: FastAPI) -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    fastapi_app.dependency_overrides[get_settings] = _settings_with_secret
    fastapi_app.dependency_overrides[get_jwks_cache] = lambda: JWKSCache(
        fetcher=fetcher,
        ttl_seconds=60,
    )

    token = _make_hs256_token()
    client = TestClient(fastapi_app)
    response = client.get(
        "/api/v1/protected/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"data": {"pong": True}, "error": None}


def test_decode_jwt_missing_supabase_url() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    bad_settings = Settings(
        supabase_url="",
        supabase_jwt_audience="authenticated",
        supabase_jwt_secret=None,
        supabase_jwks_cache_ttl_seconds=60,
        api_version="0.1.0",
    )

    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt("token", settings=bad_settings, jwks_cache=cache))
    assert exc.value.code == "config_error"


def test_decode_jwt_key_not_found() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": [{"kid": "other"}]}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_token()

    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_decode_jwt_invalid_audience() -> None:
    jwks = _build_jwks()

    async def fetcher() -> dict[str, object]:
        return jwks

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    token = _make_token(audience="wrong")

    with pytest.raises(AuthError) as exc:
        asyncio.run(decode_jwt(token, settings=_settings(), jwks_cache=cache))
    assert exc.value.code == "invalid_token"


def test_require_jwt_rejects_non_bearer() -> None:
    async def fetcher() -> dict[str, object]:
        return {"keys": []}

    cache = JWKSCache(fetcher=fetcher, ttl_seconds=60)
    with pytest.raises(AuthError) as exc:
        asyncio.run(
            require_jwt(
                authorization="Basic abc",
                settings=_settings(),
                jwks_cache=cache,
            )
        )
    assert exc.value.code == "invalid_token"


def test_build_urls() -> None:
    issuer = _build_issuer(SUPABASE_URL)
    jwks_url = _build_jwks_url(SUPABASE_URL)
    assert issuer == f"{SUPABASE_URL}/auth/v1"
    assert jwks_url == f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"


def test_find_jwk() -> None:
    jwk_value = {"kid": "alpha"}
    assert _find_jwk({"keys": [jwk_value]}, "alpha") == jwk_value
    assert _find_jwk({"keys": [jwk_value]}, "missing") is None


def test_fetch_jwks() -> None:
    jwks_payload = {"keys": [{"kid": "local"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/auth/v1/.well-known/jwks.json"
        body = json.dumps(jwks_payload).encode("utf-8")
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            content=body,
        )

    transport = httpx.MockTransport(handler)
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_jwt_audience="authenticated",
        supabase_jwt_secret=None,
        supabase_jwks_cache_ttl_seconds=60,
        api_version="0.1.0",
    )

    result = asyncio.run(_fetch_jwks(settings, transport=transport))
    assert result == jwks_payload


def test_get_jwks_cache_reuses_instance() -> None:
    reset_jwks_cache()
    settings = _settings()
    cache_one = asyncio.run(get_jwks_cache(settings))
    cache_two = asyncio.run(get_jwks_cache(settings))
    assert cache_one is cache_two

    settings_updated = Settings(
        supabase_url=settings.supabase_url,
        supabase_jwt_audience=settings.supabase_jwt_audience,
        supabase_jwt_secret=settings.supabase_jwt_secret,
        supabase_jwks_cache_ttl_seconds=120,
        api_version=settings.api_version,
    )
    cache_three = asyncio.run(get_jwks_cache(settings_updated))
    assert cache_three is not cache_one
    reset_jwks_cache()
