"""Vector retrieval over Qdrant (SPEC section 7 / 14).

Retriever is an abstraction so it can be swapped later. v0.1 ships one
implementation, QdrantRetriever, which supports both an embedded in-process
store (QDRANT_URL=":memory:", offline friendly) and a remote server.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from itertools import islice

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import Settings, get_settings
from app.core.embeddings import EmbeddingProvider, get_embedding_provider
from app.core.logging import get_logger
from app.models.source import Chunk, ChunkMetadata

logger = get_logger(__name__)

_NAMESPACE = uuid.UUID("a3f1c0de-0000-4000-8000-0a1b2c3d4e5f")


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, chunk_id))


def _batched(items: list[qmodels.PointStruct], size: int) -> list[list[qmodels.PointStruct]]:
    if size <= 0:
        return [items]

    out: list[list[qmodels.PointStruct]] = []
    iterator = iter(items)
    while batch := list(islice(iterator, size)):
        out.append(batch)
    return out


class Retriever(ABC):
    @abstractmethod
    def ensure_collection(self) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def upsert(self, chunks: list[Chunk]) -> int: ...

    @abstractmethod
    def search(self, query: str, top_k: int) -> list[Chunk]: ...

    @abstractmethod
    def search_ontology_candidates(self, entities: list[str], top_k: int) -> list[Chunk]: ...


class QdrantRetriever(Retriever):
    def __init__(self, settings: Settings, embedder: EmbeddingProvider) -> None:
        self.collection = settings.qdrant_collection
        self.dim = settings.embedding_dim
        self.upsert_batch_size = settings.qdrant_upsert_batch_size
        self.embedder = embedder
        if settings.qdrant_url == ":memory:" or not settings.qdrant_url:
            logger.info("Using in-memory Qdrant store.")
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(url=settings.qdrant_url)

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(
                    size=self.dim, distance=qmodels.Distance.COSINE
                ),
            )
            logger.info("Created Qdrant collection %s (dim=%d)", self.collection, self.dim)

    def reset(self) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
            logger.info("Deleted Qdrant collection %s", self.collection)
        self.ensure_collection()

    def upsert(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        self.ensure_collection()
        vectors = self.embedder.embed([c.content for c in chunks])
        points = [
            qmodels.PointStruct(
                id=_point_id(c.chunk_id),
                vector=vec,
                payload={
                    "chunk_id": c.chunk_id,
                    "content": c.content,
                    **c.metadata.model_dump(),
                },
            )
            for c, vec in zip(chunks, vectors)
        ]
        for batch in _batched(points, self.upsert_batch_size):
            self.client.upsert(collection_name=self.collection, points=batch)
        logger.info(
            "Upserted %d points into %s using batch_size=%d",
            len(points),
            self.collection,
            self.upsert_batch_size,
        )
        return len(points)

    def search(self, query: str, top_k: int) -> list[Chunk]:
        self.ensure_collection()
        vector = self.embedder.embed_one(query)
        hits = self.client.query_points(
            collection_name=self.collection, query=vector, limit=top_k, with_payload=True
        ).points
        chunks: list[Chunk] = []
        for h in hits:
            p = h.payload or {}
            chunks.append(
                Chunk(
                    chunk_id=p.get("chunk_id", str(h.id)),
                    content=p.get("content", ""),
                    metadata=ChunkMetadata(
                        source_name=p.get("source_name", "unknown"),
                        source_url=p.get("source_url"),
                        version=p.get("version"),
                        section_title=p.get("section_title"),
                        chunk_type=p.get("chunk_type", "general"),
                        entity=p.get("entity"),
                        related_entities=p.get("related_entities", []) or [],
                    ),
                )
            )
        return chunks

    def search_ontology_candidates(self, entities: list[str], top_k: int) -> list[Chunk]:
        if not entities or top_k <= 0:
            return []

        self.ensure_collection()
        filters = [
            qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="chunk_type",
                        match=qmodels.MatchAny(any=["class_definition", "property_definition"]),
                    ),
                    qmodels.FieldCondition(key="entity", match=qmodels.MatchAny(any=entities)),
                ]
            ),
            qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="chunk_type",
                        match=qmodels.MatchAny(any=["class_definition", "property_definition"]),
                    ),
                    qmodels.FieldCondition(
                        key="related_entities", match=qmodels.MatchAny(any=entities)
                    ),
                ]
            ),
        ]

        found: dict[str, Chunk] = {}
        for flt in filters:
            points, _ = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=flt,
                limit=top_k,
                with_payload=True,
            )
            for point in points:
                payload = point.payload or {}
                chunk = Chunk(
                    chunk_id=payload.get("chunk_id", str(point.id)),
                    content=payload.get("content", ""),
                    metadata=ChunkMetadata(
                        source_name=payload.get("source_name", "unknown"),
                        source_url=payload.get("source_url"),
                        version=payload.get("version"),
                        section_title=payload.get("section_title"),
                        chunk_type=payload.get("chunk_type", "general"),
                        entity=payload.get("entity"),
                        related_entities=payload.get("related_entities", []) or [],
                    ),
                )
                found.setdefault(chunk.chunk_id, chunk)
                if len(found) >= top_k:
                    return list(found.values())
        return list(found.values())


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = QdrantRetriever(get_settings(), get_embedding_provider())
    return _retriever
