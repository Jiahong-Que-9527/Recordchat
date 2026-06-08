"""Shared fixtures with explicit test doubles and in-memory Qdrant."""

import os

os.environ.setdefault("QDRANT_URL", ":memory:")
os.environ.setdefault("EMBEDDING_DIM", "32")

import pytest

from app.core.config import Settings
from app.core.embeddings import EmbeddingProvider
from app.core.llm import LLMProvider
from app.rag.ingest import run_ingest
from app.rag.retriever import QdrantRetriever


class FakeEmbeddingProvider(EmbeddingProvider):
    dim = 32

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for idx, byte in enumerate(text.encode("utf-8")):
            vec[idx % self.dim] += byte / 255.0
        norm = sum(value * value for value in vec) ** 0.5
        if norm:
            vec = [value / norm for value in vec]
        return vec


class FakeLLMProvider(LLMProvider):
    def complete(self, *, system: str, user: str) -> str:
        return f"Stub answer based on prompt: {user[:200]}"


@pytest.fixture
def retriever():
    settings = Settings(embedding_dim=FakeEmbeddingProvider.dim)
    r = QdrantRetriever(settings, FakeEmbeddingProvider())
    r.reset()
    return r


@pytest.fixture
def ingested_retriever(retriever):
    run_ingest(source_dir="data/raw", reset=False, retriever=retriever)
    return retriever
