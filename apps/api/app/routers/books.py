from __future__ import annotations

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import enforce_client_user_rate_limit
from app.core.responses import ok
from app.core.security import AuthContext, require_client_auth_context
from app.db.session import get_db_session
from app.services.catalog import import_openlibrary_bundle
from app.services.open_library import OpenLibraryClient


class ImportBookRequest(BaseModel):
    work_key: str = Field(min_length=3)
    edition_key: str | None = None


def get_open_library_client() -> OpenLibraryClient:
    return OpenLibraryClient()


router = APIRouter(
    prefix="/api/v1/books",
    tags=["books"],
    dependencies=[Depends(enforce_client_user_rate_limit)],
)


@router.get("/search")
async def search_books(
    query: Annotated[str, Query(min_length=1)],
    _auth: Annotated[AuthContext, Depends(require_client_auth_context)],
    open_library: Annotated[OpenLibraryClient, Depends(get_open_library_client)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    page: Annotated[int, Query(ge=1)] = 1,
) -> dict[str, object]:
    try:
        response = await open_library.search_books(query=query, limit=limit, page=page)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "open_library_unavailable",
                "message": "Open Library is unavailable. Please try again shortly.",
            },
        ) from exc
    return ok(
        {
            "items": [
                {
                    "work_key": item.work_key,
                    "title": item.title,
                    "author_names": item.author_names,
                    "first_publish_year": item.first_publish_year,
                    "cover_url": item.cover_url,
                }
                for item in response.items
            ],
            "cache_hit": response.cache_hit,
        }
    )


@router.post("/import")
async def import_book(
    payload: ImportBookRequest,
    _auth: Annotated[AuthContext, Depends(require_client_auth_context)],
    session: Annotated[Session, Depends(get_db_session)],
    open_library: Annotated[OpenLibraryClient, Depends(get_open_library_client)],
) -> dict[str, object]:
    try:
        bundle = await open_library.fetch_work_bundle(
            work_key=payload.work_key,
            edition_key=payload.edition_key,
        )
        result = import_openlibrary_bundle(session, bundle=bundle)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "open_library_unavailable",
                "message": "Open Library is unavailable. Please try again shortly.",
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ok(result)
