"""Canonical source version policy (AUD-02 / #27).

See docs/data_source_plan.md §10. A given class, property, endpoint, or spec
release should have one live canonical version in the corpus. Non-canonical
copies may remain on disk but must not be ingested or loaded into OntologyGraph.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_ONTOLOGY_SUFFIXES = {".ttl", ".owl"}


def _version_set(raw: str) -> set[str]:
    return {part.strip() for part in raw.split(",") if part.strip()}


def _rel_parts(path: Path, source_root: Path | None) -> tuple[str, ...]:
    if source_root is not None:
        try:
            return Path(path).resolve().relative_to(Path(source_root).resolve()).parts
        except ValueError:
            pass
    return Path(path).parts


def load_sidecar(path: Path) -> dict:
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Invalid sidecar metadata: %s", meta_path)
        return {}


def is_canonical_source(
    path: Path,
    sidecar: dict | None = None,
    *,
    source_root: Path | None = None,
    settings: Settings | None = None,
) -> bool:
    """Return True when ``path`` should be ingested / loaded into the graph."""
    settings = settings or get_settings()
    sidecar = sidecar if sidecar is not None else load_sidecar(path)
    parts = _rel_parts(path, source_root)
    version = str(sidecar.get("version") or "")
    doc_type = str(sidecar.get("document_type") or "")
    source_name = str(sidecar.get("source_name") or "").lower()
    name_lower = path.name.lower()

    ontology_versions = _version_set(settings.canonical_ontology_versions)
    openapi_versions = _version_set(settings.canonical_openapi_versions)
    spec_versions = _version_set(settings.canonical_spec_versions)
    api_ontology_versions = _version_set(settings.canonical_api_ontology_versions)
    domain = str(sidecar.get("domain") or "")

    # Example payloads are not version-competing ontology/spec families.
    if doc_type == "example":
        return True

    # Community TTL references and GraphDB repository configs are not live
    # ontology/API corpus (they duplicate or are infra, not Q&A sources).
    if doc_type == "ttl_reference" or "neone-repository" in name_lower:
        return False

    # Official OpenAPI family — one live version.
    if "api_specs" in parts and "official" in parts:
        return version in openapi_versions

    # Spec release trees — keep development + pinned release; drop older releases.
    if "one_record_docs" in parts and any(
        part.startswith("spec_") or part == "spec_development" for part in parts
    ):
        # Nested ontology extracts duplicate the official ontology family.
        if doc_type == "ontology" or path.suffix.lower() in _ONTOLOGY_SUFFIXES:
            return False
        return version in spec_versions

    # NE:ONE implementation ontologies: keep NE:ONE-specific files, skip IATA
    # mirrors that duplicate ontology/official.
    if domain in {"one_record_implementation", "ne_one"} or "ne_one" in parts:
        if path.suffix.lower() in _ONTOLOGY_SUFFIXES or doc_type == "ontology":
            if (
                name_lower.startswith("iata-1r-")
                or "one-record-api-ontology" in name_lower
                or "neone-repository" in name_lower
            ):
                return False
            return True
        return True

    # Ontology family — only real ontology serializations, not notes under
    # ontology/ folders (e.g. ontology_sources.md).
    if doc_type == "ontology" or path.suffix.lower() in _ONTOLOGY_SUFFIXES:
        # Prefer Turtle when an OWL twin exists for the same stem.
        if path.suffix.lower() == ".owl":
            ttl_peer = path.with_suffix(".ttl")
            if ttl_peer.exists():
                return False

        if (
            "api ontology" in source_name
            or "api_ontology" in name_lower
            or "one_record_api_ontology" in name_lower
        ):
            return version in api_ontology_versions

        # Cargo / data-model ontology — only the pinned release.
        if version in ontology_versions:
            return True

        # Unknown/unversioned ontology outside the official pin: keep only when
        # it does not compete with a pinned official file (e.g. notes).
        if "official" in parts:
            return False
        # Curated illustrative subsets (version=demo) duplicate official classes.
        if version in {"demo", "working_draft"} or version.startswith("2023"):
            return False
        return True

    return True


def describe_skip(path: Path, sidecar: dict | None = None) -> str:
    sidecar = sidecar if sidecar is not None else load_sidecar(path)
    version = sidecar.get("version") or "unknown"
    doc_type = sidecar.get("document_type") or "unknown"
    return f"{path} (document_type={doc_type}, version={version})"
