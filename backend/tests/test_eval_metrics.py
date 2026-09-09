from app.models.source import Chunk, ChunkMetadata
from app.rag.eval_metrics import (
    canonical_version_hit,
    entity_recall_at_k,
    mean_reciprocal_rank,
    source_family_hit,
)


def _chunk(entity=None, source_name="docs", version=None) -> Chunk:
    return Chunk(
        chunk_id=f"{source_name}::{entity or 'x'}",
        content="x",
        metadata=ChunkMetadata(
            source_name=source_name,
            entity=entity,
            version=version,
        ),
    )


def test_entity_recall_and_mrr():
    chunks = [
        _chunk(source_name="docs"),
        _chunk(entity="Piece", source_name="ONE Record Cargo Data Model Ontology"),
        _chunk(entity="Shipment", source_name="ONE Record Cargo Data Model Ontology"),
    ]
    assert entity_recall_at_k(chunks, ["Piece", "Shipment"], k=3) == 1.0
    assert entity_recall_at_k(chunks, ["Piece", "Waybill"], k=3) == 0.5
    assert mean_reciprocal_rank(chunks, ["Piece"]) == 0.5
    assert mean_reciprocal_rank(chunks, ["Waybill"]) == 0.0


def test_source_family_and_version_hit():
    chunks = [
        _chunk(source_name="NE:ONE docs", version="snapshot"),
        _chunk(
            entity="Piece",
            source_name="ONE Record Cargo Data Model Ontology",
            version="2025-07",
        ),
    ]
    assert source_family_hit(chunks, ["Ontology", "ONE Record"])
    assert not source_family_hit(chunks, ["OpenAPI"])
    assert canonical_version_hit(chunks, "2025-07")
    assert not canonical_version_hit(chunks, "2023-12")
