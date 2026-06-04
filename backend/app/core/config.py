"""Application configuration (SPEC section 8).

All runtime knobs come from environment variables / .env.
Graceful degradation rule: a missing API key must NOT crash the app.
The provider factories (core/llm.py, core/embeddings.py) fall back to a
local implementation and log a warning instead.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str = "local"            # local | qwen | openai | claude
    llm_model: str = "qwen-plus"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # Embedding
    embedding_provider: str = "local"      # local | qwen | openai
    embedding_model: str = "text-embedding-v4"
    embedding_api_key: str = ""
    embedding_dim: int = 1024

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
