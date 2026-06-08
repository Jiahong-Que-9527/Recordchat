#!/usr/bin/env python3
"""Add sidecar metadata to NE:ONE API/config extracts."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TARGET_ROOT = ROOT / "data" / "raw" / "api_specs" / "ne_one"
INGESTED_AT = f"{date.today().isoformat()}T00:00:00Z"
ALLOWED_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".jsonld", ".ttl", ".owl", ".yaml", ".yml"}


def document_type_for(path: Path) -> str:
    if "ontologies" in path.parts or path.suffix.lower() in {".ttl", ".owl"}:
        return "ontology"
    return {
        ".json": "api_spec",
        ".yaml": "api_spec",
        ".yml": "api_spec",
    }.get(path.suffix.lower(), "docs")


def source_name_for(path: Path) -> str:
    if "ontologies" in path.parts:
        return "NE:ONE ontology extract"
    if "docker_compose" in path.parts:
        return "NE:ONE deployment and config extract"
    return "NE:ONE API/config extract"


def build_meta(path: Path) -> dict[str, str]:
    return {
        "source_name": source_name_for(path),
        "version": "2026-06-07_repo_snapshot",
        "url": "https://git.openlogisticsfoundation.org/wg-digitalaircargo/ne-one",
        "document_type": document_type_for(path),
        "domain": "one_record_implementation",
        "publisher": "Open Logistics Foundation",
        "license": "Open Logistics Foundation License 1.3",
        "allowed_use": "retrieval,citation,educational_demo,internal_normalization",
        "registry_id": "ne_one_repo_and_docs",
        "batch_id": "ne_one_api_config_extract",
        "ingested_at": INGESTED_AT,
    }


def main() -> int:
    written = 0
    skipped = 0

    for path in sorted(TARGET_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".meta.json") or path.name == ".gitkeep":
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.exists():
            skipped += 1
            continue

        meta_path.write_text(
            json.dumps(build_meta(path), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        written += 1

    print(f"NE:ONE API/config sidecars written: {written}")
    print(f"NE:ONE API/config sidecars skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
