from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.responses import ok

router = APIRouter(tags=["version"])


@router.get("/api/v1/version")
async def version(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    return ok({"version": settings.api_version})
