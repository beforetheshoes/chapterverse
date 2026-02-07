from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import enforce_client_user_rate_limit
from app.core.responses import ok
from app.core.security import AuthContext, require_auth_context
from app.db.session import get_db_session
from app.services.user_library import (
    create_or_get_library_item,
    delete_library_item,
    list_library_items,
    update_library_item,
)


class CreateLibraryItemRequest(BaseModel):
    work_id: uuid.UUID
    preferred_edition_id: uuid.UUID | None = None
    status: str | None = Field(default=None, max_length=32)
    visibility: str | None = Field(default=None, max_length=32)
    rating: int | None = Field(default=None, ge=0, le=10)
    tags: list[str] | None = None


class UpdateLibraryItemRequest(BaseModel):
    preferred_edition_id: uuid.UUID | None = None
    status: str | None = Field(default=None, max_length=32)
    visibility: str | None = Field(default=None, max_length=32)
    rating: int | None = Field(default=None, ge=0, le=10)
    tags: list[str] | None = None


router = APIRouter(
    prefix="/api/v1/library/items",
    tags=["library"],
    dependencies=[Depends(enforce_client_user_rate_limit)],
)


@router.get("")
def list_items(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    visibility: str | None = None,
) -> dict[str, object]:
    try:
        result = list_library_items(
            session,
            user_id=auth.user_id,
            limit=limit,
            cursor=cursor,
            status=status,
            tag=tag,
            visibility=visibility,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok(result)


@router.post("")
def create_item(
    payload: CreateLibraryItemRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, object]:
    try:
        item, created = create_or_get_library_item(
            session,
            user_id=auth.user_id,
            work_id=payload.work_id,
            preferred_edition_id=payload.preferred_edition_id,
            status=payload.status,
            visibility=payload.visibility,
            rating=payload.rating,
            tags=payload.tags,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ok(
        {
            "id": str(item.id),
            "work_id": str(item.work_id),
            "status": item.status,
            "visibility": item.visibility,
            "rating": item.rating,
            "tags": item.tags or [],
            "created": created,
        }
    )


@router.patch("/{item_id}")
def patch_item(
    item_id: uuid.UUID,
    payload: UpdateLibraryItemRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, object]:
    updates = payload.model_dump(exclude_unset=True)
    try:
        item = update_library_item(
            session,
            user_id=auth.user_id,
            item_id=item_id,
            updates=updates,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ok(
        {
            "id": str(item.id),
            "work_id": str(item.work_id),
            "status": item.status,
            "visibility": item.visibility,
            "rating": item.rating,
            "tags": item.tags or [],
        }
    )


@router.delete("/{item_id}")
def remove_item(
    item_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, object]:
    try:
        delete_library_item(
            session,
            user_id=auth.user_id,
            item_id=item_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ok({"deleted": True})
