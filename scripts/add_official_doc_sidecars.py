#!/usr/bin/env python3
"""Add sidecar metadata to official ONE Record document extracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_ROOT = ROOT / "data" / "raw" / "one_record_docs"
INGESTED_AT = f"{date.today().isoformat()}T00:00:00Z"
ALLOWED_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".jsonld", ".ttl", ".owl", ".yaml", ".yml"}


@dataclass(frozen=True)
class BatchConfig:
    root: Path
    version: str
    url: str
    batch_id: str


BATCHES = (
    BatchConfig(
        root=RAW_ROOT / "spec_development",
        version="development",
        url="https://github.com/IATA-Cargo/ONE-Record/tree/master/Documentation_website/docs",
        batch_id="one_record_docs_development_repo_extract",
    ),
    BatchConfig(
        root=RAW_ROOT / "spec_2025_07" / "repo_release",
        version="2025-07",
        url="https://github.com/IATA-Cargo/ONE-Record/tree/master/2025-07-standard",
        batch_id="one_record_docs_2025_07_repo_release",
    ),
    BatchConfig(
        root=RAW_ROOT / "spec_2023_12" / "repo_release",
        version="2023-12",
        url="https://github.com/IATA-Cargo/ONE-Record/tree/master/2023-12-standard",
        batch_id="one_record_docs_2023_12_repo_release",
    ),
)


def document_type_for(path: Path) -> str:
    return {
        ".ttl": "ontology",
        ".owl": "ontology",
        ".json": "example",
        ".jsonld": "example",
        ".yaml": "api_spec",
        ".yml": "api_spec",
    }.get(path.suffix.lower(), "docs")


def source_name_for(path: Path) -> str:
    doc_type = document_type_for(path)
    return {
        "ontology": "ONE Record Official Ontology Extract",
        "example": "ONE Record Official Spec Example",
        "api_spec": "ONE Record Official API Spec Extract",
        "docs": "ONE Record Official Spec Document",
    }[doc_type]


def build_meta(path: Path, config: BatchConfig) -> dict[str, str]:
    return {
        "source_name": source_name_for(path),
        "version": config.version,
        "url": config.url,
        "document_type": document_type_for(path),
        "domain": "one_record",
        "publisher": "IATA-Cargo",
        "license": "MIT",
        "allowed_use": "retrieval,citation,educational_demo,internal_normalization",
        "registry_id": "official_one_record_repo",
        "batch_id": config.batch_id,
        "ingested_at": INGESTED_AT,
    }


def iter_ingestible_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".meta.json") or path.name == ".gitkeep":
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        files.append(path)
    return files


def main() -> int:
    written = 0
    skipped = 0

    for config in BATCHES:
        for path in iter_ingestible_files(config.root):
            meta_path = path.with_suffix(path.suffix + ".meta.json")
            if meta_path.exists():
                skipped += 1
                continue
            meta_path.write_text(
                json.dumps(build_meta(path, config), indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
            written += 1

    print(f"Official doc sidecars written: {written}")
    print(f"Official doc sidecars skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
