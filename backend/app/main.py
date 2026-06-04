"""RecordChat FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, ingest
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


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

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(ingest.router)

    logger.info(
        "RecordChat started (llm=%s, embedding=%s, qdrant=%s)",
        settings.llm_provider, settings.embedding_provider, settings.qdrant_url,
    )
    return app


app = create_app()
