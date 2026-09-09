"""Vector + lexical hybrid retrieval over Qdrant (SPEC section 7 / 14, #29).

Retriever is an abstraction so it can be swapped later. v0.1 ships one
implementation, QdrantRetriever, which supports both an embedded in-process
store (QDRANT_URL=":memory:", offline friendly) and a remote server.

Hybrid retrieval (#29): dense cosine candidates are fused with an in-process
BM25-lite lexical index via reciprocal rank fusion. Optional metadata filters
narrow candidates by query type (chunk_type include/exclude).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import islice

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import Settings, get_settings
from app.core.embeddings import EmbeddingProvider, get_embedding_provider
from app.core.logging import get_logger
from app.models.source import Chunk, ChunkMetadata
from app.rag.lexical import LexicalIndex, reciprocal_rank_fuse

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


@dataclass(frozen=True)
class SearchFilter:
    """Optional metadata constraints for hybrid search (#29)."""

    chunk_types: tuple[str, ...] = ()
    exclude_chunk_types: tuple[str, ...] = ()
    source_name_contains: tuple[str, ...] = ()

    def allows(self, chunk: Chunk) -> bool:
        ctype = chunk.metadata.chunk_type or "general"
        if self.chunk_types and ctype not in self.chunk_types:
            return False
        if self.exclude_chunk_types and ctype in self.exclude_chunk_types:
            return False
        if self.source_name_contains:
            name = (chunk.metadata.source_name or "").lower()
            if not any(token.lower() in name for token in self.source_name_contains):
                return False
        return True

    def is_empty(self) -> bool:
        return not (self.chunk_types or self.exclude_chunk_types or self.source_name_contains)


def _chunk_from_payload(point_id: object, payload: dict) -> Chunk:
    return Chunk(
        chunk_id=payload.get("chunk_id", str(point_id)),
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


class Retriever(ABC):
    @abstractmethod
    def ensure_collection(self) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def upsert(self, chunks: list[Chunk]) -> int: ...

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int,
        *,
        search_filter: SearchFilter | None = None,
    ) -> list[Chunk]: ...

    @abstractmethod
    def search_ontology_candidates(self, entities: list[str], top_k: int) -> list[Chunk]: ...


class QdrantRetriever(Retriever):
    def __init__(self, settings: Settings, embedder: EmbeddingProvider) -> None:
        self.collection = settings.qdrant_collection
        self.dim = settings.embedding_dim
        self.upsert_batch_size = settings.qdrant_upsert_batch_size
        self.embedder = embedder
        self._lexical = LexicalIndex()
        self._in_memory = settings.qdrant_url == ":memory:" or not settings.qdrant_url
        if self._in_memory:
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
            self._ensure_payload_indexes()

    def _ensure_payload_indexes(self) -> None:
        # Payload indexes are a no-op (and warn) for local in-memory Qdrant.
        if self._in_memory:
            return
        for field_name, schema in (
            ("chunk_type", qmodels.PayloadSchemaType.KEYWORD),
            ("entity", qmodels.PayloadSchemaType.KEYWORD),
        ):
            try:
                self.client.create_payload_index(
                    collection_name=self.collection,
                    field_name=field_name,
                    field_schema=schema,
                )
            except Exception:  # noqa: BLE001
                logger.debug("Payload index %s not created (may already exist).", field_name)

    def reset(self) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
            logger.info("Deleted Qdrant collection %s", self.collection)
        self._lexical.clear()
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
        self._lexical.add(chunks)
        logger.info(
            "Upserted %d points into %s using batch_size=%d",
            len(points),
            self.collection,
            self.upsert_batch_size,
        )
        return len(points)

    def _qdrant_filter(self, search_filter: SearchFilter | None) -> qmodels.Filter | None:
        if search_filter is None or search_filter.is_empty():
            return None
        must: list[qmodels.Condition] = []
        must_not: list[qmodels.Condition] = []
        if search_filter.chunk_types:
            must.append(
                qmodels.FieldCondition(
                    key="chunk_type",
                    match=qmodels.MatchAny(any=list(search_filter.chunk_types)),
                )
            )
        if search_filter.exclude_chunk_types:
            must_not.append(
                qmodels.FieldCondition(
                    key="chunk_type",
                    match=qmodels.MatchAny(any=list(search_filter.exclude_chunk_types)),
                )
            )
        # source_name_contains is applied as a post-filter in SearchFilter.allows —
        # Qdrant substring match needs a text index we do not require locally.
        if not must and not must_not:
            return None
        return qmodels.Filter(must=must or None, must_not=must_not or None)

    def _dense_search(
        self,
        query: str,
        top_k: int,
        *,
        search_filter: SearchFilter | None = None,
    ) -> list[Chunk]:
        self.ensure_collection()
        vector = self.embedder.embed_one(query)
        query_filter = self._qdrant_filter(search_filter)
        try:
            hits = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            ).points
        except Exception as exc:  # noqa: BLE001
            # Filtered query can fail if payload indexes are missing; retry bare.
            logger.warning("Dense filtered search failed (%s); retrying without filter.", exc)
            hits = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                limit=top_k,
                with_payload=True,
            ).points
        chunks = [_chunk_from_payload(h.id, h.payload or {}) for h in hits]
        if search_filter is not None:
            chunks = [c for c in chunks if search_filter.allows(c)]
        return chunks

    def search(
        self,
        query: str,
        top_k: int,
        *,
        search_filter: SearchFilter | None = None,
    ) -> list[Chunk]:
        """Hybrid dense + lexical search fused with RRF (#29)."""
        if top_k <= 0:
            return []

        # Over-fetch each channel so fusion has room after filtering.
        channel_k = max(top_k, min(top_k * 2, 40))
        dense = self._dense_search(query, channel_k, search_filter=search_filter)
        predicate = search_filter.allows if search_filter is not None else None
        lexical = self._lexical.search(query, channel_k, predicate=predicate)

        fused = reciprocal_rank_fuse(dense, lexical, limit=top_k)

        # Only backfill when the filter returned nothing — never re-introduce
        # explicitly excluded chunk types into a non-empty filtered pool.
        if search_filter is not None and not fused:
            logger.info("Hybrid search empty with filter; backfilling unfiltered.")
            fused = reciprocal_rank_fuse(
                self._dense_search(query, channel_k, search_filter=None),
                self._lexical.search(query, channel_k, predicate=None),
                limit=top_k,
            )
        return fused[:top_k]

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
                chunk = _chunk_from_payload(point.id, point.payload or {})
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
