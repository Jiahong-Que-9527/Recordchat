"""Application configuration (SPEC section 8).

All runtime knobs come from environment variables / .env.
RecordChat now requires externally hosted LLM and embedding APIs.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # LLM
    llm_provider: str = "openai"           # qwen | openai | claude
    llm_model: str = "qwen-plus"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # Embedding
    embedding_provider: str = "openai"     # qwen | openai
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_dim: int = 1536

    # Qdrant — ":memory:" runs an embedded in-process store (offline friendly)
    qdrant_url: str = ":memory:"
    qdrant_collection: str = "recordchat_one_record"

    # RAG
    rag_top_k: int = 5

    # CORS (frontend origin)
    cors_origins: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
