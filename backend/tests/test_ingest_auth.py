"""AUTH-04: ingest is not public when AUTH_MODE=enforced."""

from __future__ import annotations

import os

os.environ.setdefault("QDRANT_URL", ":memory:")
os.environ.setdefault("AUTH_MODE", "off")

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.quota import reset_quota_state
from app.db.sqlite import reset_db_state
from app.main import app
from app.models.chat import IngestResponse


SECRET = "n" * 32
TOKEN = "ingest-secret-token"


def _client(tmp_path, monkeypatch, **env: str) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", env.get("AUTH_MODE", "enforced"))
    monkeypatch.setenv("INTERNAL_AUTH_SECRET", SECRET)
    monkeypatch.setenv("RECORDCHAT_DB_PATH", str(tmp_path / "recordchat.db"))
    monkeypatch.setenv("INGEST_TOKEN", env.get("INGEST_TOKEN", TOKEN))
    monkeypatch.setenv("INGEST_ALLOW_RESET", env.get("INGEST_ALLOW_RESET", "true"))
    get_settings.cache_clear()
    reset_db_state()
    reset_quota_state()
    return TestClient(app)


def test_off_mode_keeps_public_ingest(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, AUTH_MODE="off")
    monkeypatch.setattr(
        "app.api.ingest.run_ingest",
        lambda **kwargs: IngestResponse(chunks_indexed=2),
    )
    resp = client.post("/ingest", json={"reset": False})
    assert resp.status_code == 200
    assert resp.json()["chunks_indexed"] == 2


def test_enforced_public_ingest_is_404(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "app.api.ingest.run_ingest",
        lambda **kwargs: IngestResponse(chunks_indexed=2),
    )
    resp = client.post("/ingest", json={})
    assert resp.status_code == 404
    assert resp.json()["error"] == "not_found"


def test_enforced_internal_ingest_requires_token(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "app.api.ingest.run_ingest",
        lambda **kwargs: IngestResponse(chunks_indexed=2),
    )
    missing = client.post("/internal/ingest", json={})
    assert missing.status_code == 401
    wrong = client.post(
        "/internal/ingest", json={}, headers={"X-Ingest-Token": "nope"}
    )
    assert wrong.status_code == 401
    ok = client.post(
        "/internal/ingest", json={}, headers={"X-Ingest-Token": TOKEN}
    )
    assert ok.status_code == 200
    assert ok.json()["chunks_indexed"] == 2


def test_ingest_allow_reset_false_forces_no_reset(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, INGEST_ALLOW_RESET="false")
    seen: dict = {}

    def fake_ingest(*, source_dir, reset):
        seen["reset"] = reset
        return IngestResponse(chunks_indexed=1)

    monkeypatch.setattr("app.api.ingest.run_ingest", fake_ingest)
    resp = client.post(
        "/internal/ingest",
        json={"reset": True},
        headers={"X-Ingest-Token": TOKEN},
    )
    assert resp.status_code == 200
    assert seen["reset"] is False
