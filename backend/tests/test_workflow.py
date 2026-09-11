"""v0.2.4/v0.2.5 workflow orchestration + RecordForge HTTP (#13) + AUD-07."""

import json
from pathlib import Path

import httpx

from app.connectors.base import ConnectorAvailability
from app.connectors.orchestration import run_synthetic_data_workflow
from app.connectors.recordforge import RecordForgeConnector
from app.core.config import Settings
from app.core.request_log import log_chat_request
from app.core.llm import LLMProvider
from app.models.chat import QueryType, SyntheticMode
from app.rag.pipeline import answer, classify_query


class _UnusedLLM(LLMProvider):
    def complete(self, *, system: str, user: str) -> str:
        raise AssertionError("synthetic workflow must not call the LLM")

    def complete_stream(self, *, system: str, user: str):
        raise AssertionError("synthetic workflow must not call the LLM")


def _mock_transport(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


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


def test_recordforge_ready_http_completes_with_objects():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path.endswith("/v1/generate")
        body = json.loads(request.content.decode("utf-8"))
        assert body["object_type"] == "Piece"
        assert body["count"] == 3
        assert request.headers.get("Authorization") == "Bearer secret"
        return httpx.Response(
            200,
            json={
                "objects": [
                    {"@type": "Piece", "@id": "https://example.com/piece/1"},
                    {"@type": "Piece", "@id": "https://example.com/piece/2"},
                    {"@type": "Piece", "@id": "https://example.com/piece/3"},
                ]
            },
        )

    connector = RecordForgeConnector(
        Settings(
            recordforge_url="https://recordforge.example.com",
            recordforge_api_key="secret",
        ),
        http_client=_mock_transport(handler),
    )
    result = run_synthetic_data_workflow(
        "Generate 3 pieces",
        connector=connector,
    )
    assert result.status == "completed"
    assert result.connector.availability == ConnectorAvailability.ready
    assert any(step.id == "execute" and step.status == "completed" for step in result.steps)
    request = next(a for a in result.artifacts if a.kind == "generation_request")
    assert request.content["endpoint"].endswith("/v1/generate")
    assert request.content["body"]["object_type"] == "Piece"
    objects = next(a for a in result.artifacts if a.kind == "generated_objects")
    assert len(objects.content) == 3


def test_recordforge_unavailable_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    connector = RecordForgeConnector(
        Settings(recordforge_url="https://recordforge.example.com"),
        http_client=_mock_transport(handler),
    )
    result = connector.execute_synthetic_generation("Generate 2 synthetic shipments")
    assert result.status == "failed"
    assert result.connector.availability == ConnectorAvailability.unavailable
    assert any(step.id == "execute" and step.status == "failed" for step in result.steps)
    assert "503" in (result.detail or "")


def test_recordforge_unavailable_on_transport_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    connector = RecordForgeConnector(
        Settings(recordforge_url="https://recordforge.example.com"),
        http_client=_mock_transport(handler),
    )
    result = connector.execute_synthetic_generation("Generate 1 shipment")
    assert result.status == "failed"
    assert result.connector.availability == ConnectorAvailability.unavailable
    assert "failed" in (result.detail or "").lower() or "refused" in (result.detail or "").lower()


def test_answer_uses_structured_workflow_when_configured(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"objects": [{"@type": "Shipment", "@id": "https://example.com/s/1"}]},
        )

    monkeypatch.setenv("RECORDFORGE_URL", "https://recordforge.example.com")
    from app.core.config import get_settings
    from app.connectors import orchestration

    get_settings.cache_clear()
    try:
        settings = get_settings()
        connector = RecordForgeConnector(settings, http_client=_mock_transport(handler))
        monkeypatch.setattr(
            orchestration,
            "get_recordforge_connector",
            lambda settings=None: connector,
        )
        resp = answer(
            "Generate 2 synthetic shipments with pieces",
            llm=_UnusedLLM(),
        )
        assert resp.query_type == QueryType.synthetic_data_generation
        assert resp.structured_output["status"] == "completed"
        assert resp.structured_output["connector"]["availability"] == "ready"
        assert any(
            art["kind"] == "generated_objects"
            for art in resp.structured_output["artifacts"]
        )
    finally:
        monkeypatch.delenv("RECORDFORGE_URL", raising=False)
        get_settings.cache_clear()


def test_answer_unconfigured_stays_blocked(monkeypatch):
    monkeypatch.delenv("RECORDFORGE_URL", raising=False)
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        resp = answer(
            "Generate 5 synthetic shipments with pieces",
            llm=_UnusedLLM(),
        )
        assert resp.query_type == QueryType.synthetic_data_generation
        assert resp.structured_output["kind"] == "workflow_result"
        assert resp.structured_output["status"] == "blocked"
        assert resp.structured_output["connector"]["availability"] == "unconfigured"
    finally:
        get_settings.cache_clear()


def test_answer_local_synthetic_mode_returns_jsonld_graph():
    resp = answer(
        "Generate 5 synthetic shipments with pieces",
        llm=_UnusedLLM(),
        synthetic_mode=SyntheticMode.local,
    )
    assert resp.query_type == QueryType.synthetic_data_generation
    assert resp.structured_output is not None
    assert resp.structured_output.get("kind") != "workflow_result"
    assert "@graph" in resp.structured_output
    graph = resp.structured_output["@graph"]
    assert len(graph) == 10  # 5 shipments + 5 linked pieces
    assert any(obj.get("@type") == "Shipment" for obj in graph)
    assert any(obj.get("@type") == "Piece" for obj in graph)
    assert "locally" in resp.answer.lower() or "template" in resp.answer.lower()
    assert resp.sources == []


def test_answer_local_synthetic_single_object():
    resp = answer(
        "Generate 1 piece",
        llm=_UnusedLLM(),
        synthetic_mode=SyntheticMode.local,
    )
    assert resp.structured_output is not None
    assert resp.structured_output.get("@type") == "Piece"
    assert "@graph" not in resp.structured_output


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


def test_request_log_relative_path_resolves_to_logs_dir():
    from app.core.request_log import _resolve_log_path

    path = _resolve_log_path("data/logs/requests.jsonl")
    assert path.name == "requests.jsonl"
    assert path.parts[-2] == "logs"
