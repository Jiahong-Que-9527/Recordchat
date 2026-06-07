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


def rerank(query: str, chunks: list[Chunk]) -> list[Chunk]:
    if not chunks:
        return chunks

    query_entities = detect_entities(query)
    if not query_entities:
        return chunks

    expanded: set[str] = set(query_entities)
    graph = get_ontology_graph()
    if graph:
        for entity in query_entities:
            expanded.update(graph.get_related(entity))

    def score(index: int, chunk: Chunk) -> float:
        # Preserve vector rank as a baseline tie-breaker.
        value = float(len(chunks) - index)
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

        return value

    return [
        chunk
        for _, chunk in sorted(
            enumerate(chunks),
            key=lambda pair: score(pair[0], pair[1]),
            reverse=True,
        )
    ]
