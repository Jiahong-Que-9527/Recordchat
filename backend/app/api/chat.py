"""POST /chat — thin handler: parse request, call pipeline, return response.

No business logic here (SPEC section 14).
"""

from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.rag.pipeline import answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return answer(req.message)
