"""AUTH-03: JWT identity, ensure upsert, quotas, trial clamps."""

from __future__ import annotations

import os

os.environ.setdefault("QDRANT_URL", ":memory:")
os.environ.setdefault("AUTH_MODE", "off")

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.internal_auth import sign_internal_jwt
from app.core.quota import check_and_begin, end_stream, reset_quota_state
from app.db.sqlite import get_user_by_idp, reset_db_state, upsert_user
from app.main import app
from app.models.chat import ChatResponse, QueryType, SyntheticMode


SECRET = "n" * 32


def _client(tmp_path, monkeypatch, **env: str) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", env.get("AUTH_MODE", "enforced"))
    monkeypatch.setenv("INTERNAL_AUTH_SECRET", env.get("INTERNAL_AUTH_SECRET", SECRET))
    monkeypatch.setenv("RECORDCHAT_DB_PATH", str(tmp_path / "recordchat.db"))
    monkeypatch.setenv("LLM_KILL_SWITCH", env.get("LLM_KILL_SWITCH", "false"))
    monkeypatch.setenv("CHAT_DAILY_LIMIT_TRIAL", env.get("CHAT_DAILY_LIMIT_TRIAL", "30"))
    monkeypatch.setenv("LLM_DAILY_BUDGET_USD", env.get("LLM_DAILY_BUDGET_USD", "15"))
    get_settings.cache_clear()
    reset_db_state()
    reset_quota_state()
    return TestClient(app)


def _token(sub: str = "user_abc", email_hash: str = "ab" * 32) -> str:
    return sign_internal_jwt(sub=sub, email_hash=email_hash, secret=SECRET)


def _auth(sub: str = "user_abc") -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(sub)}"}


def _stub_answer(monkeypatch, captured: dict | None = None):
    def fake_answer(message, model=None, history=None, synthetic_mode=None):
        if captured is not None:
            captured["model"] = model
            captured["synthetic_mode"] = synthetic_mode
            captured["message"] = message
        return ChatResponse(answer="ok", query_type=QueryType.general_question)

    monkeypatch.setattr("app.api.chat.answer", fake_answer)


def test_off_mode_chat_without_jwt(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, AUTH_MODE="off")
    _stub_answer(monkeypatch)
    resp = client.post("/chat", json={"message": "What is a Piece?"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "ok"


def test_enforced_without_jwt_is_401(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "unauthorized"


def test_bad_signature_is_401(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    other = sign_internal_jwt(sub="user_abc", email_hash="x", secret="z" * 32)
    resp = client.post(
        "/chat",
        json={"message": "hi"},
        headers={"Authorization": f"Bearer {other}"},
    )
    assert resp.status_code == 401


def test_valid_jwt_without_ensure_is_401(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    _stub_answer(monkeypatch)
    resp = client.post("/chat", json={"message": "hi"}, headers=_auth())
    assert resp.status_code == 401


def test_ensure_then_chat(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    _stub_answer(monkeypatch)
    ensured = client.post(
        "/internal/users/ensure",
        json={"email_prefix": "ab***@example.com"},
        headers=_auth(),
    )
    assert ensured.status_code == 200
    body = ensured.json()
    assert body["plan"] == "trial"
    assert body["role"] == "user"
    chat = client.post("/chat", json={"message": "hi"}, headers=_auth())
    assert chat.status_code == 200
    assert chat.json()["answer"] == "ok"
    me = client.get("/internal/users/me", headers=_auth())
    assert me.json()["used_today"] == 1


def test_revoked_user_is_401(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    _stub_answer(monkeypatch)
    client.post("/internal/users/ensure", json={}, headers=_auth())
    from app.db.sqlite import set_status

    set_status(idp_user_id="user_abc", status="revoked")
    resp = client.post("/chat", json={"message": "hi"}, headers=_auth())
    assert resp.status_code == 401
    assert resp.json()["error"] == "revoked"


def test_payload_too_large(tmp_path, monkeypatch):
    monkeypatch.setenv("CHAT_MAX_MESSAGE_CHARS", "8")
    client = _client(tmp_path, monkeypatch)
    client.post("/internal/users/ensure", json={}, headers=_auth())
    resp = client.post("/chat", json={"message": "123456789"}, headers=_auth())
    assert resp.status_code == 400
    assert resp.json()["error"] == "payload_too_large"


def test_daily_quota_429(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, CHAT_DAILY_LIMIT_TRIAL="1")
    _stub_answer(monkeypatch)
    client.post("/internal/users/ensure", json={}, headers=_auth())
    assert client.post("/chat", json={"message": "one"}, headers=_auth()).status_code == 200
    second = client.post("/chat", json={"message": "two"}, headers=_auth())
    assert second.status_code == 429
    assert second.json()["error"] == "rate_limited"
    assert "Retry-After" in second.headers


def test_concurrent_stream_429(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/internal/users/ensure", json={}, headers=_auth())
    user = get_user_by_idp("user_abc")
    assert user is not None
    check_and_begin(user, "first")
    try:
        from fastapi import HTTPException

        try:
            check_and_begin(user, "second")
            raise AssertionError("expected 429")
        except HTTPException as exc:
            assert exc.status_code == 429
    finally:
        end_stream(user.idp_user_id)


def test_trial_clamps_model_and_recordforge(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    captured: dict = {}
    _stub_answer(monkeypatch, captured)
    client.post("/internal/users/ensure", json={}, headers=_auth())
    resp = client.post(
        "/chat",
        json={
            "message": "hi",
            "model": "deepseek-v4-pro",
            "synthetic_mode": "recordforge",
        },
        headers=_auth(),
    )
    assert resp.status_code == 200
    assert captured["model"] == "deepseek-v4-flash"
    assert captured["synthetic_mode"] == SyntheticMode.local


def test_kill_switch_503(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, LLM_KILL_SWITCH="true")
    client.post("/internal/users/ensure", json={}, headers=_auth())
    resp = client.post("/chat", json={"message": "hi"}, headers=_auth())
    assert resp.status_code == 503
    assert resp.json()["error"] == "unavailable"


def test_ensure_does_not_reset_plan(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/internal/users/ensure", json={}, headers=_auth())
    upsert_user(idp_user_id="user_abc", email_hash="ab" * 32, plan="user")
    again = client.post("/internal/users/ensure", json={}, headers=_auth())
    assert again.json()["plan"] == "user"
