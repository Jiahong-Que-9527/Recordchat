#!/usr/bin/env python3
"""RAG evaluation (SPEC section 9 / Phase 9).

Runs the eval question set through the pipeline and reports:
  - retrieval hit rate     (every question returns >=1 chunk)
  - source coverage        (answers carry source citations)
  - answer non-empty rate
  - JSON-LD validity        (for jsonld questions: structured_output is valid JSON)
  - keyword hit rate        (expected_keywords present in answer/structured output)

Runs fully offline with the local providers; no API key required. Set
LLM_PROVIDER / EMBEDDING_PROVIDER to evaluate real models.

Usage:
    uv run python ../scripts/evaluate_rag.py            # from backend/
    python scripts/evaluate_rag.py                      # from repo root (with deps)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

# Make the backend package importable regardless of CWD.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("EMBEDDING_DIM", "256")

from app.rag.ingest import run_ingest  # noqa: E402
from app.rag.pipeline import answer  # noqa: E402

EVAL_FILE = ROOT / "data" / "eval" / "questions.yaml"


def _contains_keywords(text: str, keywords: list[str]) -> tuple[int, int]:
    low = text.lower()
    hits = sum(1 for k in keywords if k.lower() in low)
    return hits, len(keywords)


def main() -> int:
    questions = yaml.safe_load(EVAL_FILE.read_text())
    print(f"Loaded {len(questions)} eval questions from {EVAL_FILE}")

    print("Ingesting knowledge base (glossary + data/raw)…")
    run_ingest(source_dir=str(ROOT / "data" / "raw"), reset=True)

    n = len(questions)
    retrieval_hits = 0
    source_cov = 0
    nonempty = 0
    jsonld_total = 0
    jsonld_valid = 0
    kw_hit = 0
    kw_total = 0
    failures: list[str] = []

    for item in questions:
        resp = answer(item["question"])
        haystack = resp.answer
        if resp.structured_output:
            haystack += "\n" + json.dumps(resp.structured_output)

        if resp.sources:
            retrieval_hits += 1
            source_cov += 1
        if resp.answer.strip():
            nonempty += 1

        if item.get("expects_jsonld"):
            jsonld_total += 1
            try:
                assert resp.structured_output is not None
                json.dumps(resp.structured_output)
                jsonld_valid += 1
            except (AssertionError, TypeError):
                failures.append(f"{item['id']}: invalid/missing JSON-LD")

        hits, total = _contains_keywords(haystack, item.get("expected_keywords", []))
        kw_hit += hits
        kw_total += total
        if total and hits < total:
            missing = [k for k in item["expected_keywords"] if k.lower() not in haystack.lower()]
            failures.append(f"{item['id']}: missing keywords {missing}")

    def pct(a: int, b: int) -> str:
        return f"{(100 * a / b):.0f}%" if b else "n/a"

    print("\n=== RecordChat RAG evaluation ===")
    print(f"Retrieval hit rate : {pct(retrieval_hits, n)} ({retrieval_hits}/{n})")
    print(f"Source coverage    : {pct(source_cov, n)} ({source_cov}/{n})")
    print(f"Answer non-empty   : {pct(nonempty, n)} ({nonempty}/{n})")
    print(f"JSON-LD validity   : {pct(jsonld_valid, jsonld_total)} ({jsonld_valid}/{jsonld_total})")
    print(f"Keyword hit rate   : {pct(kw_hit, kw_total)} ({kw_hit}/{kw_total})")

    if failures:
        print("\nNotes (keyword/JSON-LD gaps — expected with the offline local LLM):")
        for f in failures:
            print(f"  - {f}")

    # Hard gates that must pass even offline.
    ok = retrieval_hits == n and nonempty == n and jsonld_valid == jsonld_total
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
