# AGENTS.md — RecordChat developer guidance

Entry point for coding agents working on RecordChat. Read this first, then the
canonical documents listed below in order. When documents disagree, the file
with higher precedence in the table wins.

## 1. What this is

RecordChat is a **citation-first RAG assistant** for IATA ONE Record (concepts,
ontology, JSON-LD, API, NE:ONE implementation). Next.js frontend → FastAPI
backend → Qdrant. It retrieves from reviewed public sources and answers with
citations; it does **not** fine-tune on third-party corpora and is **not** an
official IATA product.

Later ecosystem (deferred, do not build yet): RecordForge (synthetic data
generator), ONE Record Server (data exchange), AviationLakehouse (analytics).

## 2. Canonical documents (read order matters)

| Precedence | Document | What it is for |
|---|---|---|
| 1 | `docs/project_plan.md` | **Current status + next work.** The single source of truth when docs disagree. Contains the 2026-09 audit items (AUD-01…AUD-10) and the execution order. |
| 2 | `docs/architecture.md` | System architecture and key design decisions. |
| 3 | `SPEC.md` | v0.1 API / data / module contracts. Still **binding** (field names, module boundaries, forbidden patterns). |
| 4 | `docs/roadmap.md` | Milestone narrative and positioning. |
| 5 | `docs/data_source_plan.md` | Data acquisition, governance, **canonical source version policy** (§10). |
| 6 | `docs/adr/*.md` | Recorded decisions (provider abstraction, ontology-aware retrieval, connectors). |

Repo directories:

```
backend/    FastAPI service (app/ under it) — API, RAG pipeline, domain, tests
frontend/   Next.js + Tailwind chat UI (components/, app/, lib/)
scripts/    ingestion, eval, data-governance helpers
data/raw/   corpus (gitignored; local only) — _staging is NEVER ingested
docs/       plans, architecture, ADRs, compliance
```

## 3. Commands

```bash
make env       # create .env from .env.example, add LLM/EMBEDDING API keys
make up        # backend + frontend + qdrant (http://localhost:3000)
make ingest    # rebuild the Qdrant collection from data/raw + glossary
make test      # backend pytest suite
make logs      # tail all service logs
```

Backend (from `backend/`, uses uv):

```bash
uv run uvicorn app.main:app --reload --port 8000
uv run pytest -q
```

Frontend (from `frontend/`):

```bash
npm run dev
npm run build
```

Eval (from repo root, needs API keys):

```bash
uv run --project backend python scripts/evaluate_rag.py
```

## 4. Hard rules (do not violate)

1. **API contract stability.** `/chat` request/response field names are binding
   (SPEC §6, mirrored in `backend/app/models/chat.py` and
   `frontend/lib/api.ts`). Never rename fields.
2. **`pipeline.py` is the only orchestrator.** `api/*.py` handlers are thin;
   never write prompts / call LLMs / parse results in handlers.
3. **Provider abstraction.** LLM / Embedding / Retriever / Connector are ABCs
   behind factories in `core/`. Switching providers is configuration, never code.
   No provider may be hardcoded into business logic.
4. **JSON-LD comes from templates only.** `domain/jsonld_generator.py` owns
   structure; the LLM never emits complete JSON-LD.
5. **Data governance.** `data/raw/_staging/` is never ingested. Governed files
   carry `<file>.<ext>.meta.json` sidecars (`source_name`, `version`, `url`,
   `document_type`, `domain`, …). Do not ingest access-restricted or
   non-public content.
6. **Only one canonical live version per source family.** Do NOT add another
   copy of a document that already exists (see AUD-02 and
   `docs/data_source_plan.md` §10).
7. **The eval set is authored by us and MUST be versioned.** It lives at
   `data/eval/questions.yaml` (gitignored-exempt). Never leave the project with
   `scripts/evaluate_rag.py` unable to load it.
8. **Every phase must leave the project runnable and tested.** No credentials
   may be required to merely boot (graceful degradation instead).

## 5. Current state (2026-09-09)

- Delivered: v0.1 baseline, Data Foundation (core pack), v0.2.1 ontology-aware
  retrieval, v0.2.2 NE:ONE Q&A, v0.2.3 streaming frontend, audit P0
  (AUD-01…AUD-04), `#27` canonical pin, `#28` gold eval metrics.
- Partial: v0.2.4 workflow (Connector ABC + synthetic routing exist; `#32`
  remains). Retrieval Quality `#29`–`#31` still open.
- **Current slice: finish Retrieval Quality (`#29`–`#31`).** Do not start
  RecordForge / ALH until retrieval is clean and measurable.
- Backend tests: 39 passing (`uv run pytest -q`).

## 6. Next work (in order)

1. **Retrieval Quality remainder:** `#29` hybrid + filters → `#30` follow-up
   rewrite (AUD-06) → `#31` citation filter (AUD-05). AUD-07 request logging
   before expert interviews.
2. **v0.2.4 workflow** `#32` → **v0.2.5 RecordForge** `#13` `#14` →
   **v0.2.6 ALH narrative** `#7`–`#10`.
3. **v0.3 platform** (auth, sessions, source versioning, tracing, eval
   dashboard) — sketch only, not scheduled.
4. Optional UI follow-up: wire ModelPicker to `GET /models` (AUD-04 remainder).

## 7. Definition of done for the current iteration

Retrieval Quality + audit P0 are done when:

- [x] `data/eval/questions.yaml` exists (≥10 questions), is committed, and
      `evaluate_rag.py` runs without crashing.
- [x] A given class/property has **one** live canonical chunk (plus glossary),
      not 4–6 near-duplicates — checkable via `verify_source_governance.py` or
      an ingest-time duplicate report.
- [x] Retrieval metrics reported by `evaluate_rag.py` can go red (recall@5 /
      MRR / source-family accuracy, not just "answer non-empty").
- [x] Non-entity queries keep vector-ranked order; entity boost never drags an
      unrelated ontology chunk to position 1.
- [x] Config defaults are coherent with the docs; backend `GET /models` is the
      allowlist source of truth (frontend wiring still optional).
- [ ] `#27`–`#31` acceptance criteria from `docs/project_plan.md` §4 are met
      (`#27`/`#28` done; `#29`–`#31` remain).
- [x] Backend tests green, `verify_source_governance.py` green.

## 8. How to verify your work

- Backend logic: `uv run pytest -q` from `backend/`.
- Frontend: `npm run build` from `frontend/` (CI does the same).
- Data governance: `uv run --project backend python scripts/verify_source_governance.py`.
- Retrieval: `python scripts/evaluate_rag.py` (needs API keys; local eval can be
  gated on `data/eval/questions.yaml` existing).
- Full stack: `make up && make ingest`, then ask 2–3 questions from
  `docs/demo_cheat_sheet.md` or `docs/demo_script.md` and confirm cited sources.