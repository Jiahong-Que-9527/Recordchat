# Agent execution playbook

How a coding agent should work in this repo. Read this after `AGENTS.md`
and `docs/project_plan.md`. Do not invent a new milestone order.

## 1. What RecordChat is (frozen)

RecordChat is a **citation-first RAG assistant** for IATA ONE Record. It is
not an official IATA product. It retrieves reviewed public sources and
answers with citations.

Ecosystem story (do not collapse these into one service):

```text
RecordChat        = AI interface for ONE Record knowledge   (this repo)
RecordForge       = optional synthetic-data generator       (HTTP when configured)
ONE Record Server = data exchange layer                     (not in this slice)
AviationLakehouse = analytical Bronze/Silver/Gold narrative (v0.2.6, docs only)
```

### Product decisions that later agents must not reverse

1. **Synthetic generation stops at display.** Local templates or RecordForge
   produce JSON-LD / workflow artifacts in the UI. RecordChat does **not**
   auto-POST objects into a ONE Record Server.
2. **Two generation modes** (`ChatRequest.synthetic_mode`):
   - `local` (frontend default) — `jsonld_generator` templates → JSON-LD panel
   - `recordforge` — Connector workflow; unconfigured → `blocked`; HTTP
     failure → `unavailable`
3. **JSON-LD structure comes from templates**, never from free-form LLM output.
4. **`pipeline.py` is the only orchestrator.** API handlers stay thin.
5. **`data/raw/_staging/` is never ingested.** One live canonical version per
   source family.
6. **`/chat` field names are a hard contract.** Additive optional fields are
   allowed; renaming is not.

## 2. Canonical documents (when they disagree)

| Precedence | Document | Use it for |
|---|---|---|
| 1 | `docs/project_plan.md` | Current status + next work |
| 2 | this playbook | How to execute a slice |
| 3 | the slice brief (e.g. `docs/alh_execution_brief.md`) | Step-by-step for that slice |
| 4 | `docs/architecture.md` + `docs/adr/*.md` | Design constraints |
| 5 | `SPEC.md` | `/chat` field names, module boundaries |
| 6 | `docs/v0.2_development_plan.md` | Historical v0.2 task map |
| 7 | `docs/data_source_plan.md` | Ingest / governance |
| 8 | `docs/roadmap.md` | Milestone narrative (may lag; plan wins) |
| 9 | GitHub issues | Ticket-level tasks; plan + brief win if they conflict |

`SPEC.md` is **not** the execution-order source after v0.1.

## 3. Current line (keep this in sync with project_plan)

- **Delivered:** v0.1 → Data Foundation core pack → v0.2.1–v0.2.6,
  Retrieval Quality `#27`–`#31`, audit AUD-01…AUD-07, workflow `#32`,
  RecordForge `#13` `#14`, Local / RecordForge UI toggle, ALH `#7`–`#10`.
- **Next slice:** none scheduled.
- **Unscheduled:** v0.3 sketch — `docs/v03_sketch.md` (only if the user asks).
- **Optional P2:** AUD-08, AUD-09, AUD-10, AUD-04 frontend `/models` wiring,
  leftover `#23`.

Do **not** start without an explicit ask:

- live ONE Record Server writes
- live AviationLakehouse
- auth / persisted sessions / tracing dashboards
- bulk ingest of `_staging/` or extra overlapping ontology copies

## 4. How to execute any slice

Work in this order. Skip a step only when the slice brief says so.

1. **Read** `AGENTS.md` → `project_plan.md` → this playbook → the slice brief.
2. **Confirm the slice is the current next work.** If the user asks to jump
   ahead (Server ingest, v0.3, ALH live), say so and keep the change optional
   or deferred unless they explicitly override the plan.
3. **Stay inside the brief’s file list.** Do not “while we’re here” rewrite
   retrieval, providers, or the `/chat` contract.
4. **Implement in the issue order** listed in the brief (`#7` then `#8`…).
5. **Add/adjust tests first or alongside**, never after “it looks fine”.
6. **Verify** with the commands in `AGENTS.md` §9:
   - `uv run pytest -q` from `backend/`
   - `npm run build` from `frontend/` if UI changed
   - `uv run --project backend python scripts/verify_source_governance.py`
     if ingest/data files changed
   - `uv run --project backend python scripts/evaluate_rag.py` if eval
     questions changed (needs API keys; do not fake a pass)
7. **Update the status docs in the same PR/slice:** `project_plan.md`,
   `AGENTS.md` current-state, the brief’s checklist, and GitHub issue
   comments. If `roadmap.md` still describes the old world, fix the status
   paragraph.
8. **Leave the project bootable without secrets.** Missing
   `RECORDFORGE_URL` / LLM keys must degrade, not crash.

## 5. Module boundaries (do not leak)

```text
api/*.py        parse request → call pipeline / ingest
rag/pipeline.py only orchestrator
rag/*           retrieve, chunk, prompt, rerank
domain/*        ONE Record knowledge, templates, mapping (no HTTP, no LLM)
connectors/*    optional external tools (RecordForge today)
core/*          config, provider factories, logging
models/chat.py  public JSON contract (mirror frontend/lib/api.ts)
```

Frontend: `frontend/lib/api.ts` mirrors `ChatRequest` / `ChatResponse`.
The BFF `frontend/app/api/chat/route.ts` forwards `model`, `history`, and
`synthetic_mode`.

## 6. Optional P2 (when idle, not instead of ALH)

| ID | What to do | Files | Done when |
|---|---|---|---|
| AUD-04 remainder | ModelPicker fetches `GET /models` instead of hardcoding | `frontend/components/ModelPicker.tsx`, BFF or health proxy | picker list == backend allowlist |
| AUD-08 | One `_is_ontology_query` helper; stop duplicating classify rules | `rag/pipeline.py`, `rag/reranker.py` | single function, tests still pass, Chinese markers kept |
| AUD-09 | Pin `qdrant/qdrant:<version>` in compose; note unauthenticated local posture | `docker-compose.yml`, README | image not `:latest` |
| AUD-10 | CI-safe fake-embedding retrieval fixture with gold chunks | `backend/tests/` + tiny fixture corpus | pytest asserts recall/canonical rank with no network |
| `#23` | Manual overview/PDF/community pack via `_staging` → normalized `data/raw` | `docs/data_addition_workflow.md` | key narrative sources ingestible; `_staging` still excluded |

## 7. Expert interviews (`project_plan.md` §4.6)

Discovery, **not** a coding slice. Do not block ALH on it. If you run them,
freeze revision / model / corpus first and use `RECORDCHAT_REQUEST_LOG`.

## 8. After finishing a slice

Update, in order:

1. Slice brief checkboxes
2. `docs/project_plan.md` header + milestone board + “next work”
3. `AGENTS.md` current state + next-work list + DoD
4. GitHub issues (comment + close when acceptance is met)
5. `docs/roadmap.md` status bullets if they would otherwise lie

Then stop. Do not start the next milestone unless the user asks or the plan
already names it as current next.
