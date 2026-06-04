"""Domain-aware chunking (SPEC section 5.3).

Strategy is chosen from the document's chunk_type (set by the loader):
    class_definition (ontology) -> one chunk per RDF class/property
    api              (openapi)  -> one chunk per endpoint
    example          (json-ld)  -> whole payload is one chunk
    concept (md) / general      -> split by markdown heading, then by size

All strategies fall back to size-based splitting if parsing fails, so a
malformed input never breaks ingestion.
"""

from __future__ import annotations

import hashlib
import re

import yaml

from app.core.logging import get_logger
from app.models.source import Chunk, ChunkMetadata, RawDocument

logger = get_logger(__name__)

_MAX_CHARS = 1200
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def _chunk_id(source_name: str, key: str) -> str:
    h = hashlib.sha1(f"{source_name}::{key}".encode()).hexdigest()[:16]
    return f"{source_name}::{h}"


def chunk_document(doc: RawDocument) -> list[Chunk]:
    ct = doc.metadata.chunk_type
    try:
        if ct == "class_definition":
            chunks = _chunk_ontology(doc)
        elif ct == "api":
            chunks = _chunk_openapi(doc)
        elif ct == "example":
            chunks = _chunk_whole(doc)
        else:
            chunks = _chunk_markdown(doc)
    except Exception as exc:  # noqa: BLE001 - robustness over purity
        logger.warning("Chunking failed for %s (%s); using size fallback.", doc.path, exc)
        chunks = _chunk_by_size(doc, doc.text, doc.metadata)
    return [c for c in chunks if c.content.strip()]


def chunk_documents(docs: list[RawDocument]) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc))
    return out


# --- strategies -----------------------------------------------------------

def _chunk_ontology(doc: RawDocument) -> list[Chunk]:
    """One chunk per owl:Class / rdf:Property using rdflib."""
    from rdflib import RDF, RDFS, Graph, OWL

    g = Graph()
    g.parse(data=doc.text, format="turtle")

    chunks: list[Chunk] = []
    seen: set[str] = set()

    targets = list(g.subjects(RDF.type, OWL.Class)) + list(g.subjects(RDF.type, RDFS.Class))
    prop_types = [OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property]
    properties = [s for pt in prop_types for s in g.subjects(RDF.type, pt)]

    def _local_name(uri) -> str:
        s = str(uri)
        return re.split(r"[#/]", s)[-1] or s

    for subj, chunk_type in (
        *[(t, "class_definition") for t in targets],
        *[(p, "property_definition") for p in properties],
    ):
        name = _local_name(subj)
        if name in seen:
            continue
        seen.add(name)
        label = g.value(subj, RDFS.label)
        comment = g.value(subj, RDFS.comment)
        parts = [f"{chunk_type.replace('_', ' ').title()}: {name}"]
        if label:
            parts.append(f"Label: {label}")
        if comment:
            parts.append(f"Definition: {comment}")
        content = "\n".join(parts)
        meta = doc.metadata.model_copy(
            update={"chunk_type": chunk_type, "entity": name, "section_title": name}
        )
        chunks.append(Chunk(chunk_id=_chunk_id(meta.source_name, name), content=content, metadata=meta))

    if not chunks:  # ontology had no recognizable classes
        return _chunk_by_size(doc, doc.text, doc.metadata)
    logger.info("Ontology %s -> %d class/property chunks", doc.path, len(chunks))
    return chunks


def _chunk_openapi(doc: RawDocument) -> list[Chunk]:
    """One chunk per (path, method) in an OpenAPI document."""
    spec = yaml.safe_load(doc.text)
    if not isinstance(spec, dict) or "paths" not in spec:
        return _chunk_markdown(doc)

    chunks: list[Chunk] = []
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            summary = op.get("summary", "")
            desc = op.get("description", "")
            content = f"API endpoint: {method.upper()} {path}\n{summary}\n{desc}".strip()
            section = f"{method.upper()} {path}"
            meta = doc.metadata.model_copy(update={"chunk_type": "api", "section_title": section})
            chunks.append(Chunk(chunk_id=_chunk_id(meta.source_name, section), content=content, metadata=meta))
    if not chunks:
        return _chunk_markdown(doc)
    return chunks


def _chunk_whole(doc: RawDocument) -> list[Chunk]:
    meta = doc.metadata.model_copy(update={"section_title": doc.metadata.source_name})
    return [Chunk(chunk_id=_chunk_id(meta.source_name, "payload"), content=doc.text, metadata=meta)]


def _chunk_markdown(doc: RawDocument) -> list[Chunk]:
    """Split by markdown headings, then size-cap each section."""
    text = doc.text
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return _chunk_by_size(doc, text, doc.metadata)

    chunks: list[Chunk] = []
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        meta = doc.metadata.model_copy(update={"section_title": title})
        chunks.extend(_chunk_by_size(doc, section_text, meta, key_prefix=title))
    return chunks


def _chunk_by_size(
    doc: RawDocument, text: str, meta: ChunkMetadata, key_prefix: str = ""
) -> list[Chunk]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[Chunk] = []
    buf = ""
    idx = 0

    def _flush() -> None:
        nonlocal buf, idx
        if buf.strip():
            key = f"{key_prefix}#{idx}"
            chunks.append(
                Chunk(chunk_id=_chunk_id(meta.source_name, key), content=buf.strip(), metadata=meta)
            )
            idx += 1
            buf = ""

    for para in paragraphs:
        if len(buf) + len(para) + 2 > _MAX_CHARS and buf:
            _flush()
        buf += para + "\n\n"
    _flush()
    if not chunks and text.strip():
        chunks.append(
            Chunk(chunk_id=_chunk_id(meta.source_name, f"{key_prefix}#0"), content=text.strip(), metadata=meta)
        )
    return chunks
