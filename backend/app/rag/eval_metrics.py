"""Gold retrieval metrics for evaluate_rag.py (#28)."""

from __future__ import annotations

from app.models.source import Chunk

DEFAULT_TOP_K = 5


def _family_match(source_name: str, families: list[str]) -> bool:
    low = source_name.lower()
    return any(family.lower() in low for family in families)


def entity_recall_at_k(
    chunks: list[Chunk],
    expected_entities: list[str],
    k: int = DEFAULT_TOP_K,
) -> float:
    """Fraction of expected entities present in top-k chunk.entity metadata."""
    if not expected_entities:
        return 1.0
    found = {chunk.metadata.entity for chunk in chunks[:k] if chunk.metadata.entity}
    hits = sum(1 for entity in expected_entities if entity in found)
    return hits / len(expected_entities)


def mean_reciprocal_rank(chunks: list[Chunk], expected_entities: list[str]) -> float:
    """MRR against the first chunk whose entity is in expected_entities."""
    if not expected_entities:
        return 1.0
    expected = set(expected_entities)
    for index, chunk in enumerate(chunks, start=1):
        if chunk.metadata.entity in expected:
            return 1.0 / index
    return 0.0


def source_family_hit(
    chunks: list[Chunk],
    families: list[str],
    k: int = DEFAULT_TOP_K,
) -> bool:
    if not families:
        return True
    return any(_family_match(chunk.metadata.source_name, families) for chunk in chunks[:k])


def canonical_version_hit(
    chunks: list[Chunk],
    version: str | None,
    k: int = DEFAULT_TOP_K,
) -> bool:
    if not version:
        return True
    return any(chunk.metadata.version == version for chunk in chunks[:k])
