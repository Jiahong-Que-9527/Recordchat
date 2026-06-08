import json

from app.core.llm import LLMProvider
from app.models.chat import QueryType
from app.rag.pipeline import answer, answer_stream, classify_query


class FakeLLMProvider(LLMProvider):
    def complete(self, *, system: str, user: str) -> str:
        return f"Stub answer based on prompt: {user[:200]}"

    def complete_stream(self, *, system: str, user: str):
        yield f"Stub answer based on prompt: {user[:80]}"


class EmptyLLMProvider(LLMProvider):
    def complete(self, *, system: str, user: str) -> str:
        return "   "

    def complete_stream(self, *, system: str, user: str):
        if False:
            yield ""


class FakeStreamingLLMProvider(LLMProvider):
    def complete(self, *, system: str, user: str) -> str:
        return "Streamed answer"

    def complete_stream(self, *, system: str, user: str):
        yield "Streamed "
        yield "answer"


def test_classify_query():
    assert classify_query("Generate a JSON-LD example for a Piece") == QueryType.jsonld_generation
    assert classify_query("给我生成一个 Piece 的 JSON-LD 示例") == QueryType.jsonld_generation
    assert classify_query("What is the difference between Shipment and Piece") == QueryType.relationship_question
    assert classify_query("What is a Waybill and how does it relate to Shipment?") == QueryType.relationship_question
    assert classify_query("Waybill 和 Shipment 的关系是什么？") == QueryType.relationship_question
    assert classify_query("How does the ONE Record API work") == QueryType.api_question
    assert classify_query("怎么创建 ONE Record 订阅接口？") == QueryType.api_question
    assert classify_query("Which class is Shipment a subclass of?") == QueryType.ontology_question
    assert classify_query("Shipment 和 Piece 在本体里通过什么属性关联？") == QueryType.ontology_question
    assert classify_query("How do I start NE:ONE locally with docker compose") == QueryType.implementation_question
    assert classify_query("怎么在本地用 docker compose 启动 NE:ONE？") == QueryType.implementation_question
    assert classify_query("What should I check when an NE:ONE API request fails") == QueryType.implementation_question
    assert classify_query("What is a LogisticsObject") == QueryType.concept_explanation
    assert classify_query("ONE Record 里的 Piece 是什么？") == QueryType.concept_explanation


def test_chat_returns_grounded_answer_with_sources(ingested_retriever):
    resp = answer("What is a Piece in ONE Record?", retriever=ingested_retriever, llm=FakeLLMProvider())
    assert resp.answer.strip()
    assert len(resp.sources) > 0
    assert resp.query_type == QueryType.concept_explanation


def test_jsonld_generation_produces_valid_jsonld(ingested_retriever):
    resp = answer("Generate a JSON-LD example for a Piece", retriever=ingested_retriever, llm=FakeLLMProvider())
    assert resp.query_type == QueryType.jsonld_generation
    assert resp.structured_output is not None
    assert resp.structured_output["@type"] == "Piece"
    # must be JSON-serializable / valid
    json.dumps(resp.structured_output)


def test_relationship_question_enriches_related_concepts(ingested_retriever):
    resp = answer("Explain the relationship between Shipment and Piece", retriever=ingested_retriever, llm=FakeLLMProvider())
    assert "Piece" in resp.related_concepts or "Shipment" in resp.related_concepts


def test_empty_llm_answer_falls_back_to_grounded_text(ingested_retriever):
    resp = answer("What is a Piece in ONE Record?", retriever=ingested_retriever, llm=EmptyLLMProvider())
    assert resp.answer.strip()
    assert "Grounded fallback answer" in resp.answer
    assert resp.sources


def test_answer_stream_emits_tokens_then_metadata(ingested_retriever):
    events = list(
        answer_stream(
            "What is a Piece in ONE Record?",
            retriever=ingested_retriever,
            llm=FakeStreamingLLMProvider(),
        )
    )
    assert [event["event"] for event in events[:-1]] == ["token", "token"]
    assert events[-1]["event"] == "metadata"
    assert events[-1]["data"]["answer"] == "Streamed answer"
    assert events[-1]["data"]["sources"]
