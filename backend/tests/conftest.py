"""Shared fixtures. Forces offline `local` providers + in-memory Qdrant."""

import os

os.environ.setdefault("LLM_PROVIDER", "local")
os.environ.setdefault("EMBEDDING_PROVIDER", "local")
os.environ.setdefault("QDRANT_URL", ":memory:")
os.environ.setdefault("EMBEDDING_DIM", "256")

import pytest

from app.core.config import Settings
from app.core.embeddings import build_embedding_provider
from app.rag.ingest import run_ingest
from app.rag.retriever import QdrantRetriever


@pytest.fixture
def retriever():
    settings = Settings()
    r = QdrantRetriever(settings, build_embedding_provider(settings))
    r.reset()
    return r


@pytest.fixture
def ingested_retriever(retriever):
    run_ingest(source_dir="data/raw", reset=False, retriever=retriever)
    return retriever
