"""Internal data models for the ingestion / retrieval path.

These describe documents as they move through:
    RawDocument  -> (chunker) -> Chunk[]  -> (embeddings) -> Qdrant
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# chunk_type values are part of the SPEC (section 5.3). Keep them stable.
ChunkType = str  # one of: concept | api | class_definition | property_definition | example | general


class ChunkMetadata(BaseModel):
    """Metadata attached to every chunk and stored in the Qdrant payload."""

    source_name: str
    source_url: str | None = None
    version: str | None = None
    section_title: str | None = None
    chunk_type: ChunkType = "general"
    entity: str | None = None
    related_entities: list[str] = Field(default_factory=list)


class Chunk(BaseModel):
    """A retrievable unit of knowledge."""

    chunk_id: str
    content: str
    metadata: ChunkMetadata


class RawDocument(BaseModel):
    """A document loaded from data/raw before chunking."""

    path: str
    text: str
    metadata: ChunkMetadata
