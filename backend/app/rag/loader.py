"""Load raw documents from data/raw (SPEC section 5).

Each document may have a sidecar `<filename>.meta.json` describing its
source. Supported extensions map to a default chunk_type so the chunker
can apply a domain-aware strategy.
"""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.models.source import ChunkMetadata, RawDocument
from app.rag.canonical import describe_skip, is_canonical_source, load_sidecar

logger = get_logger(__name__)

# extension -> default document kind (drives chunking strategy)
_TEXT_EXTENSIONS = {
    ".ttl": "ontology",
    ".owl": "ontology",
    ".md": "docs",
    ".markdown": "docs",
    ".txt": "notes",
    ".json": "example",
    ".jsonld": "example",
    ".yaml": "api_spec",
    ".yml": "api_spec",
}


def _should_skip_path(path: Path) -> bool:
    return "_staging" in path.parts


def load_documents(source_dir: str) -> list[RawDocument]:
    root = Path(source_dir)
    if not root.exists():
        logger.info("Source dir %s does not exist; nothing to load.", source_dir)
        return []

    docs: list[RawDocument] = []
    skipped = 0
    for path in sorted(root.rglob("*")):
        if _should_skip_path(path):
            continue
        if not path.is_file() or path.suffix not in _TEXT_EXTENSIONS:
            continue
        if path.name.endswith(".meta.json"):
            continue

        sidecar = load_sidecar(path)
        if not is_canonical_source(path, sidecar, source_root=root):
            skipped += 1
            logger.info("Skipping non-canonical source: %s", describe_skip(path, sidecar))
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            logger.warning("Skipping unreadable file %s: %s", path, exc)
            continue

        doc_kind = sidecar.get("document_type", _TEXT_EXTENSIONS[path.suffix])
        metadata = ChunkMetadata(
            source_name=sidecar.get("source_name", path.stem),
            source_url=sidecar.get("url"),
            version=sidecar.get("version"),
            chunk_type=_doc_kind_to_chunk_type(doc_kind),
        )
        docs.append(RawDocument(path=str(path), text=text, metadata=metadata))

    logger.info(
        "Loaded %d documents from %s (%d non-canonical skipped)",
        len(docs),
        source_dir,
        skipped,
    )
    return docs


def _doc_kind_to_chunk_type(doc_kind: str) -> str:
    return {
        "ontology": "class_definition",
        "api_spec": "api",
        "docs": "concept",
        "example": "example",
        "notes": "general",
    }.get(doc_kind, "general")
