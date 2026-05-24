"""FastAPI application entrypoint.

`create_app()` builds and configures the application; `app` is the
ASGI instance picked up by uvicorn (`uvicorn app.main:app`).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown hooks."""
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API for managing an organizational structure.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["meta"], summary="Health check")
    async def health() -> dict[str, str]:
        """Lightweight liveness probe."""
        return {"status": "ok"}

    return app


app = create_app()
