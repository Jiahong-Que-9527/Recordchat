"""v0.2.4 workflow orchestration (#32) + AUD-07 request log smoke."""

import json
from pathlib import Path

from app.connectors.base import ConnectorAvailability
from app.connectors.orchestration import run_synthetic_data_workflow
from app.connectors.recordforge import RecordForgeConnector
from app.core.config import Settings
from app.core.request_log import log_chat_request
from app.core.llm import LLMProvider
from app.models.chat import QueryType
from app.rag.pipeline import answer, classify_query


class _UnusedLLM(LLMProvider):
    def complete(self, *, system: str, user: str) -> str:
        raise AssertionError("synthetic workflow must not call the LLM")

    def complete_stream(self, *, system: str, user: str):
        raise AssertionError("synthetic workflow must not call the LLM")


def test_recordforge_unconfigured_returns_blocked_workflow():
    connector = RecordForgeConnector(Settings(recordforge_url="", recordforge_api_key=""))
    result = connector.execute_synthetic_generation(
        "Generate 5 synthetic shipments with pieces"
    )
    assert result.kind == "workflow_result"
    assert result.status == "blocked"
    assert result.connector.availability == ConnectorAvailability.unconfigured
    assert result.artifacts[0].content["count"] == 5
    assert result.artifacts[0].content["object_type"] == "Shipment"
    assert result.artifacts[0].content["options"]["with_pieces"] is True
    assert any(step.status == "skipped" for step in result.steps)


def test_recordforge_configured_returns_planned_execution_path():
    connector = RecordForgeConnector(
        Settings(
            recordforge_url="https://recordforge.example.com",
            recordforge_api_key="secret",
        )
    )
    result = run_synthetic_data_workflow(
        "Generate 3 pieces",
        connector=connector,
    )
    assert result.status == "planned"
    assert result.connector.availability == ConnectorAvailability.ready
    assert any(step.id == "execute" and step.status == "ready" for step in result.steps)
    request = next(a for a in result.artifacts if a.kind == "generation_request")
    assert request.content["endpoint"].endswith("/v1/generate")
    assert request.content["body"]["object_type"] == "Piece"
    assert request.content["body"]["count"] == 3


def test_answer_uses_structured_workflow_when_configured(monkeypatch):
    monkeypatch.setenv("RECORDFORGE_URL", "https://recordforge.example.com")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        resp = answer(
            "Generate 2 synthetic shipments with pieces",
            llm=_UnusedLLM(),
        )
        assert resp.query_type == QueryType.synthetic_data_generation
        assert resp.structured_output["status"] == "planned"
        assert resp.structured_output["connector"]["availability"] == "ready"
        assert any(
            art["kind"] == "generation_request"
            for art in resp.structured_output["artifacts"]
        )
    finally:
        monkeypatch.delenv("RECORDFORGE_URL", raising=False)
        get_settings.cache_clear()


def test_synthetic_intent_still_routed():
    assert (
        classify_query("Generate 5 synthetic shipments with pieces")
        == QueryType.synthetic_data_generation
    )


def test_request_log_writes_jsonl(tmp_path, monkeypatch):
    log_path = tmp_path / "requests.jsonl"
    monkeypatch.setenv("RECORDCHAT_REQUEST_LOG", str(log_path))
    log_chat_request(
        {
            "event": "chat",
            "query": "What is a Piece?",
            "query_type": "concept_explanation",
            "latency_ms": 12,
            "chunks": [{"rank": 1, "chunk_id": "piece::1"}],
        }
    )
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["query"] == "What is a Piece?"
    assert payload["chunks"][0]["chunk_id"] == "piece::1"
    assert "ts" in payload
