"""Lightweight JSONL request diagnostics (AUD-07).

Records query_type, ranked chunk ids, latency, and model/config without
pulling in OpenTelemetry (that stays in the v0.3 sketch).

By default the raw user question is **not** stored (v0.3.1 trial auth). Set
``RECORDCHAT_REQUEST_LOG_INCLUDE_QUERY=true`` only for a time-boxed local
debug session.

Destination:
- ``RECORDCHAT_REQUEST_LOG=stdout`` (default) → structured log line via logger
- ``RECORDCHAT_REQUEST_LOG=<path>`` → append JSONL to that file (e.g. data/logs/requests.jsonl)
- ``RECORDCHAT_REQUEST_LOG=off`` → disabled
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger("recordchat.request")

_DEFAULT = "stdout"
_SENSITIVE_KEYS = ("query", "message", "answer", "history", "user_prompt", "prompt")


def _destination() -> str:
    return (os.environ.get("RECORDCHAT_REQUEST_LOG") or _DEFAULT).strip() or _DEFAULT


def _resolve_log_path(dest: str) -> Path:
    """Resolve a log path for local repo runs and the Docker image.

    Relative paths are rooted at the repo (local) or ``/app`` (container),
    not at ``backend/app/core/``.
    """
    path = Path(dest).expanduser()
    if path.is_absolute():
        return path
    docker_root = Path("/app")
    if (docker_root / "app" / "core" / "request_log.py").is_file():
        return docker_root / path
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / path


def _include_raw_query() -> bool:
    flag = (os.environ.get("RECORDCHAT_REQUEST_LOG_INCLUDE_QUERY") or "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def redact_log_event(event: dict[str, Any]) -> dict[str, Any]:
    """Copy *event* and drop raw question text unless the include flag is on."""
    payload = dict(event)
    if not payload.get("request_id"):
        payload["request_id"] = str(uuid.uuid4())
    raw_query = payload.get("query")
    if isinstance(raw_query, str):
        encoded = raw_query.encode("utf-8")
        payload.setdefault("query_len", len(raw_query))
        payload.setdefault("query_hash", hashlib.sha256(encoded).hexdigest())
    if not _include_raw_query():
        for key in _SENSITIVE_KEYS:
            payload.pop(key, None)
    return payload


def log_chat_request(event: dict[str, Any]) -> None:
    """Append one diagnostic event. Never raises into the request path."""
    try:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **redact_log_event(event),
        }
        line = json.dumps(payload, ensure_ascii=False, default=str)
        dest = _destination().lower()
        if dest in {"", "off", "0", "false", "no"}:
            return
        if dest in {"stdout", "stderr", "log"}:
            logger.info("request_diag %s", line)
            return
        path = _resolve_log_path(dest)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning("request diagnostic log failed: %s", exc)


class RequestTimer:
    """Simple monotonic timer for latency_ms fields."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    def latency_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)
