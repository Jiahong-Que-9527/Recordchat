"""Reranker hook (SPEC: optional for v0.1).

v0.1 ships a no-op pass-through so the pipeline has a stable seam for a
real cross-encoder / LLM reranker in v0.2 without changing call sites.
"""

from __future__ import annotations

from app.models.source import Chunk


def rerank(query: str, chunks: list[Chunk]) -> list[Chunk]:  # noqa: ARG001
    return chunks
