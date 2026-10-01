"""POST /chat — thin handler: parse request, call pipeline, return response.

No RAG/LLM logic here (SPEC section 14). Auth and quota Depends stay here.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.internal_auth import get_auth_user
from app.core.quota import check_and_begin, clamp_model_and_mode, end_stream, record_completion
from app.db.sqlite import LocalUser
from app.models.chat import ChatRequest, ChatResponse
from app.rag.pipeline import answer, answer_stream

router = APIRouter()


def _prepare(req: ChatRequest, user: LocalUser | None):
    model, mode = req.model, req.synthetic_mode
    if user is not None:
        check_and_begin(user, req.message, req.history)
        model, mode = clamp_model_and_mode(user, model, mode)
    return model, mode


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    user: Annotated[LocalUser | None, Depends(get_auth_user)] = None,
) -> ChatResponse:
    model, mode = _prepare(req, user)
    try:
        response = answer(
            req.message,
            model=model,
            history=req.history,
            synthetic_mode=mode,
        )
        if user is not None:
            record_completion(user, req.message, response.answer)
        return response
    finally:
        if user is not None:
            end_stream(user.idp_user_id)


def _sse_event(*, event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_chat_events(
    message: str,
    model: str | None = None,
    history=None,
    synthetic_mode=None,
) -> Iterator[str]:
    for item in answer_stream(
        message,
        model=model,
        history=history,
        synthetic_mode=synthetic_mode,
    ):
        yield _sse_event(event=item["event"], data=item["data"])


@router.post("/chat/stream")
def chat_stream(
    req: ChatRequest,
    user: Annotated[LocalUser | None, Depends(get_auth_user)] = None,
) -> StreamingResponse:
    model, mode = _prepare(req, user)

    def generate() -> Iterator[str]:
        parts: list[str] = []
        try:
            for item in answer_stream(
                req.message,
                model=model,
                history=req.history,
                synthetic_mode=mode,
            ):
                if item.get("event") == "token":
                    text = (item.get("data") or {}).get("text")
                    if isinstance(text, str):
                        parts.append(text)
                yield _sse_event(event=item["event"], data=item["data"])
            if user is not None:
                record_completion(user, req.message, "".join(parts))
        finally:
            if user is not None:
                end_stream(user.idp_user_id)

    return StreamingResponse(generate(), media_type="text/event-stream")
