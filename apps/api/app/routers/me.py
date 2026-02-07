from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import enforce_client_user_rate_limit
from app.core.responses import ok
from app.core.security import AuthContext, require_auth_context
from app.db.session import get_db_session
from app.services.user_library import get_or_create_profile, update_profile


class UpdateProfileRequest(BaseModel):
    handle: str | None = Field(default=None, max_length=64)
    display_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=2048)


router = APIRouter(
    prefix="/api/v1/me",
    tags=["me"],
    dependencies=[Depends(enforce_client_user_rate_limit)],
)


@router.get("")
def get_me(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, object]:
    profile = get_or_create_profile(session, user_id=auth.user_id)
    return ok(
        {
            "id": str(profile.id),
            "handle": profile.handle,
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
        }
    )


@router.patch("")
def patch_me(
    payload: UpdateProfileRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, object]:
    try:
        profile = update_profile(
            session,
            user_id=auth.user_id,
            handle=payload.handle,
            display_name=payload.display_name,
            avatar_url=payload.avatar_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ok(
        {
            "id": str(profile.id),
            "handle": profile.handle,
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
        }
    )
