"""Reranker hook with ontology-aware entity boosting (ADR 0002).

Vector search produces a candidate pool; this module lightly re-orders chunks so
entity-specific ontology definitions can rise a few places for concept /
relationship questions — without letting boosts override vector similarity.

Score model (AUD-03):
  score = (pool_size - index) * RANK_SCALE + boost
where RANK_SCALE is larger than any single boost, so a chunk can move only a
limited number of positions. Cumulative boosts stay below ~2.5 * RANK_SCALE,
so a bottom-of-pool false positive cannot leap to rank 1.
"""

from __future__ import annotations

from app.domain.one_record_schema import detect_entities
from app.domain.ontology_graph import get_ontology_graph
from app.models.source import Chunk

# Rank gap between adjacent vector positions. Boosts must stay well below
# several multiples of this value so vector order stays dominant.
_RANK_SCALE = 10.0

# Additive boosts. Entity match is slightly above one rank step so a matching
# chunk one slot behind the vector leader can swap up; stacked signals stay
# well below several rank steps so a distant false positive cannot leap to #1.
_ENTITY_MATCH_BOOST = 11.0
_RELATED_ENTITY_BOOST = 3.0
_METADATA_RELATED_BOOST = 1.5
_ONTOLOGY_CLASS_BOOST = 4.0
_ONTOLOGY_PROPERTY_BOOST = 8.0
_ONTOLOGY_ENTITY_CONTEXT_BOOST = 2.0


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
        # Vector rank dominates; boosts only nudge nearby candidates.
        value = float(len(chunks) - index) * _RANK_SCALE
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
