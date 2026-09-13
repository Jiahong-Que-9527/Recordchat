"""SQLite helpers for trial users, daily usage, and audit events."""

from __future__ import annotations

import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings

_lock = threading.Lock()
_initialized: set[str] = set()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  idp_user_id   TEXT UNIQUE NOT NULL,
  email_hash    TEXT NOT NULL,
  email_prefix  TEXT NOT NULL DEFAULT '',
  role          TEXT NOT NULL DEFAULT 'user',
  plan          TEXT NOT NULL DEFAULT 'trial',
  status        TEXT NOT NULL DEFAULT 'active',
  daily_quota   INTEGER,
  created_at    TEXT NOT NULL,
  revoked_at    TEXT
);

CREATE TABLE IF NOT EXISTS usage_daily (
  user_id                 TEXT NOT NULL,
  day                     TEXT NOT NULL,
  request_count           INTEGER NOT NULL DEFAULT 0,
  prompt_tokens_est       INTEGER NOT NULL DEFAULT 0,
  completion_tokens_est   INTEGER NOT NULL DEFAULT 0,
  estimated_usd           REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);

CREATE TABLE IF NOT EXISTS audit_events (
  id              TEXT PRIMARY KEY,
  ts              TEXT NOT NULL,
  actor_user_id   TEXT,
  action          TEXT NOT NULL,
  ip_hash         TEXT,
  request_id      TEXT,
  metadata_json   TEXT
);
"""


@dataclass(frozen=True)
class LocalUser:
    id: str
    idp_user_id: str
    email_hash: str
    email_prefix: str
    role: str
    plan: str
    status: str
    daily_quota: int | None
    created_at: str
    revoked_at: str | None

    def effective_daily_quota(self, trial_limit: int, user_limit: int) -> int:
        if self.daily_quota is not None:
            return self.daily_quota
        return trial_limit if self.plan == "trial" else user_limit


def utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _db_path() -> Path:
    settings = get_settings()
    path = Path(settings.recordchat_db_path).expanduser()
    if not path.is_absolute():
        repo_root = Path(__file__).resolve().parents[3]
        docker_root = Path("/app")
        if (docker_root / "app" / "db" / "sqlite.py").is_file():
            path = docker_root / path
        else:
            path = repo_root / path
    return path


def connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.Connection(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    key = str(path)
    with _lock:
        if key not in _initialized:
            conn.executescript(_SCHEMA)
            conn.commit()
            _initialized.add(key)
    return conn


def reset_db_state() -> None:
    """Test helper: forget which files were initialized."""
    with _lock:
        _initialized.clear()


def _row_to_user(row: sqlite3.Row) -> LocalUser:
    return LocalUser(
        id=row["id"],
        idp_user_id=row["idp_user_id"],
        email_hash=row["email_hash"],
        email_prefix=row["email_prefix"] or "",
        role=row["role"],
        plan=row["plan"],
        status=row["status"],
        daily_quota=row["daily_quota"],
        created_at=row["created_at"],
        revoked_at=row["revoked_at"],
    )


def get_user_by_idp(idp_user_id: str) -> LocalUser | None:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE idp_user_id = ?", (idp_user_id,)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def upsert_user(
    *,
    idp_user_id: str,
    email_hash: str,
    email_prefix: str = "",
    plan: str | None = None,
    role: str | None = None,
) -> LocalUser:
    settings = get_settings()
    admin_ids = {
        item.strip()
        for item in settings.admin_idp_user_ids.split(",")
        if item.strip()
    }
    now = utc_now()
    conn = connect()
    try:
        existing = conn.execute(
            "SELECT * FROM users WHERE idp_user_id = ?", (idp_user_id,)
        ).fetchone()
        if existing is None:
            user_id = str(uuid.uuid4())
            resolved_role = role or ("admin" if idp_user_id in admin_ids else "user")
            resolved_plan = plan or "trial"
            conn.execute(
                """
                INSERT INTO users (
                    id, idp_user_id, email_hash, email_prefix, role, plan,
                    status, daily_quota, created_at, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'active', NULL, ?, NULL)
                """,
                (
                    user_id,
                    idp_user_id,
                    email_hash,
                    email_prefix,
                    resolved_role,
                    resolved_plan,
                    now,
                ),
            )
        else:
            user_id = existing["id"]
            if existing["status"] != "revoked" and idp_user_id in admin_ids:
                conn.execute(
                    "UPDATE users SET role = 'admin' WHERE id = ?",
                    (user_id,),
                )
            conn.execute(
                "UPDATE users SET email_hash = ?, email_prefix = ? WHERE id = ?",
                (email_hash, email_prefix, user_id),
            )
            if plan is not None:
                conn.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
            if role is not None:
                conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        assert row is not None
        return _row_to_user(row)
    finally:
        conn.close()


def set_status(*, idp_user_id: str, status: str) -> LocalUser | None:
    conn = connect()
    try:
        revoked_at = utc_now() if status == "revoked" else None
        conn.execute(
            "UPDATE users SET status = ?, revoked_at = ? WHERE idp_user_id = ?",
            (status, revoked_at, idp_user_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE idp_user_id = ?", (idp_user_id,)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def increment_request(user_id: str, day: str | None = None) -> int:
    day = day or utc_day()
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO usage_daily (user_id, day, request_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, day) DO UPDATE SET
              request_count = request_count + 1
            """,
            (user_id, day),
        )
        conn.commit()
        row = conn.execute(
            "SELECT request_count FROM usage_daily WHERE user_id = ? AND day = ?",
            (user_id, day),
        ).fetchone()
        return int(row["request_count"]) if row else 1
    finally:
        conn.close()


def add_token_usage(
    user_id: str,
    *,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_usd: float,
    day: str | None = None,
) -> None:
    day = day or utc_day()
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO usage_daily (
                user_id, day, request_count, prompt_tokens_est,
                completion_tokens_est, estimated_usd
            ) VALUES (?, ?, 0, ?, ?, ?)
            ON CONFLICT(user_id, day) DO UPDATE SET
              prompt_tokens_est = prompt_tokens_est + excluded.prompt_tokens_est,
              completion_tokens_est = completion_tokens_est + excluded.completion_tokens_est,
              estimated_usd = estimated_usd + excluded.estimated_usd
            """,
            (user_id, day, prompt_tokens, completion_tokens, estimated_usd),
        )
        conn.commit()
    finally:
        conn.close()


def used_today(user_id: str, day: str | None = None) -> int:
    day = day or utc_day()
    conn = connect()
    try:
        row = conn.execute(
            "SELECT request_count FROM usage_daily WHERE user_id = ? AND day = ?",
            (user_id, day),
        ).fetchone()
        return int(row["request_count"]) if row else 0
    finally:
        conn.close()


def global_usd_today(day: str | None = None) -> float:
    day = day or utc_day()
    conn = connect()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(estimated_usd), 0) AS total FROM usage_daily WHERE day = ?",
            (day,),
        ).fetchone()
        return float(row["total"]) if row else 0.0
    finally:
        conn.close()


def write_audit(
    *,
    action: str,
    actor_user_id: str | None = None,
    ip_hash: str | None = None,
    request_id: str | None = None,
    metadata_json: str | None = None,
) -> None:
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO audit_events (
                id, ts, actor_user_id, action, ip_hash, request_id, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                utc_now(),
                actor_user_id,
                action,
                ip_hash,
                request_id,
                metadata_json,
            ),
        )
        conn.commit()
    finally:
        conn.close()
