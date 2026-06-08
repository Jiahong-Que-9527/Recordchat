#!/usr/bin/env python3
"""Verify source-governance metadata for the curated core corpus."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "docs" / "data_sources_registry.yaml"

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


def validate() -> list[str]:
    errors: list[str] = []
    registry = load_registry()

    if "_staging" not in (REPO_ROOT / "backend" / "app" / "rag" / "loader.py").read_text(
        encoding="utf-8"
    ):
        errors.append("backend/app/rag/loader.py no longer explicitly skips _staging")
    if "_staging" not in (
        REPO_ROOT / "backend" / "app" / "domain" / "ontology_graph.py"
    ).read_text(encoding="utf-8"):
        errors.append("backend/app/domain/ontology_graph.py no longer explicitly skips _staging")

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
