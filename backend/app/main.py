"""
FinTwin AI — FastAPI Application Factory
Configures middleware, routers, exception handlers, and startup/shutdown events.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.exceptions import FinTwinException
from app.db.base import engine, init_db
from app.utils.logger import configure_logging

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle handler."""
    logger.info(
        "Starting FinTwin AI",
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )

    # Initialize database connection pool
    await init_db()
    logger.info("Database connection pool initialized")

    # Initialize Qdrant collections
    from app.utils.qdrant_init import ensure_collections
    await ensure_collections()
    logger.info("Qdrant vector collections verified")

    # Load ML models into memory
    from ai_modules.risk_prediction.model_registry import ModelRegistry
    await ModelRegistry.instance().load_all()
    logger.info("ML models loaded into memory")

    yield

    # Shutdown
    logger.info("Shutting down FinTwin AI")
    await engine.dispose()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Application factory — returns configured FastAPI instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Digital Twin Platform for Intelligent MSME Loan Risk Assessment",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ---- Middleware (order matters: outermost = first to process request) ----
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # ---- Request ID + Timing middleware ----
    @app.middleware("http")
    async def request_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.2f}ms"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        logger.info(
            "Request completed",
            status_code=response.status_code,
            duration_ms=round(duration, 2),
        )
        return response

    # ---- Exception Handlers ----
    @app.exception_handler(FinTwinException)
    async def fintwin_exception_handler(
        request: Request, exc: FinTwinException
    ) -> JSONResponse:
        logger.warning(
            "FinTwin business exception",
            code=exc.code,
            detail=exc.detail,
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": exc.code,
                "field_errors": exc.field_errors,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred.",
                "code": "INTERNAL_ERROR",
                "field_errors": {},
            },
        )

    # ---- Routers ----
    app.include_router(api_v1_router, prefix="/api/v1")

    # ---- Health endpoints ----
    @app.get("/health", include_in_schema=False)
    async def health_check() -> dict:
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"service": settings.APP_NAME, "version": settings.APP_VERSION}

    # ---- Prometheus metrics ----
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/health", "/"],
    ).instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
