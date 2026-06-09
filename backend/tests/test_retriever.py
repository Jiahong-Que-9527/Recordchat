from app.core.config import Settings
from app.models.source import Chunk, ChunkMetadata
from app.rag.retriever import QdrantRetriever

from .conftest import FakeEmbeddingProvider


class _SpyClient:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def collection_exists(self, _collection: str) -> bool:
        return True

    def upsert(self, *, collection_name: str, points: list) -> None:
        assert collection_name == "recordchat_test"
        self.calls.append(len(points))


def _chunk(index: int) -> Chunk:
    return Chunk(
        chunk_id=f"chunk-{index}",
        content=f"content {index}",
        metadata=ChunkMetadata(
            source_name="test",
            source_url=None,
            version="v1",
            section_title=None,
            chunk_type="general",
            entity=None,
            related_entities=[],
        ),
    )


def test_qdrant_upsert_batches_points():
    retriever = QdrantRetriever(
        Settings(
            qdrant_url=":memory:",
            qdrant_collection="recordchat_test",
            embedding_dim=FakeEmbeddingProvider.dim,
            qdrant_upsert_batch_size=2,
        ),
        FakeEmbeddingProvider(),
    )
    spy = _SpyClient()
    retriever.client = spy  # type: ignore[assignment]

    indexed = retriever.upsert([_chunk(1), _chunk(2), _chunk(3), _chunk(4), _chunk(5)])

    assert indexed == 5
    assert spy.calls == [2, 2, 1]
