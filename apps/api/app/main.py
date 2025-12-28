from __future__ import annotations

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.routers import health, protected, version


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ChapterVerse API",
        description="API for the ChapterVerse book tracking application",
        version=settings.api_version,
    )
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(version.router)
    app.include_router(protected.router)
    return app
