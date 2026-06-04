#!/usr/bin/env python3
"""Ingest data/raw into Qdrant from the command line (SPEC Phase 10).

Usage:
    python scripts/ingest_docs.py [--reset] [--source-dir data/raw]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.rag.ingest import run_ingest  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest ONE Record docs into Qdrant.")
    ap.add_argument("--reset", action="store_true", help="Clear the collection first.")
    ap.add_argument("--source-dir", default=str(ROOT / "data" / "raw"))
    args = ap.parse_args()

    resp = run_ingest(source_dir=args.source_dir, reset=args.reset)
    print(resp.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
