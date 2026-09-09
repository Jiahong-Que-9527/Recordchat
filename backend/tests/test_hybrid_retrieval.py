"""Hybrid retrieval + query-type filters (#29)."""

from app.core.config import Settings
from app.models.chat import QueryType
from app.models.source import Chunk, ChunkMetadata
from app.rag.lexical import LexicalIndex, reciprocal_rank_fuse, tokenize
from app.rag.pipeline import search_filter_for_query
from app.rag.retriever import QdrantRetriever, SearchFilter

from .conftest import FakeEmbeddingProvider


def _chunk(
    chunk_id: str,
    content: str,
    *,
    chunk_type: str = "general",
    source_name: str = "docs",
    entity: str | None = None,
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        content=content,
        metadata=ChunkMetadata(
            source_name=source_name,
            chunk_type=chunk_type,
            entity=entity,
        ),
    )


def test_tokenize_keeps_path_like_tokens():
    tokens = tokenize("POST /companies/{company}/subscriptions docker-compose")
    assert "subscriptions" in tokens
    assert "docker-compose" in tokens
    assert "companies" in tokens


def test_lexical_index_ranks_exact_endpoint_phrase():
    index = LexicalIndex()
    index.add(
        [
            _chunk("ex1", '{"piece": {"@type": "Piece"}}', chunk_type="example", source_name="example"),
            _chunk(
                "api1",
                "POST /companies/{company}/subscriptions creates a subscription webhook",
                chunk_type="api",
                source_name="ONE Record OpenAPI Specification",
            ),
            _chunk("doc1", "Subscriptions notify logistics partners of events", chunk_type="concept"),
        ]
    )
    hits = index.search("POST /companies subscriptions", top_k=2)
    assert hits[0].chunk_id == "api1"


def test_rrf_prefers_items_high_in_both_lists():
    a = _chunk("a", "a")
    b = _chunk("b", "b")
    c = _chunk("c", "c")
    fused = reciprocal_rank_fuse([a, b, c], [b, a, c], limit=3)
    assert fused[0].chunk_id == "a" or fused[0].chunk_id == "b"
    assert {x.chunk_id for x in fused} == {"a", "b", "c"}


def test_search_filter_excludes_examples_for_implementation():
    flt = search_filter_for_query(
        "How do I start NE:ONE locally with docker compose?",
        QueryType.implementation_question,
    )
    assert flt is not None
    assert "example" in flt.exclude_chunk_types
    assert not flt.allows(_chunk("e", "payload", chunk_type="example"))
    assert flt.allows(_chunk("d", "docker compose up", chunk_type="concept"))


def test_search_filter_allows_examples_when_requested():
    assert (
        search_filter_for_query(
            "Show me an example NE:ONE JSON payload",
            QueryType.implementation_question,
        )
        is None
    )


def test_hybrid_retriever_excludes_examples_and_finds_lexical_config():
    retriever = QdrantRetriever(
        Settings(
            qdrant_url=":memory:",
            qdrant_collection="hybrid_test",
            embedding_dim=FakeEmbeddingProvider.dim,
        ),
        FakeEmbeddingProvider(),
    )
    retriever.reset()
    retriever.upsert(
        [
            _chunk(
                "example-json",
                '{"@type":"Piece","handling":"bulk example noise"}',
                chunk_type="example",
                source_name="NE:ONE Example Payload",
            ),
            _chunk(
                "neone-docs",
                "Start NE:ONE locally with docker compose up -d and check keycloak",
                chunk_type="concept",
                source_name="NE:ONE documentation",
            ),
            _chunk(
                "openapi",
                "GET /subscriptions lists active subscription endpoints",
                chunk_type="api",
                source_name="ONE Record OpenAPI Specification",
            ),
        ]
    )

    impl_hits = retriever.search(
        "How do I start NE:ONE locally with docker compose?",
        top_k=3,
        search_filter=SearchFilter(exclude_chunk_types=("example",)),
    )
    assert impl_hits
    assert all(c.metadata.chunk_type != "example" for c in impl_hits)
    assert any(c.chunk_id == "neone-docs" for c in impl_hits)

    api_hits = retriever.search(
        "GET /subscriptions endpoint",
        top_k=3,
        search_filter=SearchFilter(chunk_types=("api", "concept", "general")),
    )
    assert api_hits[0].chunk_id == "openapi"
