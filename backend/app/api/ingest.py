"""POST /ingest — trigger load/chunk/embed/store from data/raw."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_settings
from app.models.chat import IngestRequest, IngestResponse
from app.rag.ingest import run_ingest

router = APIRouter()


def _run(req: IngestRequest | None) -> IngestResponse:
    settings = get_settings()
    req = req or IngestRequest()
    reset = bool(req.reset) if settings.ingest_allow_reset else False
    return run_ingest(source_dir=req.source_dir, reset=reset)


@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest | None = None) -> IngestResponse:
    if get_settings().auth_enforced():
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    return _run(req)


@router.post("/internal/ingest", response_model=IngestResponse)
def ingest_internal(
    req: IngestRequest | None = None,
    x_ingest_token: Annotated[str | None, Header()] = None,
) -> IngestResponse:
    settings = get_settings()
    if settings.auth_enforced():
        expected = settings.ingest_token
        provided = x_ingest_token or ""
        if not expected or not hmac.compare_digest(provided, expected):
            raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    return _run(req)
