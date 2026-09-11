# v0.2.6 ALH narrative — execution brief

**Status:** done (2026-09-11) on branch `feat/v0.2.6-alh-narrative`  
**Issues:** `#7` → `#8` → `#9` → `#10` (this order is mandatory)  
**Owner docs:** this file wins over the older GitHub issue bodies when they
disagree (those issues still point at a pre-v0.2.5 “v0.2.3” section).

This is **narrative + mapping + Q&A**. It is not a live lakehouse.

## 1. Goal

RecordChat should answer, with citations:

> How could ONE Record data land in an AviationLakehouse Bronze / Silver /
> Gold layout, and why would that matter?

The answer is a **RecordChat platform story**, not an IATA-official product
claim. Distinguish “ONE Record standard” vs “this project’s analytical
narrative” in both the source document and the prompt.

## 2. Non-goals (do not implement)

- No live AviationLakehouse cluster, Spark, Iceberg, or warehouse connector
- No writing generated JSON-LD into a lake or a ONE Record Server
- No new auth, sessions, or tracing
- No ingest of `_staging/` HTML/PDF dumps as a substitute for the ALH doc
- Do not reopen Retrieval Quality / RecordForge unless a regression appears

## 3. Why this slice exists

The ecosystem pitch is:

```text
ONE Record objects (operational, API, JSON-LD)
        ↓  (narrative mapping, not a pipeline we run)
AviationLakehouse Bronze → Silver → Gold
```

Without a grounded doc + mapping helper, the model will either invent a
medallion architecture or refuse usefully. v0.2.6 makes that story
**source-grounded and demoable**.

## 4. Architecture (how it plugs in)

Keep RAG as the path. ALH questions are **not** synthetic workflows.

```text
classify_query → architecture_question
  → rewrite (history) → hybrid retrieve (prefer docs, exclude examples)
  → rerank
  → prompt += alh_mapping context for detected entities
  → LLM
  → filter_cited_chunks
  → related_concepts (entities + Bronze/Silver/Gold as concepts if useful)
```

`structured_output` stays unused for ALH (no JSON-LD, no workflow_result).

## 5. Contract changes (additive only)

Add one QueryType value. Do **not** rename existing values.

| Layer | Change |
|---|---|
| `backend/app/models/chat.py` | `architecture_question = "architecture_question"` |
| `frontend/lib/api.ts` | add `"architecture_question"` to `QueryType` |
| Classifier | ALH / lakehouse / bronze-silver-gold markers (EN + 中文) |
| Prompt | `_TYPE_HINTS[architecture_question]` — use retrieved ALH doc; mark narrative vs official |
| Eval YAML | new questions with `expected_query_type: architecture_question` |

Classifier must run **before** generic `api_question` / `implementation_question`
so “lakehouse architecture” does not match on the word “server” / “api”.

Suggested markers (extend, don’t shrink):

```text
aviationlakehouse, aviation lakehouse, lakehouse, medallion,
bronze, silver, gold, analytical layer, bronze/silver/gold,
湖仓, 数据湖, 青铜, 白银, 黄金, 分析层
```

Require at least one ALH-specific marker (lakehouse / medallion / bronze|silver|gold
in an analytics sense). Do not classify a random “gold standard” ontology
question as ALH.

Search filter for `architecture_question`:

```text
chunk_types include: concept, general
exclude_chunk_types: example
```

## 6. Work order

### Step 6.1 — `#7` knowledge document

Create:

```text
data/raw/one_record_docs/aviation_lakehouse.md
data/raw/one_record_docs/aviation_lakehouse.md.meta.json
```

Sidecar (required fields):

```json
{
  "source_name": "RecordChat AviationLakehouse narrative",
  "version": "2026-09-narrative",
  "url": null,
  "document_type": "docs",
  "domain": "aviation_lakehouse",
  "ingested_at": "<ISO-8601 when you add it>"
}
```

Document outline (use these headings so chunker splits usefully):

1. **What AviationLakehouse is in this project** — analytical landing zone
   for ONE Record objects; RecordChat narrative, not an IATA spec.
2. **Relationship to ONE Record and RecordChat** — Chat explains; Server
   would hold live objects (out of scope); ALH would analyse copies.
3. **Bronze** — raw / near-raw JSON-LD LogisticsObjects as landed; append-style;
   preserve `@id` / `@type` / source system.
4. **Silver** — typed, validated, linked entities (Piece, Shipment, Waybill,
   TransportMovement, LogisticsEvent); conformed identifiers; still grain of
   the logistics object.
5. **Gold** — business-ready facts (shipment cycle time, piece dwell, event
   timelines) for analytics; aggregations, not the system of record.
6. **Example landing: Shipment + Piece** — one worked example of the same
   objects in each layer.
7. **What this project does not run** — no live ingest job in RecordChat.

Tone: educational, explicit about being a mapping narrative. Do not claim
IATA publishes ALH.

After writing: `make ingest` (or the project ingest command) and confirm
chunks exist. Add a backend test that the file is loadable / not skipped by
canonical filters (`document_type: docs` is fine; do not put it under
`ontology/` or a non-canonical spec family).

### Step 6.2 — `#8` `domain/alh_mapping.py`

Independent of RAG (same rule as `jsonld_generator.py`: no LLM, no HTTP).

Required API:

```python
from typing import Literal

LayerName = Literal["bronze", "silver", "gold"]

def mapped_entities() -> tuple[str, ...]:
    """Piece, Shipment, Waybill, TransportMovement, LogisticsEvent."""

def get_alh_layers(entity: str) -> list[dict]:
    """
    Return three dicts, one per layer, in bronze → silver → gold order:
      {"layer": "bronze"|"silver"|"gold", "summary": str, "example_landing": str}
    Unknown entity → [] (caller falls back to generic layer blurbs).
    """

def format_alh_context(query: str) -> str:
    """Plain text for the prompt: generic layers + per-detected-entity notes."""
```

Keep summaries short (2–4 sentences). They must agree with the markdown doc.

Tests (`backend/tests/test_alh_mapping.py`):

- `get_alh_layers("Piece")` has three layers, names bronze/silver/gold
- unknown entity returns `[]`
- `format_alh_context("How does a Shipment land in Gold?")` mentions Gold
  and Shipment

### Step 6.3 — `#9` classifier, prompt, glossary, pipeline hook

Files:

- `backend/app/rag/pipeline.py` — classify + `search_filter_for_query` +
  pass mapping text into prompt assembly
- `backend/app/rag/prompt.py` — type hint; optional extra block
  `AviationLakehouse mapping (project narrative):` when context is non-empty
- `backend/app/domain/glossary.py` — add terms: `AviationLakehouse`,
  `Bronze`, `Silver`, `Gold` (mark as RecordChat curated glossary)
- `frontend/lib/api.ts` — QueryType union
- `backend/app/models/chat.py` — enum

Tests:

- `classify_query("How could ONE Record data be connected to an AviationLakehouse?")`
  → `architecture_question`
- A control query (`What is a Piece?`) stays `concept_explanation`
- Prompt for architecture questions contains the mapping block when entities
  are present
- `/chat` still returns the same field names

Do **not** call RecordForge or skip RAG for ALH questions.

### Step 6.4 — `#10` eval + demo

Add at least these eval items to `data/eval/questions.yaml` (keep existing
ones). Gold retrieval should prefer the ALH doc / glossary, not example JSON:

```yaml
- id: alh_layers_overview
  question: How could ONE Record data be connected to an AviationLakehouse?
  expected_query_type: architecture_question
  expected_keywords: ["Bronze", "Silver", "Gold"]
  expected_source_families: ["AviationLakehouse", "lakehouse", "glossary"]

- id: alh_piece_landing
  question: How would a Piece land in Bronze, Silver, and Gold?
  expected_query_type: architecture_question
  expected_keywords: ["Piece", "Bronze", "Silver", "Gold"]
  expected_entities: ["Piece"]
  expected_source_families: ["AviationLakehouse", "lakehouse", "glossary"]

- id: alh_vs_system_of_record
  question: Why is an AviationLakehouse not a replacement for a ONE Record Server?
  expected_query_type: architecture_question
  expected_keywords: ["ONE Record Server", "Gold"]
  expected_source_families: ["AviationLakehouse", "lakehouse", "glossary"]
```

Demo:

- `docs/demo_script.md` — one prompt after the NE:ONE / workflow prompts
- `docs/demo_cheat_sheet.md` — same question, one-liner
- `docs/architecture.md` — future-integration bullet: ALH is narrative-only

Eval: `evaluate_rag.py` must **load** the new questions. Full metric pass
needs API keys; still add a unit test that `classify_query` matches
`expected_query_type` for the three ids (can load YAML in pytest).

## 7. Definition of done

- [x] `#7` ALH markdown + sidecar; governance script green
- [x] `#8` `alh_mapping.py` + tests
- [x] `#9` `architecture_question` end-to-end (backend + frontend type union)
- [x] `#10` three eval questions + demo prompt
- [x] Answers to the gold questions mention Bronze, Silver, and Gold and
      cite the ALH doc or glossary (spot-checked `/chat` after ingest)
- [x] No live lakehouse / Server write code
- [x] `uv run pytest -q` green; `npm run build` green
- [x] `project_plan.md` / `AGENTS.md` marked v0.2.6 done; next = v0.3 sketch only

## 8. Suggested `/chat` spot checks

1. `How could ONE Record data be connected to an AviationLakehouse?`
2. `How would a Piece land in Bronze, Silver, and Gold?`
3. `What is a Piece in ONE Record?` (regression — not ALH)
4. `Generate 5 synthetic shipments with pieces.` (regression — still
   local JSON-LD or RecordForge workflow, never ALH)

## 9. After this slice

Stop. Next scheduled work is **not** coding v0.3. See `docs/v03_sketch.md`.
Optional: P2 audit items in the playbook §6.
