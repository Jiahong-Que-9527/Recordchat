#!/usr/bin/env python3
"""RAG evaluation (SPEC section 9 / Phase 9 / Retrieval Quality #28).

Runs the eval question set through the pipeline and reports:
  - retrieval hit rate     (every question returns >=1 chunk)
  - source coverage        (answers carry source citations)
  - answer non-empty rate
  - JSON-LD validity        (for jsonld questions: structured_output is valid JSON)
  - query-type match rate   (for questions that declare expected_query_type)
  - keyword hit rate        (expected_keywords present in answer/structured output)
  - entity recall@5 / MRR   (gold entities in retrieved chunk metadata)
  - source-family accuracy  (expected_source_families vs source_name)
  - canonical-version hit   (expected_canonical_version in top-k)

Runs against the providers configured in `.env` / environment variables.
RecordChat now requires external APIs for both LLM and embedding calls.

Usage:
    uv run python ../scripts/evaluate_rag.py            # from backend/
    python scripts/evaluate_rag.py                      # from repo root (with deps)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

# Make the backend package importable regardless of CWD.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.rag.eval_metrics import (  # noqa: E402
    DEFAULT_TOP_K,
    canonical_version_hit,
    entity_recall_at_k,
    mean_reciprocal_rank,
    source_family_hit,
)
from app.rag.ingest import run_ingest  # noqa: E402
from app.rag.pipeline import _prepare_answer_context, answer  # noqa: E402
from app.rag.retriever import get_retriever  # noqa: E402

EVAL_FILE = ROOT / "data" / "eval" / "questions.yaml"
TOP_K = DEFAULT_TOP_K


def _contains_keywords(text: str, keywords: list[str]) -> tuple[int, int]:
    low = text.lower()
    hits = sum(1 for k in keywords if k.lower() in low)
    return hits, len(keywords)


def _load_questions() -> list[dict]:
    if not EVAL_FILE.exists():
        raise SystemExit(
            f"Eval set missing: {EVAL_FILE}\n"
            "AUD-01 / SPEC Phase 9 require data/eval/questions.yaml to be "
            "versioned in the repo. Restore it before running evaluate_rag.py."
        )
    raw = yaml.safe_load(EVAL_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise SystemExit(
            f"Eval set at {EVAL_FILE} must be a non-empty YAML list of questions."
        )
    return raw


def main() -> int:
    questions = _load_questions()
    print(f"Loaded {len(questions)} eval questions from {EVAL_FILE}")

    print("Ingesting knowledge base (glossary + data/raw)…")
    run_ingest(source_dir=str(ROOT / "data" / "raw"), reset=True)
    retriever = get_retriever()

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

    entity_questions = 0
    entity_recall_sum = 0.0
    mrr_sum = 0.0
    family_total = 0
    family_hits = 0
    version_total = 0
    version_hits = 0

    failures: list[str] = []
    retrieval_failures: list[str] = []

    for item in questions:
        qid = item["id"]
        question = item["question"]
        resp = answer(question, retriever=retriever)
        _, chunks, _ = _prepare_answer_context(question, retriever)

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
                    f"{qid}: expected query_type={expected_query_type}, got {resp.query_type.value}"
                )

        if item.get("expects_jsonld"):
            jsonld_total += 1
            try:
                assert resp.structured_output is not None
                json.dumps(resp.structured_output)
                jsonld_valid += 1
            except (AssertionError, TypeError):
                failures.append(f"{qid}: invalid/missing JSON-LD")

        hits, total = _contains_keywords(haystack, item.get("expected_keywords", []))
        kw_hit += hits
        kw_total += total
        if total and hits < total:
            missing = [
                k for k in item["expected_keywords"] if k.lower() not in haystack.lower()
            ]
            failures.append(f"{qid}: missing keywords {missing}")

        expected_entities = item.get("expected_entities") or []
        if expected_entities:
            entity_questions += 1
            recall = entity_recall_at_k(chunks, expected_entities, TOP_K)
            mrr = mean_reciprocal_rank(chunks, expected_entities)
            entity_recall_sum += recall
            mrr_sum += mrr
            if recall <= 0:
                retrieval_failures.append(
                    f"{qid}: entity recall@{TOP_K}=0 (expected {expected_entities})"
                )

        families = item.get("expected_source_families") or []
        if families:
            family_total += 1
            if source_family_hit(chunks, families, TOP_K):
                family_hits += 1
            else:
                names = [c.metadata.source_name for c in chunks[:TOP_K]]
                retrieval_failures.append(
                    f"{qid}: source-family miss (expected {families}, got {names})"
                )

        version = item.get("expected_canonical_version")
        if version:
            version_total += 1
            if canonical_version_hit(chunks, version, TOP_K):
                version_hits += 1
            else:
                versions = [c.metadata.version for c in chunks[:TOP_K]]
                retrieval_failures.append(
                    f"{qid}: canonical-version miss "
                    f"(expected {version}, got {versions})"
                )

    def pct(a: float, b: float) -> str:
        return f"{(100 * a / b):.0f}%" if b else "n/a"

    print("\n=== RecordChat RAG evaluation ===")
    print(f"Retrieval hit rate : {pct(retrieval_hits, n)} ({retrieval_hits}/{n})")
    print(f"Source coverage    : {pct(source_cov, n)} ({source_cov}/{n})")
    print(f"Answer non-empty   : {pct(nonempty, n)} ({nonempty}/{n})")
    print(f"JSON-LD validity   : {pct(jsonld_valid, jsonld_total)} ({jsonld_valid}/{jsonld_total})")
    print(
        f"Query-type match   : {pct(query_type_match, query_type_total)} "
        f"({query_type_match}/{query_type_total})"
    )
    print(f"Keyword hit rate   : {pct(kw_hit, kw_total)} ({kw_hit}/{kw_total})")
    print(
        f"Entity recall@{TOP_K}  : "
        f"{pct(entity_recall_sum, entity_questions)} "
        f"(mean over {entity_questions} questions)"
    )
    if entity_questions:
        print(f"Entity MRR         : {(mrr_sum / entity_questions):.3f}")
    else:
        print("Entity MRR         : n/a")
    print(f"Source-family acc  : {pct(family_hits, family_total)} ({family_hits}/{family_total})")
    print(
        f"Canonical-version  : {pct(version_hits, version_total)} "
        f"({version_hits}/{version_total})"
    )

    if failures:
        print("\nNotes (keyword/query-type/JSON-LD gaps):")
        for item in failures:
            print(f"  - {item}")

    if retrieval_failures:
        print("\nRetrieval gold failures (#28):")
        for item in retrieval_failures:
            print(f"  - {item}")

    ok = (
        retrieval_hits == n
        and nonempty == n
        and jsonld_valid == jsonld_total
        and not retrieval_failures
    )
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
