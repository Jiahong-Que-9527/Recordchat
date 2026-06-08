from app.api.health import health


def test_health():
    body = health().model_dump()
    assert body["status"] == "ok"
    assert body["service"] == "recordchat-backend"
    assert body["llm_provider"]
    assert body["llm_model"]
    assert isinstance(body["llm_api_key_configured"], bool)
    assert isinstance(body["embedding_api_key_configured"], bool)
    assert body["qdrant_mode"] in {"in_memory", "remote"}
    assert body["qdrant_collection"]
