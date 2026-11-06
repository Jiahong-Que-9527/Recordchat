"""Per-user and global chat limits. Not RAG logic — stay out of pipeline.py."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.config import get_settings
from app.core.llm import ALLOWED_CHAT_MODELS
from app.db.sqlite import (
    LocalUser,
    add_token_usage,
    global_usd_today,
    increment_request,
    used_today,
    write_audit,
)
from app.models.chat import ChatHistoryMessage, SyntheticMode

_lock = threading.Lock()
_streams: dict[str, int] = {}
_global_streams = 0

FLASH = "deepseek-v4-flash"


def reset_quota_state() -> None:
    global _global_streams
    with _lock:
        _streams.clear()
        _global_streams = 0


def seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((tomorrow - now).total_seconds()))


def _payload_too_large(message: str, history: list[ChatHistoryMessage] | None) -> bool:
    settings = get_settings()
    limit = settings.chat_max_message_chars
    if len(message) > limit:
        return True
    turns = history or []
    if len(turns) > settings.chat_max_history_turns:
        return True
    return any(len(item.content) > limit for item in turns)


def check_and_begin(
    user: LocalUser,
    message: str,
    history: list[ChatHistoryMessage] | None = None,
) -> None:
    global _global_streams
    settings = get_settings()
    if settings.llm_kill_switch:
        raise HTTPException(
            status_code=503,
            detail={"error": "unavailable", "retry_after_seconds": 3600},
            headers={"Retry-After": "3600"},
        )
    if global_usd_today() >= settings.llm_daily_budget_usd:
        raise HTTPException(
            status_code=503,
            detail={"error": "unavailable", "retry_after_seconds": seconds_until_utc_midnight()},
            headers={"Retry-After": str(seconds_until_utc_midnight())},
        )
    if user.status != "active":
        raise HTTPException(status_code=401, detail={"error": "revoked"})
    if _payload_too_large(message, history):
        raise HTTPException(status_code=400, detail={"error": "payload_too_large"})

    retry = seconds_until_utc_midnight()
    quota = user.effective_daily_quota(
        settings.chat_daily_limit_trial, settings.chat_daily_limit_user
    )
    if used_today(user.id) >= quota:
        write_audit(action="chat_429", actor_user_id=user.idp_user_id)
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limited", "retry_after_seconds": retry},
            headers={"Retry-After": str(retry)},
        )

    with _lock:
        current = _streams.get(user.idp_user_id, 0)
        if current >= settings.chat_max_concurrent_per_user:
            raise HTTPException(
                status_code=429,
                detail={"error": "rate_limited", "retry_after_seconds": 5},
                headers={"Retry-After": "5"},
            )
        if _global_streams >= settings.chat_global_max_streams:
            raise HTTPException(
                status_code=429,
                detail={"error": "rate_limited", "retry_after_seconds": 5},
                headers={"Retry-After": "5"},
            )
        _streams[user.idp_user_id] = current + 1
        _global_streams += 1

    increment_request(user.id)


def end_stream(idp_user_id: str) -> None:
    global _global_streams
    with _lock:
        current = _streams.get(idp_user_id, 0)
        if current <= 1:
            _streams.pop(idp_user_id, None)
        else:
            _streams[idp_user_id] = current - 1
        if _global_streams > 0:
            _global_streams -= 1


def clamp_model_and_mode(
    user: LocalUser,
    model: str | None,
    synthetic_mode: SyntheticMode | None,
) -> tuple[str | None, SyntheticMode | None]:
    if user.plan != "trial":
        if model is not None and model not in ALLOWED_CHAT_MODELS:
            model = FLASH
        return model, synthetic_mode
    return FLASH, SyntheticMode.local


def record_completion(user: LocalUser, message: str, answer: str) -> None:
    settings = get_settings()
    prompt_tokens = max(1, len(message) // 4)
    completion_tokens = max(1, len(answer) // 4)
    usd = ((prompt_tokens + completion_tokens) / 1000.0) * settings.llm_usd_per_1k_tokens
    add_token_usage(
        user.id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_usd=usd,
    )
    write_audit(action="chat_ok", actor_user_id=user.idp_user_id)
