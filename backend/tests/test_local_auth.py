"""Self-hosted email/password auth (no Clerk)."""

from __future__ import annotations

import os

os.environ.setdefault("QDRANT_URL", ":memory:")
os.environ.setdefault("AUTH_MODE", "off")

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.internal_auth import sign_internal_jwt
from app.core.quota import reset_quota_state
from app.db.sqlite import reset_db_state
from app.main import app

SECRET = "n" * 32


def _client(tmp_path, monkeypatch, **env: str) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", env.get("AUTH_MODE", "enforced"))
    monkeypatch.setenv("INTERNAL_AUTH_SECRET", SECRET)
    monkeypatch.setenv("RECORDCHAT_DB_PATH", str(tmp_path / "recordchat.db"))
    monkeypatch.setenv("ADMIN_EMAILS", env.get("ADMIN_EMAILS", "admin@example.com"))
    get_settings.cache_clear()
    reset_db_state()
    reset_quota_state()
    return TestClient(app)


def test_signup_login_and_session(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/internal/auth/signup",
        json={"email": "a@example.com", "password": "correcthorse"},
    )
    assert created.status_code == 200
    token = created.json()["session_token"]
    looked = client.post("/internal/auth/session", json={"session_token": token})
    assert looked.status_code == 200
    assert looked.json()["user"]["plan"] == "trial"
    login = client.post(
        "/internal/auth/login",
        json={"email": "a@example.com", "password": "correcthorse"},
    )
    assert login.status_code == 200


def test_wrong_password(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post(
        "/internal/auth/signup",
        json={"email": "a@example.com", "password": "correcthorse"},
    )
    bad = client.post(
        "/internal/auth/login",
        json={"email": "a@example.com", "password": "wrong-wrong"},
    )
    assert bad.status_code == 401


def test_short_password_rejected(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    resp = client.post(
        "/internal/auth/signup",
        json={"email": "a@example.com", "password": "short"},
    )
    assert resp.status_code == 400


def test_admin_email_gets_role(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, ADMIN_EMAILS="ops@example.com")
    created = client.post(
        "/internal/auth/signup",
        json={"email": "ops@example.com", "password": "correcthorse"},
    )
    assert created.json()["user"]["role"] == "admin"


def test_change_password(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/internal/auth/signup",
        json={"email": "a@example.com", "password": "correcthorse"},
    )
    token = created.json()["session_token"]
    changed = client.post(
        "/internal/auth/change-password",
        json={"current_password": "correcthorse", "new_password": "newpassword1"},
        headers={"X-Session-Token": token},
    )
    assert changed.status_code == 200
    assert (
        client.post(
            "/internal/auth/login",
            json={"email": "a@example.com", "password": "correcthorse"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/internal/auth/login",
            json={"email": "a@example.com", "password": "newpassword1"},
        ).status_code
        == 200
    )


def test_jwt_chat_after_signup(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    from app.models.chat import ChatResponse, QueryType

    monkeypatch.setattr(
        "app.api.chat.answer",
        lambda *a, **k: ChatResponse(answer="ok", query_type=QueryType.general_question),
    )
    created = client.post(
        "/internal/auth/signup",
        json={"email": "a@example.com", "password": "correcthorse"},
    )
    user_id = created.json()["user"]["idp_user_id"]
    jwt = sign_internal_jwt(sub=user_id, email_hash="ab" * 32, secret=SECRET)
    chat = client.post(
        "/chat",
        json={"message": "hi"},
        headers={"Authorization": f"Bearer {jwt}"},
    )
    assert chat.status_code == 200
