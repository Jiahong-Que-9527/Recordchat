#!/usr/bin/env python3
"""Drop and recreate the Qdrant collection (SPEC Phase 10).

Usage:
    python scripts/reset_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.rag.retriever import get_retriever  # noqa: E402


def main() -> None:
    get_retriever().reset()
    print("Qdrant collection reset.")


if __name__ == "__main__":
    main()
