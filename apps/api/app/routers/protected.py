from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.rate_limit import enforce_client_user_rate_limit
from app.core.responses import ok
from app.core.security import AuthContext, require_client_auth_context

router = APIRouter(
    prefix="/api/v1/protected",
    tags=["protected"],
    dependencies=[Depends(enforce_client_user_rate_limit)],
)


@router.get("/ping")
async def protected_ping(
    _auth: Annotated[AuthContext, Depends(require_client_auth_context)],
) -> dict[str, object]:
    return ok({"pong": True})
