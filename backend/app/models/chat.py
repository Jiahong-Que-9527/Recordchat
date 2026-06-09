"""Public API contract models (SPEC section 6).

Field names here are a HARD CONTRACT shared with the frontend.
Do not rename fields without updating the SPEC and the frontend.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    concept_explanation = "concept_explanation"
    relationship_question = "relationship_question"
    api_question = "api_question"
    implementation_question = "implementation_question"
    ontology_question = "ontology_question"
    jsonld_generation = "jsonld_generation"
    general_question = "general_question"


# ---- /health ----
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "recordchat-backend"
    llm_provider: str
    llm_model: str
    llm_api_key_configured: bool
    llm_base_url_configured: bool
    embedding_provider: str
    embedding_model: str
    embedding_api_key_configured: bool
    embedding_base_url_configured: bool
    qdrant_mode: str
    qdrant_collection: str


# ---- /chat ----
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class Source(BaseModel):
    source_name: str
    section_title: str | None = None
    source_url: str | None = None
    chunk_id: str


class ChatResponse(BaseModel):
    answer: str
    query_type: QueryType
    sources: list[Source] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    structured_output: dict[str, Any] | None = None


# ---- /ingest ----
class IngestRequest(BaseModel):
    reset: bool = True
    source_dir: str = "data/raw"


class IngestResponse(BaseModel):
    status: str = "ok"
    documents_loaded: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
