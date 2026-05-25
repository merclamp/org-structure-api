import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging

from app.routers import departments

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API for managing an organizational structure.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["meta"], summary="Health check")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc: NotFoundError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc: ConflictError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request, exc: ValidationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(BusinessError)
    async def business_error_handler(request, exc: BusinessError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


app = create_app()

app.include_router(departments.router)