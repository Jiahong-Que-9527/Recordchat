"""Ingestion service: load -> chunk -> embed -> store (SPEC section 5 / 6).

Always includes the curated glossary so the knowledge base is non-empty
even when data/raw/ has no files (graceful degradation).
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.domain.glossary import glossary_chunks
from app.models.chat import IngestResponse
from app.rag.chunker import chunk_documents
from app.rag.loader import load_documents
from app.rag.retriever import Retriever, get_retriever

logger = get_logger(__name__)


def run_ingest(
    source_dir: str = "data/raw",
    reset: bool = False,
    retriever: Retriever | None = None,
) -> IngestResponse:
    retriever = retriever or get_retriever()
    if reset:
        retriever.reset()

    docs = load_documents(source_dir)
    file_chunks = chunk_documents(docs)
    seed_chunks = glossary_chunks()
    all_chunks = seed_chunks + file_chunks

    indexed = retriever.upsert(all_chunks)
    logger.info(
        "Ingest complete: %d docs, %d chunks (%d glossary + %d file), %d indexed",
        len(docs), len(all_chunks), len(seed_chunks), len(file_chunks), indexed,
    )
    return IngestResponse(
        documents_loaded=len(docs),
        chunks_created=len(all_chunks),
        chunks_indexed=indexed,
    )
