from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Annotated, Any, cast

import httpx
from fastapi import Depends, Header
from jose import JWTError, jwt

from app.core.config import Settings, get_settings
from app.core.jwks import JWKSCache

ALGORITHMS_RS256 = ["RS256"]
ALGORITHMS_ES256 = ["ES256"]
ALGORITHMS_HS256 = ["HS256"]
ALGORITHMS_ASYMMETRIC = [*ALGORITHMS_RS256, *ALGORITHMS_ES256]


@dataclass
class AuthError(Exception):
    code: str
    message: str
    status_code: int = 401
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class AuthContext:
    claims: dict[str, Any]
    client_id: uuid.UUID | None
    user_id: uuid.UUID


_jwks_cache: JWKSCache | None = None
_jwks_cache_key: tuple[str, int] | None = None
_jwks_lock = asyncio.Lock()


def _build_issuer(supabase_url: str) -> str:
    return f"{supabase_url}/auth/v1"


def _build_jwks_url(supabase_url: str) -> str:
    return f"{supabase_url}/auth/v1/.well-known/jwks.json"


async def _fetch_jwks(
    settings: Settings,
    client: httpx.AsyncClient | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    url = _build_jwks_url(settings.supabase_url)
    if client is None:
        async with httpx.AsyncClient(
            timeout=5.0,
            transport=transport,
        ) as scoped_client:
            response = await scoped_client.get(url)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
    response = await client.get(url)
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


def _get_jwks_cache(settings: Settings) -> JWKSCache:
    global _jwks_cache, _jwks_cache_key
    cache_key = (settings.supabase_url, settings.supabase_jwks_cache_ttl_seconds)
    if _jwks_cache is None or _jwks_cache_key != cache_key:
        _jwks_cache = JWKSCache(
            fetcher=lambda: _fetch_jwks(settings),
            ttl_seconds=settings.supabase_jwks_cache_ttl_seconds,
        )
        _jwks_cache_key = cache_key
    return _jwks_cache


async def get_jwks_cache(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JWKSCache:
    async with _jwks_lock:
        return _get_jwks_cache(settings)


def reset_jwks_cache() -> None:
    global _jwks_cache, _jwks_cache_key
    _jwks_cache = None
    _jwks_cache_key = None


def _find_jwk(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return cast(dict[str, Any], key)
    return None


async def decode_jwt(
    token: str,
    settings: Settings,
    jwks_cache: JWKSCache,
) -> dict[str, Any]:
    if not settings.supabase_url:
        raise AuthError(
            code="config_error",
            message="SUPABASE_URL is not configured.",
            status_code=500,
        )

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise AuthError(
            code="invalid_token",
            message="Invalid JWT header.",
        ) from exc

    alg = header.get("alg")
    if not alg:
        raise AuthError(code="invalid_token", message="JWT header missing alg.")

    issuer = _build_issuer(settings.supabase_url)
    options = {"verify_aud": settings.supabase_jwt_audience is not None}

    if alg in ALGORITHMS_HS256:
        if not settings.supabase_jwt_secret:
            raise AuthError(
                code="config_error",
                message="SUPABASE_JWT_SECRET is not configured.",
                status_code=500,
            )
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=ALGORITHMS_HS256,
                issuer=issuer,
                audience=settings.supabase_jwt_audience,
                options=options,
            )
            return cast(dict[str, Any], payload)
        except JWTError as exc:
            raise AuthError(
                code="invalid_token",
                message="Invalid JWT.",
            ) from exc

    if alg not in ALGORITHMS_ASYMMETRIC:
        raise AuthError(code="invalid_token", message="Unsupported JWT algorithm.")

    kid = header.get("kid")
    if not kid:
        raise AuthError(code="invalid_token", message="JWT header missing kid.")

    try:
        jwks = await jwks_cache.get()
    except httpx.HTTPError as exc:
        raise AuthError(
            code="jwks_unavailable",
            message="Unable to fetch JWKS.",
            status_code=503,
        ) from exc

    key = _find_jwk(jwks, kid)
    if not key:
        raise AuthError(code="invalid_token", message="JWKS key not found.")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS_ASYMMETRIC,
            issuer=issuer,
            audience=settings.supabase_jwt_audience,
            options=options,
        )
        return cast(dict[str, Any], payload)
    except JWTError as exc:
        raise AuthError(
            code="invalid_token",
            message="Invalid JWT.",
        ) from exc


async def require_jwt(
    settings: Annotated[Settings, Depends(get_settings)],
    jwks_cache: Annotated[JWKSCache, Depends(get_jwks_cache)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization:
        raise AuthError(code="missing_token", message="Missing Authorization header.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthError(
            code="invalid_token",
            message="Authorization header must be a Bearer token.",
        )
    return await decode_jwt(token, settings=settings, jwks_cache=jwks_cache)


def _parse_uuid_claim(claims: dict[str, Any], key: str) -> uuid.UUID:
    value = claims.get(key)
    if value is None:
        raise AuthError(
            code=f"missing_{key}_claim",
            message=f"JWT is missing required '{key}' claim.",
        )
    if not isinstance(value, str) or not value.strip():
        raise AuthError(
            code=f"invalid_{key}_claim",
            message=f"JWT '{key}' claim must be a non-empty UUID string.",
        )
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise AuthError(
            code=f"invalid_{key}_claim",
            message=f"JWT '{key}' claim must be a valid UUID.",
        ) from exc


def _parse_optional_uuid_claim(claims: dict[str, Any], key: str) -> uuid.UUID | None:
    value = claims.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AuthError(
            code=f"invalid_{key}_claim",
            message=f"JWT '{key}' claim must be a non-empty UUID string.",
        )
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise AuthError(
            code=f"invalid_{key}_claim",
            message=f"JWT '{key}' claim must be a valid UUID.",
        ) from exc


async def require_auth_context(
    claims: Annotated[dict[str, Any], Depends(require_jwt)],
) -> AuthContext:
    user_id = _parse_uuid_claim(claims, "sub")
    client_id = _parse_optional_uuid_claim(claims, "client_id")
    return AuthContext(claims=claims, client_id=client_id, user_id=user_id)


async def require_client_auth_context(
    claims: Annotated[dict[str, Any], Depends(require_jwt)],
) -> AuthContext:
    client_id = _parse_uuid_claim(claims, "client_id")
    user_id = _parse_uuid_claim(claims, "sub")
    return AuthContext(claims=claims, client_id=client_id, user_id=user_id)
