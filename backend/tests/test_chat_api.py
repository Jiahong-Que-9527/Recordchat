from app.api.chat import chat_stream, stream_chat_events
from app.models.chat import ChatRequest


def test_chat_stream_emits_sse_events(monkeypatch):
    def fake_answer_stream(query: str):
        assert query == "stream please"
        yield {"event": "token", "data": {"text": "Hello"}}
        yield {"event": "metadata", "data": {"answer": "Hello", "sources": []}}

    monkeypatch.setattr("app.api.chat.answer_stream", fake_answer_stream)
    body = "".join(stream_chat_events("stream please"))
    resp = chat_stream(ChatRequest(message="stream please"))

    assert resp.media_type == "text/event-stream"
    assert "event: token" in body
    assert 'data: {"text": "Hello"}' in body
    assert "event: metadata" in body
    assert '"answer": "Hello"' in body
