from app.api.health import health, list_models
from app.core.llm import ALLOWED_CHAT_MODELS


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


def test_list_models_matches_backend_allowlist():
    body = list_models().model_dump()
    assert set(body["models"]) == ALLOWED_CHAT_MODELS
    assert body["default"] in ALLOWED_CHAT_MODELS
    assert body["models"] == sorted(body["models"])
