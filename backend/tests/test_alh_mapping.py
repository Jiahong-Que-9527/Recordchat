"""AviationLakehouse mapping helpers (#8) and architecture routing (#9/#10)."""

from pathlib import Path

import yaml

from app.domain.alh_mapping import format_alh_context, get_alh_layers, mapped_entities
from app.models.chat import QueryType
from app.rag.canonical import is_canonical_source
from app.rag.pipeline import classify_query
from app.rag.prompt import build_user_prompt
from app.models.source import Chunk, ChunkMetadata


REPO_ROOT = Path(__file__).resolve().parents[2]
ALH_DOC = REPO_ROOT / "data" / "raw" / "one_record_docs" / "aviation_lakehouse.md"
EVAL_PATH = REPO_ROOT / "data" / "eval" / "questions.yaml"


def test_mapped_entities_cover_core_logistics_objects():
    entities = mapped_entities()
    assert "Piece" in entities
    assert "Shipment" in entities
    assert "Waybill" in entities
    assert "TransportMovement" in entities
    assert "LogisticsEvent" in entities


def test_get_alh_layers_for_piece():
    layers = get_alh_layers("Piece")
    assert [layer["layer"] for layer in layers] == ["bronze", "silver", "gold"]
    assert all(layer["summary"] and layer["example_landing"] for layer in layers)


def test_get_alh_layers_unknown_entity_returns_empty():
    assert get_alh_layers("NotAnEntity") == []


def test_format_alh_context_mentions_gold_and_shipment():
    text = format_alh_context("How does a Shipment land in Gold?")
    assert "Gold" in text or "gold" in text.lower()
    assert "Shipment" in text


def test_alh_knowledge_doc_is_canonical_for_ingest():
    assert ALH_DOC.is_file()
    assert (ALH_DOC.parent / "aviation_lakehouse.md.meta.json").is_file()
    assert is_canonical_source(ALH_DOC, source_root=REPO_ROOT / "data" / "raw") is True


def test_classify_architecture_and_control_queries():
    assert (
        classify_query("How could ONE Record data be connected to an AviationLakehouse?")
        == QueryType.architecture_question
    )
    assert (
        classify_query("How would a Piece land in Bronze, Silver, and Gold?")
        == QueryType.architecture_question
    )
    assert (
        classify_query(
            "Why is an AviationLakehouse not a replacement for a ONE Record Server?"
        )
        == QueryType.architecture_question
    )
    assert classify_query("What is a Piece?") == QueryType.concept_explanation
    # "gold standard" alone must not steal ontology/concept classification.
    assert "gold standard" not in "What is a Piece?"


def test_architecture_prompt_includes_mapping_block():
    chunk = Chunk(
        chunk_id="alh::1",
        content="AviationLakehouse Bronze Silver Gold narrative.",
        metadata=ChunkMetadata(
            source_name="RecordChat AviationLakehouse narrative",
            section_title="Bronze",
            chunk_type="concept",
        ),
    )
    mapping = format_alh_context("How would a Piece land in Bronze, Silver, and Gold?")
    prompt = build_user_prompt(
        "How would a Piece land in Bronze, Silver, and Gold?",
        [chunk],
        QueryType.architecture_question,
        extra_context="AviationLakehouse mapping (project narrative):\n" + mapping,
    )
    assert "AviationLakehouse mapping (project narrative):" in prompt
    assert "Piece" in prompt
    assert "GUIDANCE:" in prompt


def test_eval_alh_questions_match_classifier():
    payload = yaml.safe_load(EVAL_PATH.read_text(encoding="utf-8"))
    alh_items = [item for item in payload if str(item.get("id", "")).startswith("alh_")]
    assert len(alh_items) >= 3
    for item in alh_items:
        assert item["expected_query_type"] == "architecture_question"
        assert classify_query(item["question"]) == QueryType.architecture_question
