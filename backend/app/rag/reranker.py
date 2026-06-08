"""Reranker hook with ontology-aware entity boosting (ADR 0002).

Vector search produces a candidate pool; this module re-orders chunks so
entity-specific ontology definitions rank higher for concept/relationship
questions.
"""

from __future__ import annotations

from app.domain.one_record_schema import detect_entities
from app.domain.ontology_graph import get_ontology_graph
from app.models.source import Chunk

_ENTITY_MATCH_BOOST = 10.0
_RELATED_ENTITY_BOOST = 5.0
_METADATA_RELATED_BOOST = 2.5
_ONTOLOGY_CLASS_BOOST = 8.0
_ONTOLOGY_PROPERTY_BOOST = 12.0
_ONTOLOGY_ENTITY_CONTEXT_BOOST = 4.0


def _is_ontology_query(query: str) -> bool:
    q = query.lower()
    return any(
        marker in q
        for marker in (
            "ontology",
            "subclass",
            "superclass",
            "class is",
            "property",
            "properties",
            "domain",
            "range",
            "connect",
            "connected to",
        )
    )


def rerank(query: str, chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return chunks

    query_entities = detect_entities(query)
    if not query_entities:
        return chunks

    expanded: set[str] = set(query_entities)
    graph = get_ontology_graph()
    ontology_query = _is_ontology_query(query)
    if graph:
        for entity in query_entities:
            expanded.update(graph.get_related(entity))

    def score(index: int, chunk: Chunk) -> float:
        # Preserve vector rank as a baseline tie-breaker.
        value = float(len(chunks) - index)
        if ontology_query:
            if chunk.metadata.chunk_type == "property_definition":
                value += _ONTOLOGY_PROPERTY_BOOST
            elif chunk.metadata.chunk_type == "class_definition":
                value += _ONTOLOGY_CLASS_BOOST

        entity = chunk.metadata.entity
        if entity and entity in query_entities:
            value += _ENTITY_MATCH_BOOST
        elif entity and entity in expanded:
            value += _RELATED_ENTITY_BOOST

        for related in chunk.metadata.related_entities:
            if related in query_entities:
                value += _METADATA_RELATED_BOOST
            elif related in expanded:
                value += _METADATA_RELATED_BOOST / 2

        if ontology_query and chunk.metadata.related_entities:
            if any(related in query_entities for related in chunk.metadata.related_entities):
                value += _ONTOLOGY_ENTITY_CONTEXT_BOOST

        return value

    return [
        chunk
        for _, chunk in sorted(
            enumerate(chunks),
            key=lambda pair: score(pair[0], pair[1]),
            reverse=True,
        )
    ]
