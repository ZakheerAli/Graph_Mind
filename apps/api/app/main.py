import time
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.logging import configure_logging
from .routers.documents import router as documents_router
from .routers.health import router as health_router

configure_logging()
logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="GraphMind API", version="0.1.0")

    if settings.allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    application.include_router(health_router)
    application.include_router(documents_router)

    @application.middleware("http")
    async def add_request_context(request: Request, call_next):
        structlog.contextvars.clear_contextvars()
        trace_id = uuid4().hex
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            logger.info(
                "request_completed",
                method=request.method,
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return response
        finally:
            structlog.contextvars.clear_contextvars()

    return application


app = create_app()














