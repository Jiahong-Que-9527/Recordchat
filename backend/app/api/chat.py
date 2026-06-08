"""POST /chat — thin handler: parse request, call pipeline, return response.

No business logic here (SPEC section 14).
"""

import json
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse
from app.rag.pipeline import answer, answer_stream

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return answer(req.message)


def _sse_event(*, event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_chat_events(message: str) -> Iterator[str]:
    for item in answer_stream(message):
        yield _sse_event(event=item["event"], data=item["data"])


@router.post("/chat/stream")
def chat_stream(req: ChatRequest) -> StreamingResponse:
    return StreamingResponse(stream_chat_events(req.message), media_type="text/event-stream")
