from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.responses import ok
from app.core.security import require_jwt

router = APIRouter(
    prefix="/api/v1/protected",
    tags=["protected"],
    dependencies=[Depends(require_jwt)],
)


@router.get("/ping")
async def protected_ping() -> dict[str, object]:
    return ok({"pong": True})
