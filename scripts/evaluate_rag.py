#!/usr/bin/env python3
"""RAG evaluation (SPEC section 9 / Phase 9).

Runs the eval question set through the pipeline and reports:
  - retrieval hit rate     (every question returns >=1 chunk)
  - source coverage        (answers carry source citations)
  - answer non-empty rate
  - JSON-LD validity        (for jsonld questions: structured_output is valid JSON)
  - query-type match rate   (for questions that declare expected_query_type)
  - keyword hit rate        (expected_keywords present in answer/structured output)

Runs against the providers configured in `.env` / environment variables.
RecordChat now requires external APIs for both LLM and embedding calls.

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
    query_type_total = 0
    query_type_match = 0
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

        expected_query_type = item.get("expected_query_type")
        if expected_query_type:
            query_type_total += 1
            if resp.query_type.value == expected_query_type:
                query_type_match += 1
            else:
                failures.append(
                    f"{item['id']}: expected query_type={expected_query_type}, got {resp.query_type.value}"
                )

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
    print(f"Query-type match   : {pct(query_type_match, query_type_total)} ({query_type_match}/{query_type_total})")
    print(f"Keyword hit rate   : {pct(kw_hit, kw_total)} ({kw_hit}/{kw_total})")

    if failures:
        print("\nNotes (keyword/JSON-LD gaps):")
        for f in failures:
            print(f"  - {f}")

    ok = retrieval_hits == n and nonempty == n and jsonld_valid == jsonld_total
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
