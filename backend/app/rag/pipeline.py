"""RAG orchestration (SPEC section 7).

This is the ONLY place that ties retrieval + prompt + LLM + domain tools
together. API handlers call `answer()`; they contain no business logic.
"""

from __future__ import annotations

import re

from app.core.config import get_settings
from app.core.llm import LLMProvider, get_llm_provider
from app.core.logging import get_logger
from app.domain import jsonld_generator, one_record_schema
from app.models.chat import ChatResponse, QueryType, Source
from app.rag import prompt as prompt_mod
from app.rag.reranker import rerank
from app.rag.retriever import Retriever, get_retriever

logger = get_logger(__name__)

# Fetch extra candidates for ontology-aware reranking (ADR 0002).
_CANDIDATE_POOL_MULTIPLIER = 3
_MAX_CANDIDATE_POOL = 20


def classify_query(query: str) -> QueryType:
    """Rule-based classifier (SPEC section 7). Replaceable by an LLM classifier."""
    q = query.lower()
    if ("json-ld" in q or "jsonld" in q or "payload" in q) and (
        "generate" in q or "example" in q or "create" in q
    ):
        return QueryType.jsonld_generation
    if any(k in q for k in ("relationship", "related", "difference between", " vs", "vs.")):
        return QueryType.relationship_question
    if any(k in q for k in ("api", "endpoint", "subscription", "server", "how do i create")):
        return QueryType.api_question
    if any(k in q for k in ("what is", "explain", "define", "what are")):
        return QueryType.concept_explanation
    return QueryType.general_question


def _related_concepts(query: str, chunks) -> list[str]:
    """Union of entities detected in the query, chunk metadata, and the
    curated relationship map."""
    related: list[str] = []

    def _add(items):
        for it in items:
            if it and it not in related:
                related.append(it)

    for ent in one_record_schema.detect_entities(query):
        _add([ent])
        _add(one_record_schema.get_related(ent))
    for c in chunks:
        if c.metadata.entity:
            _add([c.metadata.entity])
        _add(c.metadata.related_entities)
    return related[:8]


def _jsonld_entity(query: str) -> str | None:
    for ent in jsonld_generator.GENERATORS:
        if re.search(rf"\b{ent.lower()}\b", query.lower()):
            return ent
    return None


def answer(
    query: str,
    retriever: Retriever | None = None,
    llm: LLMProvider | None = None,
) -> ChatResponse:
    settings = get_settings()
    retriever = retriever or get_retriever()
    llm = llm or get_llm_provider()

    query_type = classify_query(query)
    pool_size = min(
        settings.rag_top_k * _CANDIDATE_POOL_MULTIPLIER,
        _MAX_CANDIDATE_POOL,
    )
    chunks = retriever.search(query, top_k=max(pool_size, settings.rag_top_k))
    chunks = rerank(query, chunks)[: settings.rag_top_k]

    user_prompt = prompt_mod.build_user_prompt(query, chunks, query_type)
    answer_text = llm.complete(system=prompt_mod.SYSTEM_PROMPT, user=user_prompt)

    structured_output = None
    if query_type == QueryType.jsonld_generation:
        structured_output = jsonld_generator.generate_for_entity(_jsonld_entity(query))

    sources = [
        Source(
            source_name=c.metadata.source_name,
            section_title=c.metadata.section_title,
            source_url=c.metadata.source_url,
            chunk_id=c.chunk_id,
        )
        for c in chunks
    ]

    return ChatResponse(
        answer=answer_text,
        query_type=query_type,
        sources=sources,
        related_concepts=_related_concepts(query, chunks),
        structured_output=structured_output,
    )
