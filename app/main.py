"""
ElectionGuide AI - Main Application Entry Point
Production-ready FastAPI application for election process assistance.
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file (GEMINI_API_KEY, etc.)

import os
import uuid
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import chat, election, health
from app.utils.logging_config import setup_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (in-memory; swap for Redis in HA setups)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ElectionGuide AI starting up…")
    yield
    logger.info("ElectionGuide AI shutting down…")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title="ElectionGuide AI",
        description="Interactive Election Process Assistant powered by Vertex AI",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── Security middleware ─────────────────────────────────────────────────
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    trusted_hosts = os.getenv("TRUSTED_HOSTS", "*").split(",")
    if trusted_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # ── Request tracing middleware ───────────────────────────────────────────
    @app.middleware("http")
    async def request_tracing(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        logger.info(
            "req=%s %s %s %sms",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        return response

    # ── Rate limiter ────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── API routers ─────────────────────────────────────────────────────────
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(election.router, prefix="/api/election", tags=["election"])

    # ── Static files ────────────────────────────────────────────────────────
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # ── SPA catch-all ───────────────────────────────────────────────────────
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(static_dir, "index.html"))

    return app


app = create_app()
