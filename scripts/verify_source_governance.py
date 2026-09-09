#!/usr/bin/env python3
"""Verify source-governance metadata for the curated core corpus."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.config import Settings  # noqa: E402
from app.rag.canonical import is_canonical_source, load_sidecar  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "docs" / "data_sources_registry.yaml"
SOURCE_ROOT = REPO_ROOT / "data" / "raw"

GOVERNED_ROOTS = [
    REPO_ROOT / "data" / "raw" / "one_record_docs" / "spec_development",
    REPO_ROOT / "data" / "raw" / "one_record_docs" / "spec_2025_07",
    REPO_ROOT / "data" / "raw" / "one_record_docs" / "spec_2023_12",
    REPO_ROOT / "data" / "raw" / "ontology" / "official",
    REPO_ROOT / "data" / "raw" / "api_specs" / "official",
    REPO_ROOT / "data" / "raw" / "api_specs" / "ne_one",
    REPO_ROOT / "data" / "raw" / "one_record_docs" / "ne_one",
    REPO_ROOT / "data" / "raw" / "examples" / "official" / "one_record_repo_examples",
    REPO_ROOT / "data" / "raw" / "examples" / "ne_one",
]
GOVERNED_EXTRA_FILES = [
    REPO_ROOT / "data" / "raw" / "examples" / "official" / "one_record_examples_sources.md",
]
GOVERNED_EXTENSIONS = {".md", ".ttl", ".owl", ".yaml", ".yml", ".jsonld", ".json"}
REQUIRED_META_FIELDS = {
    "source_name",
    "version",
    "url",
    "document_type",
    "domain",
    "registry_id",
    "batch_id",
    "ingested_at",
}


def load_registry() -> dict[str, set[str]]:
    raw = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry: dict[str, set[str]] = {}
    for item in raw:
        registry_id = item["id"]
        batches = {batch["batch_id"] for batch in item.get("batches", [])}
        registry[registry_id] = batches
    return registry


def iter_governed_files() -> list[Path]:
    files: set[Path] = set()
    for root in GOVERNED_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name.endswith(".meta.json") or path.name == ".gitkeep":
                continue
            if "assets" in path.parts:
                continue
            if path.suffix not in GOVERNED_EXTENSIONS:
                continue
            files.add(path)
    for path in GOVERNED_EXTRA_FILES:
        if path.exists():
            files.add(path)
    return sorted(files)


def _source_family(path: Path, meta: dict) -> str:
    parts = path.parts
    source_name = str(meta.get("source_name") or "").lower()
    name = path.name.lower()
    domain = str(meta.get("domain") or "")
    doc_type = str(meta.get("document_type") or "")
    if "api_specs" in parts and "official" in parts:
        return "openapi"
    if "one_record_docs" in parts and any(
        part.startswith("spec_") or part == "spec_development" for part in parts
    ):
        return "spec_docs"
    if domain in {"one_record_implementation", "ne_one"} or "ne_one" in parts:
        return "ne_one"
    if (
        "api ontology" in source_name
        or "api_ontology" in name
        or "one_record_api_ontology" in name
    ):
        return "ontology_api"
    if doc_type == "example":
        return "example"
    if doc_type == "ontology" or path.suffix in {".ttl", ".owl"}:
        return "ontology_cargo"
    return f"other:{doc_type or 'unknown'}"


def report_live_duplicates(settings: Settings | None = None) -> list[str]:
    """AUD-02: fail when more than one live version exists per exclusive family."""
    settings = settings or Settings()
    live: dict[str, set[str]] = defaultdict(set)
    live_paths: dict[str, list[str]] = defaultdict(list)

    for path in iter_governed_files():
        meta = load_sidecar(path)
        if not meta:
            continue
        if not is_canonical_source(path, meta, source_root=SOURCE_ROOT, settings=settings):
            continue
        family = _source_family(path, meta)
        version = str(meta.get("version") or "unknown")
        live[family].add(version)
        live_paths[family].append(f"{path.relative_to(REPO_ROOT)}@{version}")

    errors: list[str] = []
    exclusive_families = ("ontology_cargo", "openapi", "ontology_api")
    for family in exclusive_families:
        versions = live.get(family, set())
        if len(versions) > 1:
            errors.append(
                f"live duplicate versions for {family}: {sorted(versions)} "
                f"({'; '.join(live_paths[family][:8])})"
            )

    allowed_spec = {
        part.strip()
        for part in settings.canonical_spec_versions.split(",")
        if part.strip()
    }
    unexpected_spec = live.get("spec_docs", set()) - allowed_spec
    if unexpected_spec:
        errors.append(
            f"live spec_docs versions outside canonical allowlist "
            f"{sorted(allowed_spec)}: {sorted(unexpected_spec)}"
        )
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    registry = load_registry()

    loader_text = (REPO_ROOT / "backend" / "app" / "rag" / "loader.py").read_text(
        encoding="utf-8"
    )
    graph_text = (
        REPO_ROOT / "backend" / "app" / "domain" / "ontology_graph.py"
    ).read_text(encoding="utf-8")
    if "_staging" not in loader_text:
        errors.append("backend/app/rag/loader.py no longer explicitly skips _staging")
    if "_staging" not in graph_text:
        errors.append("backend/app/domain/ontology_graph.py no longer explicitly skips _staging")
    if "is_canonical_source" not in loader_text:
        errors.append("backend/app/rag/loader.py does not apply canonical source policy")
    if "is_canonical_source" not in graph_text:
        errors.append(
            "backend/app/domain/ontology_graph.py does not apply canonical source policy"
        )

    for path in iter_governed_files():
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        rel_path = path.relative_to(REPO_ROOT)
        if "_staging" in path.parts:
            errors.append(f"governed file unexpectedly lives under _staging: {rel_path}")
            continue
        if not meta_path.exists():
            errors.append(f"missing sidecar for {rel_path}")
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {meta_path.relative_to(REPO_ROOT)}: {exc}")
            continue

        missing = sorted(REQUIRED_META_FIELDS - meta.keys())
        if missing:
            errors.append(
                f"missing required fields in {meta_path.relative_to(REPO_ROOT)}: {', '.join(missing)}"
            )
            continue

        registry_id = meta["registry_id"]
        batch_id = meta["batch_id"]
        if registry_id not in registry:
            errors.append(
                f"{meta_path.relative_to(REPO_ROOT)} references unknown registry_id {registry_id}"
            )
            continue
        if batch_id not in registry[registry_id]:
            errors.append(
                f"{meta_path.relative_to(REPO_ROOT)} references batch_id {batch_id} "
                f"not present under registry_id {registry_id}"
            )

    errors.extend(report_live_duplicates())
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Source governance check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Source governance check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
