"""POST /ingest — trigger load/chunk/embed/store from data/raw."""

from fastapi import APIRouter

from app.models.chat import IngestRequest, IngestResponse
from app.rag.ingest import run_ingest

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest | None = None) -> IngestResponse:
    req = req or IngestRequest()
    return run_ingest(source_dir=req.source_dir, reset=req.reset)
