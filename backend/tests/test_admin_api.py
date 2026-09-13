"""AUTH-04: admin list / provision / revoke / plan."""

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
    monkeypatch.setenv("AUTH_MODE", "enforced")
    monkeypatch.setenv("INTERNAL_AUTH_SECRET", SECRET)
    monkeypatch.setenv("RECORDCHAT_DB_PATH", str(tmp_path / "recordchat.db"))
    monkeypatch.setenv("ADMIN_IDP_USER_IDS", env.get("ADMIN_IDP_USER_IDS", "user_admin"))
    get_settings.cache_clear()
    reset_db_state()
    reset_quota_state()
    return TestClient(app)


def _auth(sub: str) -> dict[str, str]:
    token = sign_internal_jwt(sub=sub, email_hash="ab" * 32, secret=SECRET)
    return {"Authorization": f"Bearer {token}"}


def test_non_admin_gets_403(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    client.post("/internal/users/ensure", json={}, headers=_auth("user_abc"))
    resp = client.get("/internal/admin/users", headers=_auth("user_abc"))
    assert resp.status_code == 403
    assert resp.json()["error"] == "forbidden"


def test_admin_provision_revoke_and_plan(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    ensured = client.post(
        "/internal/users/ensure", json={}, headers=_auth("user_admin")
    )
    assert ensured.status_code == 200
    assert ensured.json()["role"] == "admin"

    created = client.post(
        "/internal/admin/users",
        json={
            "idp_user_id": "user_new",
            "email_hash": "cd" * 32,
            "email_prefix": "cd***@example.com",
            "plan": "trial",
        },
        headers=_auth("user_admin"),
    )
    assert created.status_code == 200
    assert created.json()["plan"] == "trial"

    listed = client.get("/internal/admin/users", headers=_auth("user_admin"))
    ids = {row["idp_user_id"] for row in listed.json()}
    assert "user_new" in ids

    planned = client.post(
        "/internal/admin/users/user_new/plan",
        json={"plan": "user", "daily_quota": 80},
        headers=_auth("user_admin"),
    )
    assert planned.status_code == 200
    assert planned.json()["plan"] == "user"
    assert planned.json()["daily_quota"] == 80

    revoked = client.post(
        "/internal/admin/users/user_new/revoke",
        headers=_auth("user_admin"),
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    usage = client.get("/internal/admin/usage", headers=_auth("user_admin"))
    assert usage.status_code == 200
    assert "request_count" in usage.json()
    assert "estimated_usd" in usage.json()
