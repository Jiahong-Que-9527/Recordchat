"""RecordChat FastAPI application entrypoint."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, chat, health, ingest, internal_users
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _base_url_label(url: str) -> str:
    if not url:
        return "default"
    parsed = urlparse(url)
    return parsed.netloc or parsed.path or "configured"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RecordChat", version="0.1.0")

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def _http_error(_request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
                headers=dict(exc.headers or {}),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc.detail)},
            headers=dict(exc.headers or {}),
        )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(ingest.router)
    app.include_router(internal_users.router)
    app.include_router(admin.router)

    logger.info(
        "RecordChat started (llm=%s/%s key=%s base=%s, embedding=%s/%s key=%s base=%s, qdrant=%s collection=%s)",
        settings.llm_provider,
        settings.llm_model,
        "yes" if settings.llm_api_key else "no",
        _base_url_label(settings.llm_base_url),
        settings.embedding_provider,
        settings.embedding_model,
        "yes" if settings.embedding_api_key else "no",
        _base_url_label(settings.embedding_base_url),
        "in_memory" if settings.qdrant_url in ("", ":memory:") else "remote",
        settings.qdrant_collection,
    )
    return app


app = create_app()
