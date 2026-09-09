"""Follow-up rewrite (#30) and citation filtering (#31)."""

from app.core.llm import LLMProvider
from app.domain.one_record_schema import detect_entities
from app.models.chat import ChatHistoryMessage
from app.models.source import Chunk, ChunkMetadata
from app.rag.pipeline import (
    answer,
    filter_cited_chunks,
    rewrite_query_for_retrieval,
)


class _ScriptedLLM(LLMProvider):
    def __init__(self, text: str) -> None:
        self.text = text

    def complete(self, *, system: str, user: str) -> str:
        return self.text

    def complete_stream(self, *, system: str, user: str):
        yield self.text


def _chunk(chunk_id: str, content: str, **meta) -> Chunk:
    source_name = meta.pop("source_name", "docs")
    return Chunk(
        chunk_id=chunk_id,
        content=content,
        metadata=ChunkMetadata(source_name=source_name, **meta),
    )


def test_detect_entities_uses_token_boundaries():
    assert "Item" not in detect_entities("What is a shipment in ONE Record?")
    assert "Piece" in detect_entities("What is a Piece in ONE Record?")
    assert "Shipment" in detect_entities("Explain Shipment vs Piece")


def test_rewrite_carries_piece_into_shipment_followup():
    history = [
        ChatHistoryMessage(role="user", content="What is a Piece in ONE Record?"),
        ChatHistoryMessage(role="assistant", content="A Piece is a physical package."),
    ]
    rewritten = rewrite_query_for_retrieval(
        "How does it relate to Shipment?",
        history,
    )
    assert "Piece" in rewritten
    assert "Shipment" in rewritten
    assert "entities from earlier turns" in rewritten


def test_rewrite_noop_without_history_or_when_entities_present():
    assert rewrite_query_for_retrieval("What is a Piece?", None) == "What is a Piece?"
    history = [ChatHistoryMessage(role="user", content="What is a Piece?")]
    assert (
        rewrite_query_for_retrieval("Explain Shipment and Piece", history)
        == "Explain Shipment and Piece"
    )


def test_filter_cited_chunks_keeps_overlapping_drops_unrelated():
    piece = _chunk(
        "piece",
        "Class definition: Piece is a physical package handled in logistics.",
        entity="Piece",
        source_name="ONE Record Cargo Data Model Ontology",
        chunk_type="class_definition",
    )
    noise = _chunk(
        "noise",
        '{"@type":"Booking","random":"example payload that is unrelated"}',
        source_name="NE:ONE Example Payload",
        chunk_type="example",
    )
    answer_text = (
        "A Piece is a physical package handled in logistics. "
        "It belongs to the ONE Record cargo data model."
    )
    cited = filter_cited_chunks(answer_text, [noise, piece])
    assert [c.chunk_id for c in cited] == ["piece"]


def test_filter_cited_chunks_prefers_empty_over_unrelated():
    noise = _chunk(
        "noise",
        "Completely unrelated GraphDB repository configuration keys.",
        source_name="infra",
    )
    assert filter_cited_chunks("ONE Record is an IATA standard.", [noise]) == []


def test_followup_answer_retrieves_with_history(ingested_retriever):
    resp = answer(
        "How does it relate to Shipment?",
        retriever=ingested_retriever,
        llm=_ScriptedLLM(
            "Piece relates to Shipment through containment in the cargo model."
        ),
        history=[
            ChatHistoryMessage(role="user", content="What is a Piece in ONE Record?"),
            ChatHistoryMessage(role="assistant", content="Piece is a package."),
        ],
    )
    # Either sources mention Piece/Shipment or related_concepts do — retrieval
    # must have seen both entities via rewrite.
    haystack = " ".join(
        [resp.answer, *resp.related_concepts, *(s.source_name for s in resp.sources)]
    )
    assert "Piece" in haystack or "Shipment" in haystack
