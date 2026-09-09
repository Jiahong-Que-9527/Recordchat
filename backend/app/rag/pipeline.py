"""RAG orchestration (SPEC section 7).

This is the ONLY place that ties retrieval + prompt + LLM + domain tools
together. API handlers call `answer()`; they contain no business logic.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from app.connectors.orchestration import run_synthetic_data_workflow
from app.core.config import get_settings
from app.core.llm import LLMProvider, get_llm_provider
from app.core.logging import get_logger
from app.core.request_log import RequestTimer, log_chat_request
from app.domain import jsonld_generator, one_record_schema
from app.models.chat import ChatHistoryMessage, ChatResponse, QueryType, Source
from app.models.source import Chunk
from app.rag import prompt as prompt_mod
from app.rag.lexical import tokenize
from app.rag.reranker import rerank
from app.rag.retriever import Retriever, SearchFilter, get_retriever

logger = get_logger(__name__)

# Fetch extra candidates for ontology-aware / hybrid reranking (ADR 0002, #29).
_CANDIDATE_POOL_MULTIPLIER = 8
_MAX_CANDIDATE_POOL = 60
_ONTOLOGY_CANDIDATE_LIMIT = 12

_EXAMPLE_REQUEST_MARKERS = (
    "example",
    "sample",
    "json-ld",
    "jsonld",
    "payload",
    "示例",
    "样例",
    "例子",
)


def _wants_examples(query: str) -> bool:
    q = query.lower()
    return any(marker in q or marker in query for marker in _EXAMPLE_REQUEST_MARKERS)


def search_filter_for_query(query: str, query_type: QueryType) -> SearchFilter | None:
    """Query-type metadata filters for hybrid retrieval (#29)."""
    if query_type == QueryType.ontology_question:
        return SearchFilter(chunk_types=("class_definition", "property_definition", "concept"))
    if query_type == QueryType.api_question:
        return SearchFilter(chunk_types=("api", "concept", "general"))
    if query_type == QueryType.implementation_question:
        # Prefer docs/config; exclude bulk example JSON unless explicitly requested.
        if _wants_examples(query):
            return None
        return SearchFilter(exclude_chunk_types=("example",))
    if query_type == QueryType.jsonld_generation:
        return None
    if not _wants_examples(query) and query_type in {
        QueryType.concept_explanation,
        QueryType.relationship_question,
        QueryType.general_question,
    }:
        # Soft preference: keep examples out of the default concept pool.
        return SearchFilter(exclude_chunk_types=("example",))
    return None


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


def rewrite_query_for_retrieval(
    query: str,
    history: list[ChatHistoryMessage] | None = None,
) -> str:
    """Carry entities from prior user turns into follow-up retrieval (#30 / AUD-06)."""
    if not history:
        return query

    prior_entities: list[str] = []
    for turn in reversed(history):
        if turn.role != "user" or not turn.content.strip():
            continue
        for entity in one_record_schema.detect_entities(turn.content):
            if entity not in prior_entities:
                prior_entities.append(entity)
        if len(prior_entities) >= 5:
            break

    if not prior_entities:
        return query

    current = set(one_record_schema.detect_entities(query))
    missing = [entity for entity in prior_entities if entity not in current]
    if not missing:
        return query
    return f"{query} (entities from earlier turns: {', '.join(missing)})"


def filter_cited_chunks(answer_text: str, chunks: list[Chunk]) -> list[Chunk]:
    """Keep only chunks that appear to support the answer (#31 / AUD-05).

    Prefer no citation over a wrong one. Overlap is scored from entity /
    source / section mentions plus lexical token overlap with the answer.
    """
    if not chunks:
        return []
    if not answer_text.strip():
        return []

    answer_low = answer_text.lower()
    answer_tokens = set(tokenize(answer_text))
    scored: list[tuple[int, Chunk]] = []

    for chunk in chunks:
        score = 0
        entity = chunk.metadata.entity
        if entity and entity.lower() in answer_low:
            score += 3
        source = chunk.metadata.source_name or ""
        if source and source.lower() in answer_low:
            score += 2
        section = chunk.metadata.section_title or ""
        if section and section.lower() in answer_low:
            score += 2

        content_tokens = set(tokenize(chunk.content))
        if content_tokens and answer_tokens:
            overlap = len(content_tokens & answer_tokens)
            ratio = overlap / max(len(content_tokens), 1)
            # Require absolute overlap so a shared stopword like "is" cannot
            # promote an unrelated short payload via ratio alone.
            if overlap >= 8 or (overlap >= 4 and ratio >= 0.12):
                score += 3
            elif overlap >= 4 or (overlap >= 3 and ratio >= 0.08):
                score += 2
            elif overlap >= 3:
                score += 1

        # Distinctive multi-word fragment from the chunk appears in the answer.
        snippet = " ".join(chunk.content.split())[:80].lower()
        if len(snippet) >= 24 and snippet in answer_low:
            score += 4

        if score > 0:
            scored.append((score, chunk))

    if not scored:
        return []

    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[0][0]
    threshold = max(2, best // 2)
    return [chunk for score, chunk in scored if score >= threshold]


def _prepare_answer_context(
    query: str,
    retriever: Retriever,
    *,
    history: list[ChatHistoryMessage] | None = None,
) -> tuple[QueryType, list, str]:
    settings = get_settings()
    query_type = classify_query(query)
    retrieval_query = rewrite_query_for_retrieval(query, history)
    pool_size = min(
        settings.rag_top_k * _CANDIDATE_POOL_MULTIPLIER,
        _MAX_CANDIDATE_POOL,
    )
    search_filter = search_filter_for_query(retrieval_query, query_type)
    chunks = retriever.search(
        retrieval_query,
        top_k=max(pool_size, settings.rag_top_k),
        search_filter=search_filter,
    )
    if query_type in {QueryType.ontology_question, QueryType.relationship_question, QueryType.concept_explanation}:
        ontology_chunks = retriever.search_ontology_candidates(
            one_record_schema.detect_entities(retrieval_query),
            top_k=_ONTOLOGY_CANDIDATE_LIMIT,
        )
        by_chunk_id = {chunk.chunk_id: chunk for chunk in chunks}
        for chunk in ontology_chunks:
            by_chunk_id.setdefault(chunk.chunk_id, chunk)
        chunks = list(by_chunk_id.values())
    chunks = rerank(retrieval_query, chunks)[: settings.rag_top_k]
    user_prompt = prompt_mod.build_user_prompt(query, chunks, query_type)
    return query_type, chunks, user_prompt


def _chunk_log_entries(chunks: list[Chunk]) -> list[dict]:
    return [
        {
            "rank": index + 1,
            "chunk_id": chunk.chunk_id,
            "source_name": chunk.metadata.source_name,
            "chunk_type": chunk.metadata.chunk_type,
            "entity": chunk.metadata.entity,
            "version": chunk.metadata.version,
        }
        for index, chunk in enumerate(chunks)
    ]


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


def _answer_synthetic(query: str, *, model: str | None = None) -> ChatResponse:
    """Workflow path — no RAG retrieval (#32)."""
    timer = RequestTimer()
    settings = get_settings()
    workflow = run_synthetic_data_workflow(query, settings=settings)
    response = ChatResponse(
        answer=workflow.to_answer_text(),
        query_type=QueryType.synthetic_data_generation,
        sources=[],
        related_concepts=one_record_schema.detect_entities(query)[:8],
        structured_output=workflow.model_dump(mode="json"),
    )
    log_chat_request(
        {
            "event": "chat",
            "query": query,
            "query_type": response.query_type.value,
            "model": model or settings.llm_model,
            "llm_provider": settings.llm_provider,
            "latency_ms": timer.latency_ms(),
            "chunks": [],
            "source_count": 0,
            "workflow_status": workflow.status,
            "connector": workflow.connector.availability.value,
        }
    )
    return response


def answer(
    query: str,
    retriever: Retriever | None = None,
    llm: LLMProvider | None = None,
    model: str | None = None,
    history: list[ChatHistoryMessage] | None = None,
) -> ChatResponse:
    timer = RequestTimer()
    settings = get_settings()
    error: str | None = None

    try:
        if classify_query(query) == QueryType.synthetic_data_generation:
            return _answer_synthetic(query, model=model)

        retriever = retriever or get_retriever()
        llm = llm or get_llm_provider(model=model)

        query_type, chunks, user_prompt = _prepare_answer_context(
            query, retriever, history=history
        )
        answer_text = llm.complete(system=prompt_mod.SYSTEM_PROMPT, user=user_prompt)
        if not answer_text.strip():
            logger.warning("LLM returned an empty answer; using grounded fallback text.")
            answer_text = _fallback_answer_from_chunks(query, chunks)
            cited = chunks[:2]
        else:
            cited = filter_cited_chunks(answer_text, chunks)

        structured_output = None
        if query_type == QueryType.jsonld_generation:
            structured_output = jsonld_generator.generate_for_entity(_jsonld_entity(query))

        response = ChatResponse(
            answer=answer_text,
            query_type=query_type,
            sources=_sources_from_chunks(cited),
            related_concepts=_related_concepts(query, chunks),
            structured_output=structured_output,
        )
        log_chat_request(
            {
                "event": "chat",
                "query": query,
                "query_type": query_type.value,
                "model": model or settings.llm_model,
                "llm_provider": settings.llm_provider,
                "latency_ms": timer.latency_ms(),
                "chunks": _chunk_log_entries(chunks),
                "cited_chunk_ids": [c.chunk_id for c in cited],
                "source_count": len(response.sources),
                "history_turns": len(history or []),
            }
        )
        return response
    except Exception as exc:
        error = str(exc)
        log_chat_request(
            {
                "event": "chat_error",
                "query": query,
                "model": model or settings.llm_model,
                "llm_provider": settings.llm_provider,
                "latency_ms": timer.latency_ms(),
                "error": error,
            }
        )
        raise


def answer_stream(
    query: str,
    retriever: Retriever | None = None,
    llm: LLMProvider | None = None,
    model: str | None = None,
    history: list[ChatHistoryMessage] | None = None,
) -> Iterator[dict]:
    timer = RequestTimer()
    settings = get_settings()

    if classify_query(query) == QueryType.synthetic_data_generation:
        response = _answer_synthetic(query, model=model)
        yield {"event": "token", "data": {"text": response.answer}}
        yield {"event": "metadata", "data": response.model_dump(mode="json")}
        return

    retriever = retriever or get_retriever()
    llm = llm or get_llm_provider(model=model)

    query_type, chunks, user_prompt = _prepare_answer_context(
        query, retriever, history=history
    )
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
        cited = chunks[:2]
    else:
        cited = filter_cited_chunks(answer_text, chunks)

    structured_output = None
    if query_type == QueryType.jsonld_generation:
        structured_output = jsonld_generator.generate_for_entity(_jsonld_entity(query))

    response = ChatResponse(
        answer=answer_text,
        query_type=query_type,
        sources=_sources_from_chunks(cited),
        related_concepts=_related_concepts(query, chunks),
        structured_output=structured_output,
    )
    log_chat_request(
        {
            "event": "chat_stream",
            "query": query,
            "query_type": query_type.value,
            "model": model or settings.llm_model,
            "llm_provider": settings.llm_provider,
            "latency_ms": timer.latency_ms(),
            "chunks": _chunk_log_entries(chunks),
            "cited_chunk_ids": [c.chunk_id for c in cited],
            "source_count": len(response.sources),
            "history_turns": len(history or []),
        }
    )
    yield {"event": "metadata", "data": response.model_dump(mode="json")}
