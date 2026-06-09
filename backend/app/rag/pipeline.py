"""RAG orchestration (SPEC section 7).

This is the ONLY place that ties retrieval + prompt + LLM + domain tools
together. API handlers call `answer()`; they contain no business logic.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from app.core.config import get_settings
from app.core.llm import LLMProvider, get_llm_provider
from app.core.logging import get_logger
from app.connectors.base import ConnectorAvailability
from app.domain import jsonld_generator, one_record_schema
from app.models.chat import ChatResponse, QueryType, Source
from app.rag import prompt as prompt_mod
from app.rag.reranker import rerank
from app.rag.retriever import Retriever, get_retriever

logger = get_logger(__name__)

# Fetch extra candidates for ontology-aware reranking (ADR 0002).
_CANDIDATE_POOL_MULTIPLIER = 3
_MAX_CANDIDATE_POOL = 20
_ONTOLOGY_CANDIDATE_LIMIT = 12


def _is_ontology_query(query: str) -> bool:
    q = query.lower()
    return any(
        marker in q
        for marker in (
            "ontology",
            "subclass",
            "superclass",
            "class is",
            "class does",
            "property",
            "properties",
            "domain",
            "range",
            "connect",
            "connected to",
            "本体",
            "子类",
            "父类",
            "属性",
            "定义域",
            "值域",
        )
    ) or ("关联" in query and any(token in query for token in ("什么属性", "哪个属性", "哪些属性")))


def _is_synthetic_generation_query(query: str) -> bool:
    q = query.lower()
    explicit_generation_markers = (
        "synthetic",
        "fake data",
        "mock data",
        "sample data",
        "test data",
        "generate shipment",
        "generate shipments",
        "generate piece",
        "generate pieces",
        "seed shipment",
        "seed data",
        "合成数据",
        "模拟数据",
        "测试数据",
        "生成 shipment",
        "生成 shipments",
        "生成 piece",
        "生成 pieces",
        "生成 5 个 shipment",
        "生成 5 个 shipments",
    )
    object_markers = (
        "shipment",
        "shipments",
        "piece",
        "pieces",
        "waybill",
        "logisticsobject",
        "logistics object",
        "订舱",
        "运单",
        "货件",
        "shipment",
        "piece",
    )
    generation_verbs = (
        "generate",
        "create",
        "produce",
        "synthesize",
        "生成",
        "创建",
        "构造",
    )
    if any(marker in q or marker in query for marker in explicit_generation_markers):
        return True
    return any(verb in q or verb in query for verb in generation_verbs) and any(
        marker in q or marker in query for marker in object_markers
    )


def classify_query(query: str) -> QueryType:
    """Rule-based classifier (SPEC section 7). Replaceable by an LLM classifier."""
    q = query.lower()
    implementation_markers = (
        "ne:one",
        "neone",
        "docker compose",
        "docker-compose",
        "keycloak",
        "graphdb",
        "blazegraph",
        "minio",
        "wiremock",
        "gatling",
        "troubleshoot",
        "troubleshooting",
        "config value",
        "configuration",
        "environment variable",
        "http-client.env",
        "start locally",
        "run locally",
        "本地启动",
        "本地运行",
        "环境变量",
        "配置",
        "报错",
        "排查",
        "请求失败",
    )
    implementation_howto_markers = (
        "how do i start",
        "how do i run",
        "what should i check",
        "怎么启动",
        "怎么运行",
        "如何启动",
        "如何运行",
        "怎么排查",
        "如何排查",
    )
    implementation_context_markers = (
        "server",
        "local",
        "deployment",
        "request fails",
        "api request",
        "本地",
        "服务",
        "部署",
        "请求失败",
        "接口请求",
    )
    relationship_markers = (
        "relationship",
        "related",
        "relate to",
        "difference between",
        " vs",
        "vs.",
        "关系",
        "区别",
        "差别",
        "有什么不同",
        "如何关联",
    )
    api_markers = (
        "api",
        "endpoint",
        "subscription",
        "server",
        "how do i create",
        "接口",
        "端点",
        "订阅",
        "通知",
        "怎么创建",
        "如何创建",
    )
    concept_markers = (
        "what is",
        "explain",
        "define",
        "what are",
        "是什么",
        "解释",
        "定义",
        "什么意思",
    )
    if ("json-ld" in q or "jsonld" in q or "payload" in q) and (
        "generate" in q or "example" in q or "create" in q or "生成" in query or "示例" in query
    ):
        return QueryType.jsonld_generation
    if _is_synthetic_generation_query(query):
        return QueryType.synthetic_data_generation
    if _is_ontology_query(query):
        return QueryType.ontology_question
    if any(k in q for k in implementation_markers) or (
        any(k in q or k in query for k in implementation_howto_markers)
        and any(k in q or k in query for k in implementation_context_markers)
    ):
        return QueryType.implementation_question
    if any(k in q or k in query for k in relationship_markers):
        return QueryType.relationship_question
    if any(k in q or k in query for k in api_markers):
        return QueryType.api_question
    if any(k in q or k in query for k in concept_markers):
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


def _fallback_answer_from_chunks(query: str, chunks) -> str:
    snippets = [chunk.content.strip() for chunk in chunks if chunk.content.strip()]
    if not snippets:
        return (
            "I could not find grounded supporting context in the current ONE Record "
            "knowledge base for this question."
        )
    body = "\n\n".join(snippets[:2])
    return (
        "Grounded fallback answer:\n"
        f"{body}\n\n"
        f"Question: {query}"
    )


def _prepare_answer_context(query: str, retriever: Retriever) -> tuple[QueryType, list, str]:
    settings = get_settings()
    query_type = classify_query(query)
    pool_size = min(
        settings.rag_top_k * _CANDIDATE_POOL_MULTIPLIER,
        _MAX_CANDIDATE_POOL,
    )
    chunks = retriever.search(query, top_k=max(pool_size, settings.rag_top_k))
    if query_type == QueryType.ontology_question:
        ontology_chunks = retriever.search_ontology_candidates(
            one_record_schema.detect_entities(query),
            top_k=_ONTOLOGY_CANDIDATE_LIMIT,
        )
        by_chunk_id = {chunk.chunk_id: chunk for chunk in chunks}
        for chunk in ontology_chunks:
            by_chunk_id.setdefault(chunk.chunk_id, chunk)
        chunks = list(by_chunk_id.values())
    chunks = rerank(query, chunks)[: settings.rag_top_k]
    user_prompt = prompt_mod.build_user_prompt(query, chunks, query_type)
    return query_type, chunks, user_prompt


def _synthetic_generation_answer(query: str) -> str:
    settings = get_settings()
    if not settings.recordforge_url:
        availability = ConnectorAvailability.unconfigured.value
        return (
            "This request is classified as synthetic ONE Record data generation, "
            "but the RecordForge connector is not configured yet.\n\n"
            "Implementation note:\n"
            f"Connector status: {availability}. Set RECORDFORGE_URL (and optionally "
            "RECORDFORGE_API_KEY) to enable generation workflows such as synthetic "
            "shipments with pieces. Until then, RecordChat can explain the expected "
            "object model and payload structure, but it cannot execute the generation "
            f"request: {query}"
        )

    return (
        "This request is classified as synthetic ONE Record data generation. "
        "The RecordForge connector is configured, but execution planning is not "
        "implemented in this milestone yet.\n\n"
        "Implementation note:\n"
        "The next orchestration slice will turn this intent into a structured "
        "workflow request against RecordForge."
    )


def _sources_from_chunks(chunks) -> list[Source]:
    return [
        Source(
            source_name=c.metadata.source_name,
            section_title=c.metadata.section_title,
            source_url=c.metadata.source_url,
            chunk_id=c.chunk_id,
        )
        for c in chunks
    ]


def answer(
    query: str,
    retriever: Retriever | None = None,
    llm: LLMProvider | None = None,
) -> ChatResponse:
    retriever = retriever or get_retriever()
    llm = llm or get_llm_provider()

    query_type, chunks, user_prompt = _prepare_answer_context(query, retriever)
    if query_type == QueryType.synthetic_data_generation:
        return ChatResponse(
            answer=_synthetic_generation_answer(query),
            query_type=query_type,
            sources=_sources_from_chunks(chunks),
            related_concepts=_related_concepts(query, chunks),
            structured_output=None,
        )
    answer_text = llm.complete(system=prompt_mod.SYSTEM_PROMPT, user=user_prompt)
    if not answer_text.strip():
        logger.warning("LLM returned an empty answer; using grounded fallback text.")
        answer_text = _fallback_answer_from_chunks(query, chunks)

    structured_output = None
    if query_type == QueryType.jsonld_generation:
        structured_output = jsonld_generator.generate_for_entity(_jsonld_entity(query))

    return ChatResponse(
        answer=answer_text,
        query_type=query_type,
        sources=_sources_from_chunks(chunks),
        related_concepts=_related_concepts(query, chunks),
        structured_output=structured_output,
    )


def answer_stream(
    query: str,
    retriever: Retriever | None = None,
    llm: LLMProvider | None = None,
) -> Iterator[dict]:
    retriever = retriever or get_retriever()
    llm = llm or get_llm_provider()

    query_type, chunks, user_prompt = _prepare_answer_context(query, retriever)
    if query_type == QueryType.synthetic_data_generation:
        answer_text = _synthetic_generation_answer(query)
        yield {"event": "token", "data": {"text": answer_text}}
        response = ChatResponse(
            answer=answer_text,
            query_type=query_type,
            sources=_sources_from_chunks(chunks),
            related_concepts=_related_concepts(query, chunks),
            structured_output=None,
        )
        yield {"event": "metadata", "data": response.model_dump(mode="json")}
        return
    parts: list[str] = []
    for token in llm.complete_stream(system=prompt_mod.SYSTEM_PROMPT, user=user_prompt):
        if token:
            parts.append(token)
            yield {"event": "token", "data": {"text": token}}

    answer_text = "".join(parts).strip()
    if not answer_text:
        logger.warning("LLM stream returned no content; using grounded fallback text.")
        answer_text = _fallback_answer_from_chunks(query, chunks)
        yield {"event": "token", "data": {"text": answer_text}}

    structured_output = None
    if query_type == QueryType.jsonld_generation:
        structured_output = jsonld_generator.generate_for_entity(_jsonld_entity(query))

    response = ChatResponse(
        answer=answer_text,
        query_type=query_type,
        sources=_sources_from_chunks(chunks),
        related_concepts=_related_concepts(query, chunks),
        structured_output=structured_output,
    )
    yield {"event": "metadata", "data": response.model_dump(mode="json")}
