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

Later ecosystem: RecordForge HTTP client is the **next** slice (`#13` `#14`);
ONE Record Server and AviationLakehouse stay deferred after that.

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

## 5. Current state (2026-09-09 EOD)

- Delivered: v0.1 baseline, Data Foundation (core pack), v0.2.1–v0.2.4,
  audit P0/P1 (AUD-01…AUD-07), Retrieval Quality `#27`–`#31`.
- Synthetic generation already returns a structured `workflow_result` via
  `structured_output` (plan / blocked / artifacts). **Live HTTP to RecordForge
  is not implemented yet** — that is `#13`.
- **Current next:** v0.2.5 RecordForge HTTP client (`#13`) + frontend workflow
  rendering (`#14`). Do **not** start ALH (`#7`–`#10`) or v0.3 platform work
  until RecordForge is optionally callable and still degrades when unconfigured.
- Backend tests: 56 passing (`uv run pytest -q`).

### What landed in the 2026-09-09 slice (so agents do not redo it)

| Area | Key modules |
|---|---|
| Canonical versions | `rag/canonical.py`, `loader.py`, `ontology_graph.py`, `verify_source_governance.py` |
| Reranker | `rag/reranker.py` (vector-dominant boosts) |
| Models API | `GET /models` in `api/health.py` |
| Eval | `data/eval/questions.yaml`, `rag/eval_metrics.py`, `scripts/evaluate_rag.py` |
| Hybrid retrieval | `rag/lexical.py`, `rag/retriever.py`, query-type filters in `pipeline.py` |
| Follow-ups | `ChatRequest.history`, `rewrite_query_for_retrieval`, BFF `frontend/app/api/chat/route.ts` |
| Citations | `filter_cited_chunks` in `pipeline.py` |
| Workflow `#32` | `connectors/workflow.py`, `connectors/recordforge.py`, `connectors/orchestration.py` |
| Request log | `core/request_log.py` (`RECORDCHAT_REQUEST_LOG`) |

## 6. Next work (in order)

1. **v0.2.5 RecordForge** — `#13` (HTTP client behind `RecordForgeConnector`,
   graceful degrade when URL missing / remote fails) then `#14` (frontend
   render of `workflow_result`, not only the JSON-LD canvas path).
2. **v0.2.6 ALH narrative** `#7`–`#10` (docs / mapping only).
3. **v0.3 platform** (auth, sessions, source versioning, tracing, eval
   dashboard) — sketch only, not scheduled.
4. Optional / P2 (do not block RecordForge):
   - wire ModelPicker to `GET /models` (AUD-04 remainder)
   - AUD-08 shared `_is_ontology_query` helper
   - AUD-09 pin Qdrant image
   - AUD-10 CI-safe fake-embedding retrieval fixture

## 7. Definition of done — closed iteration

Retrieval Quality + audit P0/P1 + workflow `#32` (2026-09-09) are **done**:

- [x] Versioned eval set + gold metrics that can go red
- [x] One live canonical version per source family
- [x] Vector-dominant reranker + hybrid retrieval + query-type filters
- [x] Follow-up entity carry-over + citation filter
- [x] Structured `workflow_result` for synthetic intents (no live HTTP yet)
- [x] Lightweight JSONL request diagnostics (AUD-07)
- [x] Backend tests green, `verify_source_governance.py` green

## 8. Definition of done — next iteration (RecordForge `#13` `#14`)

- [ ] `RecordForgeConnector.execute_synthetic_generation` performs a real HTTP
      call when `RECORDFORGE_URL` is set
- [ ] Remote failure → `availability=unavailable` + structured workflow result
      (never crash boot or `/chat`)
- [ ] Unconfigured deployments keep today's blocked `workflow_result` behavior
- [ ] Frontend can present workflow status / steps / artifacts without treating
      them as JSON-LD
- [ ] Backend tests cover ready / unconfigured / unavailable; frontend build green

## 9. How to verify your work

- Backend logic: `uv run pytest -q` from `backend/`.
- Frontend: `npm run build` from `frontend/` (CI does the same).
- Data governance: `uv run --project backend python scripts/verify_source_governance.py`.
- Retrieval: `uv run --project backend python scripts/evaluate_rag.py` (needs API keys).
- Request log: set `RECORDCHAT_REQUEST_LOG=data/logs/requests.jsonl` (under
  gitignored `data/`) or leave default `stdout`.
- Full stack: `make up && make ingest`, then prompts from
  `docs/demo_cheat_sheet.md` / `docs/demo_script.md` (include the synthetic
  generation workflow prompt).