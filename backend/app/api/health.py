from fastapi import APIRouter

from app.core.config import get_settings
from app.models.chat import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        llm_api_key_configured=bool(settings.llm_api_key),
        llm_base_url_configured=bool(settings.llm_base_url),
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_api_key_configured=bool(settings.embedding_api_key),
        embedding_base_url_configured=bool(settings.embedding_base_url),
        qdrant_mode="in_memory" if settings.qdrant_url in ("", ":memory:") else "remote",
        qdrant_collection=settings.qdrant_collection,
    )
