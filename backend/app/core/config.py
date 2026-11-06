"""Application configuration (SPEC section 8)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # LLM
    llm_provider: str = "openai"           # openai | qwen | claude
    llm_model: str = "deepseek-v4-flash"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # Embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_dim: int = 1536

    # Qdrant
    qdrant_url: str = ":memory:"
    qdrant_collection: str = "recordchat_one_record"
    qdrant_upsert_batch_size: int = 128
    qdrant_api_key: str = ""

    # Workflow connectors
    recordforge_url: str = ""
    recordforge_api_key: str = ""

    # RAG
    rag_top_k: int = 5

    # Canonical source versions (AUD-02 / #27). Comma-separated allowlists.
    # Non-canonical copies stay on disk but are skipped at ingest / OntologyGraph.
    canonical_ontology_versions: str = "2025-07"
    canonical_api_ontology_versions: str = "current"
    canonical_openapi_versions: str = "2024-12"
    canonical_spec_versions: str = "development,2025-07"

    # CORS (frontend origin)
    cors_origins: str = "http://localhost:3000"

    # Trial auth (v0.3.1). off = local/CI; enforced = public.
    auth_mode: str = "off"
    internal_auth_secret: str = ""
    internal_jwt_ttl_seconds: int = 90
    email_hash_pepper: str = ""
    admin_idp_user_ids: str = ""
    admin_emails: str = ""
    recordchat_db_path: str = "data/app/recordchat.db"
    session_ttl_seconds: int = 604800
    auth_debug: bool = False

    chat_daily_limit_trial: int = 30
    chat_daily_limit_user: int = 100
    chat_max_concurrent_per_user: int = 1
    chat_max_message_chars: int = 4000
    chat_max_history_turns: int = 6
    chat_global_max_streams: int = 10
    llm_daily_budget_usd: float = 15.0
    llm_usd_per_1k_tokens: float = 0.002
    llm_kill_switch: bool = False

    ingest_token: str = ""
    ingest_allow_reset: bool = True

    def auth_enforced(self) -> bool:
        return self.auth_mode.strip().lower() == "enforced"


@lru_cache
def get_settings() -> Settings:
    return Settings()
