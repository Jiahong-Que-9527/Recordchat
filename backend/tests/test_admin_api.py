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


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "enforced")
    monkeypatch.setenv("INTERNAL_AUTH_SECRET", SECRET)
    monkeypatch.setenv("RECORDCHAT_DB_PATH", str(tmp_path / "recordchat.db"))
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    get_settings.cache_clear()
    reset_db_state()
    reset_quota_state()
    return TestClient(app)


def _jwt(idp: str) -> dict[str, str]:
    token = sign_internal_jwt(sub=idp, email_hash="ab" * 32, secret=SECRET)
    return {"Authorization": f"Bearer {token}"}


def test_non_admin_gets_403(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/internal/auth/signup",
        json={"email": "user@example.com", "password": "correcthorse"},
    )
    idp = created.json()["user"]["idp_user_id"]
    resp = client.get("/internal/admin/users", headers=_jwt(idp))
    assert resp.status_code == 403
    assert resp.json()["error"] == "forbidden"


def test_admin_provision_revoke_and_plan(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    admin = client.post(
        "/internal/auth/signup",
        json={"email": "admin@example.com", "password": "correcthorse"},
    )
    assert admin.json()["user"]["role"] == "admin"
    admin_id = admin.json()["user"]["idp_user_id"]

    created = client.post(
        "/internal/admin/users",
        json={"email": "new@example.com", "plan": "trial"},
        headers=_jwt(admin_id),
    )
    assert created.status_code == 200
    assert created.json()["temporary_password"]
    idp = created.json()["user"]["idp_user_id"]
    assert created.json()["user"]["must_reset_password"] is True

    login = client.post(
        "/internal/auth/login",
        json={
            "email": "new@example.com",
            "password": created.json()["temporary_password"],
        },
    )
    assert login.status_code == 200
    assert login.json()["must_reset_password"] is True

    planned = client.post(
        f"/internal/admin/users/{idp}/plan",
        json={"plan": "user", "daily_quota": 80},
        headers=_jwt(admin_id),
    )
    assert planned.status_code == 200
    assert planned.json()["plan"] == "user"

    revoked = client.post(
        f"/internal/admin/users/{idp}/revoke",
        headers=_jwt(admin_id),
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    usage = client.get("/internal/admin/usage", headers=_jwt(admin_id))
    assert usage.status_code == 200
    assert "request_count" in usage.json()
