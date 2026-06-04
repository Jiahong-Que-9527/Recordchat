import json

from app.core.llm import LocalLLMProvider
from app.models.chat import QueryType
from app.rag.pipeline import answer, classify_query


def test_classify_query():
    assert classify_query("Generate a JSON-LD example for a Piece") == QueryType.jsonld_generation
    assert classify_query("What is the difference between Shipment and Piece") == QueryType.relationship_question
    assert classify_query("How does the ONE Record API work") == QueryType.api_question
    assert classify_query("What is a LogisticsObject") == QueryType.concept_explanation


def test_chat_returns_grounded_answer_with_sources(ingested_retriever):
    resp = answer("What is a Piece in ONE Record?", retriever=ingested_retriever, llm=LocalLLMProvider())
    assert resp.answer.strip()
    assert len(resp.sources) > 0
    assert resp.query_type == QueryType.concept_explanation


def test_jsonld_generation_produces_valid_jsonld(ingested_retriever):
    resp = answer("Generate a JSON-LD example for a Piece", retriever=ingested_retriever, llm=LocalLLMProvider())
    assert resp.query_type == QueryType.jsonld_generation
    assert resp.structured_output is not None
    assert resp.structured_output["@type"] == "Piece"
    # must be JSON-serializable / valid
    json.dumps(resp.structured_output)


def test_relationship_question_enriches_related_concepts(ingested_retriever):
    resp = answer("Explain the relationship between Shipment and Piece", retriever=ingested_retriever, llm=LocalLLMProvider())
    assert "Piece" in resp.related_concepts or "Shipment" in resp.related_concepts
