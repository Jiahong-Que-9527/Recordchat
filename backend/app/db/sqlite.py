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

CREATE TABLE IF NOT EXISTS sessions (
  token_hash   TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL,
  expires_at   TEXT NOT NULL,
  created_at   TEXT NOT NULL
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
    email: str = ""
    password_hash: str = ""
    email_verified: bool = False
    must_reset_password: bool = False
    failed_logins: int = 0
    locked_until: str | None = None

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
            _migrate_users(conn)
            conn.commit()
            _initialized.add(key)
    return conn


def _migrate_users(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    additions = {
        "email": "ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''",
        "password_hash": "ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''",
        "email_verified": "ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0",
        "must_reset_password": "ALTER TABLE users ADD COLUMN must_reset_password INTEGER NOT NULL DEFAULT 0",
        "failed_logins": "ALTER TABLE users ADD COLUMN failed_logins INTEGER NOT NULL DEFAULT 0",
        "locked_until": "ALTER TABLE users ADD COLUMN locked_until TEXT",
    }
    for name, ddl in additions.items():
        if name not in cols:
            conn.execute(ddl)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email) WHERE email != ''"
    )


def reset_db_state() -> None:
    """Test helper: forget which files were initialized."""
    with _lock:
        _initialized.clear()


def _row_to_user(row: sqlite3.Row) -> LocalUser:
    keys = set(row.keys())
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
        email=row["email"] if "email" in keys else "",
        password_hash=row["password_hash"] if "password_hash" in keys else "",
        email_verified=bool(row["email_verified"]) if "email_verified" in keys else False,
        must_reset_password=bool(row["must_reset_password"])
        if "must_reset_password" in keys
        else False,
        failed_logins=int(row["failed_logins"]) if "failed_logins" in keys else 0,
        locked_until=row["locked_until"] if "locked_until" in keys else None,
    )


def get_user_by_email(email: str) -> LocalUser | None:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> LocalUser | None:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


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
    user: LocalUser | None = None
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
        user = _row_to_user(row) if row else None
    finally:
        conn.close()
    if user is not None and status == "revoked":
        delete_user_sessions(user.id)
    return user


def list_users() -> list[LocalUser]:
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [_row_to_user(row) for row in rows]
    finally:
        conn.close()


def set_plan(
    *,
    idp_user_id: str,
    plan: str,
    daily_quota: int | None = None,
) -> LocalUser | None:
    if plan not in {"trial", "user"}:
        raise ValueError("plan must be trial or user")
    conn = connect()
    try:
        conn.execute(
            "UPDATE users SET plan = ?, daily_quota = ? WHERE idp_user_id = ?",
            (plan, daily_quota, idp_user_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE idp_user_id = ?", (idp_user_id,)
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def usage_summary(day: str | None = None) -> dict[str, float | int]:
    day = day or utc_day()
    conn = connect()
    try:
        usage = conn.execute(
            """
            SELECT
              COUNT(DISTINCT user_id) AS dau,
              COALESCE(SUM(request_count), 0) AS request_count,
              COALESCE(SUM(estimated_usd), 0) AS estimated_usd
            FROM usage_daily
            WHERE day = ?
            """,
            (day,),
        ).fetchone()
        limited = conn.execute(
            """
            SELECT COUNT(*) AS n FROM audit_events
            WHERE action = 'chat_429' AND ts LIKE ?
            """,
            (f"{day}%",),
        ).fetchone()
        return {
            "day": day,
            "dau": int(usage["dau"] or 0),
            "request_count": int(usage["request_count"] or 0),
            "estimated_usd": float(usage["estimated_usd"] or 0),
            "rate_limited_count": int(limited["n"] or 0),
        }
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


def create_local_user(
    *,
    email: str,
    email_hash: str,
    email_prefix: str,
    password_hash: str,
    plan: str = "trial",
    role: str = "user",
    email_verified: bool = True,
    must_reset_password: bool = False,
) -> LocalUser:
    now = utc_now()
    user_id = str(uuid.uuid4())
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO users (
                id, idp_user_id, email_hash, email_prefix, role, plan, status,
                daily_quota, created_at, revoked_at, email, password_hash,
                email_verified, must_reset_password, failed_logins, locked_until
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', NULL, ?, NULL, ?, ?, ?, ?, 0, NULL)
            """,
            (
                user_id,
                user_id,
                email_hash,
                email_prefix,
                role,
                plan,
                now,
                email.strip().lower(),
                password_hash,
                1 if email_verified else 0,
                1 if must_reset_password else 0,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        assert row is not None
        return _row_to_user(row)
    finally:
        conn.close()


def set_password(*, user_id: str, password_hash: str, must_reset: bool = False) -> None:
    conn = connect()
    try:
        conn.execute(
            """
            UPDATE users SET password_hash = ?, must_reset_password = ?,
              failed_logins = 0, locked_until = NULL
            WHERE id = ?
            """,
            (password_hash, 1 if must_reset else 0, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def record_login_failure(*, user_id: str, lock_after: int = 10, lock_minutes: int = 15) -> None:
    from datetime import timedelta

    conn = connect()
    try:
        row = conn.execute(
            "SELECT failed_logins FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        fails = int(row["failed_logins"]) + 1 if row else 1
        locked_until = None
        if fails >= lock_after:
            locked_until = (
                datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute(
            "UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
            (fails, locked_until, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def record_login_success(*, user_id: str) -> None:
    conn = connect()
    try:
        conn.execute(
            "UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()


def create_session(*, user_id: str, token_hash: str, expires_at: str) -> None:
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token_hash, user_id, expires_at, utc_now()),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_session(token_hash: str) -> LocalUser | None:
    conn = connect()
    try:
        row = conn.execute(
            """
            SELECT u.* FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            """,
            (token_hash, utc_now()),
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def delete_session(token_hash: str) -> None:
    conn = connect()
    try:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
    finally:
        conn.close()


def delete_user_sessions(user_id: str) -> None:
    conn = connect()
    try:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.commit()
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
