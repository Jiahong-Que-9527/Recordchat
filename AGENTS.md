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

Later ecosystem (do not collapse into this repo’s current slice):

```text
RecordChat        = AI interface (this project)
RecordForge       = optional synthetic generator (HTTP when configured)
ONE Record Server = data exchange (not in v0.2.6; no auto-persist)
AviationLakehouse = Bronze/Silver/Gold narrative (v0.2.6, docs/mapping only)
```

## 2. Canonical documents (read order matters)

| Precedence | Document | What it is for |
|---|---|---|
| 1 | `docs/project_plan.md` | **Current status + next work.** Wins when docs disagree. |
| 2 | `docs/agent_execution_playbook.md` | How to execute any slice (read after the plan). |
| 3 | active slice brief (`docs/v03_execution_brief.md`) | Step-by-step when a slice is open. |
| 4 | `docs/architecture.md` | System architecture and design decisions. |
| 5 | `SPEC.md` | v0.1 API / data / module contracts. Still **binding** (field names, module boundaries, forbidden patterns). Additive enum values are allowed; renaming is not. |
| 6 | `docs/v0.2_development_plan.md` | Historical v0.2 task map. |
| 7 | `docs/data_source_plan.md` | Ingest / governance / canonical versions. |
| 8 | `docs/adr/*.md` | Recorded decisions. |
| 9 | `docs/roadmap.md` | Milestone narrative (may lag; plan + briefs win). |
| 10 | `docs/v03_sketch.md` | Unscheduled platform sketch. |

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
9. **Public surface is the Next.js frontend only.** Backend and Qdrant stay on
   the Docker network. `/ingest` is not a public API when `AUTH_MODE=enforced`.
   Do not put `user_id` on the `/chat` JSON body.

## 5. Current state (2026-09-13)

- Delivered: v0.1 baseline, Data Foundation (core pack), v0.2.1–v0.2.6,
  audit P0/P1 (AUD-01…AUD-07), Retrieval Quality `#27`–`#31`, RecordForge
  `#13` `#14`, Local / RecordForge generation toggle, ALH narrative `#7`–`#10`.
- Synthetic generation:
  - `synthetic_mode=local` (UI default) → template JSON-LD panel (`@graph` when
    multiple objects). No RecordForge, no Server write.
  - `synthetic_mode=recordforge` (or omitted on `/chat`) → `workflow_result`.
    Configured URL POSTs `/v1/generate`; missing URL → `blocked`; remote
    failure → `unavailable`. Never auto-persists to a ONE Record Server.
- ALH: `architecture_question` + `domain/alh_mapping.py` +
  `data/raw/one_record_docs/aviation_lakehouse.md` (narrative only).
- Frontend: `WorkflowViewer` for workflows; JSON-LD canvas for templates /
  `@graph`.
- **Current next:** v0.3.1 trial-user auth
  ([docs/v03_execution_brief.md](docs/v03_execution_brief.md)). Testers are
  trial users on our domain; same accounts promote `trial → user`. Optional P2
  (AUD-08, AUD-10, AUD-04 ModelPicker wiring, leftover `#23`) waits. AUD-09
  (pin Qdrant + auth) is in the v0.3.1 P0 list.
- Backend tests: 69 passing (`uv run pytest -q`) as of the ALH close.

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

### What landed in the 2026-09-10 RecordForge slice

| Area | Key modules |
|---|---|
| RecordForge HTTP `#13` | `connectors/recordforge.py` (POST `/v1/generate`, mockable `http_client`) |
| Frontend workflow `#14` | `components/WorkflowViewer.tsx`, `Canvas.tsx`, `Message.tsx`, `lib/api.ts` |
| Generation toggle | `ChatRequest.synthetic_mode`, `GenerationModePicker`, local `jsonld_generator` batch |
| ALH narrative `#7`–`#10` | `aviation_lakehouse.md`, `domain/alh_mapping.py`, `QueryType.architecture_question` |

## 6. Next work (in order)

1. **v0.3.1 trial-user auth** — [docs/v03_execution_brief.md](docs/v03_execution_brief.md)
   (AUTH-01 → AUTH-05). Do not persist chats. Do not publish backend/Qdrant.
2. **Optional P2 after that:** AUD-04 ModelPicker → `GET /models`, AUD-08
   shared ontology helper, AUD-10 CI fake-embedding fixture, leftover `#23`.
3. **v0.3 remainder** (memory, source admin, tracing) — [docs/v03_sketch.md](docs/v03_sketch.md)
   only with a new brief.

## 7. Definition of done — closed iterations

Retrieval Quality + audit P0/P1 + workflow `#32` (2026-09-09) and RecordForge
`#13` `#14` (2026-09-10) are **done**:

- [x] Versioned eval set + gold metrics that can go red
- [x] One live canonical version per source family
- [x] Vector-dominant reranker + hybrid retrieval + query-type filters
- [x] Follow-up entity carry-over + citation filter
- [x] Structured `workflow_result` for synthetic intents
- [x] Lightweight JSONL request diagnostics (AUD-07)
- [x] Backend tests green, `verify_source_governance.py` green
- [x] `RecordForgeConnector.execute_synthetic_generation` performs a real HTTP
      call when `RECORDFORGE_URL` is set
- [x] Remote failure → `availability=unavailable` + structured workflow result
      (never crash boot or `/chat`)
- [x] Unconfigured deployments keep blocked `workflow_result` behavior
- [x] Frontend presents workflow status / steps / artifacts without treating
      them as JSON-LD
- [x] Backend tests cover ready / unconfigured / unavailable; frontend build green

## 8. Definition of done — ALH `#7`–`#10` (closed)

See `docs/alh_execution_brief.md` §7.

- [x] Ingestible ALH markdown + sidecar; governance script green
- [x] `domain/alh_mapping.py` with bronze/silver/gold for core entities
- [x] Additive `QueryType.architecture_question` + classifier/prompt/glossary
- [x] Three eval questions + demo prompt
- [x] No live lakehouse or ONE Record Server write path
- [x] pytest green; frontend build green

## 8b. Definition of done — v0.3.1 trial-user auth (open)

See [docs/v03_execution_brief.md](docs/v03_execution_brief.md) §10.

Must keep:

- `/chat` field names unchanged; identity in internal JWT headers only
- `pipeline.py` the only orchestrator
- `AUTH_MODE=off` boots without Clerk
- backend and Qdrant never on a public hostname
- `/ingest` not reachable from the internet
- request logs omit raw user questions by default

## 9. How to verify your work

- Backend logic: `uv run pytest -q` from `backend/`.
- Frontend: `npm run build` from `frontend/` (CI does the same).
- Data governance: `uv run --project backend python scripts/verify_source_governance.py`.
- Retrieval: `uv run --project backend python scripts/evaluate_rag.py` (needs API keys).
- Request log: Docker writes `data/logs/requests.jsonl` (writable overlay).
  Tail with `make request-log`. Freeze a session with `make session-env`.
  Script: `docs/expert_session_script.md`.
- Full stack: `make up && make ingest`, then prompts from
  `docs/demo_cheat_sheet.md` / `docs/demo_script.md` (include the synthetic
  generation workflow prompt).