from __future__ import annotations

from fastapi import APIRouter

from app.core.responses import ok

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
async def health() -> dict[str, object]:
    return ok({"status": "ok"})
