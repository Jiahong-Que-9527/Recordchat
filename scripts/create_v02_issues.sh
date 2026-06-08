#!/usr/bin/env bash
# Create v0.2 milestones and issues on GitHub. Idempotent only for milestones
# (skips if title exists). Run from repo root: bash scripts/create_v02_issues.sh
set -euo pipefail

REPO="Jiahong-Que-9527/Recordchat"

milestone_exists() {
  local title="$1"
  gh api "repos/${REPO}/milestones" --paginate \
    --jq ".[] | select(.title==\"${title}\") | .number" | head -1
}

ensure_milestone() {
  local title="$1"
  local desc="$2"
  local existing
  existing="$(milestone_exists "$title" || true)"
  if [[ -n "$existing" ]]; then
    echo "Milestone exists: $title (#$existing)"
    echo "$existing"
    return
  fi
  gh api "repos/${REPO}/milestones" \
    -f title="$title" \
    -f description="$desc" \
    -f state="open" \
    --jq .number
}

create_issue() {
  local title="$1"
  local milestone="$2"
  local body="$3"
  gh issue create --repo "$REPO" \
    --title "$title" \
    --milestone "$milestone" \
    --body "$body"
}

echo "Creating milestones..."

M21=$(ensure_milestone "v0.2.1 — Ontology-aware retrieval" \
  "Parse ONE Record ontology; entity-first retrieval; augment relationship map. See docs/v0.2_development_plan.md")

M23=$(ensure_milestone "v0.2.3 — Frontend upgrade" \
  "Vercel AI Chatbot template, streaming SSE, domain UI port.")

M24=$(ensure_milestone "v0.2.4 — Workflow orchestration" \
  "Connector abstraction, execution routing, and structured workflow output for ONE Record business flows.")

M25=$(ensure_milestone "v0.2.5 — RecordForge integration" \
  "Synthetic data generation via RecordForge connector after the orchestration layer lands.")

M26=$(ensure_milestone "v0.2.6 — AviationLakehouse narrative" \
  "Deferred ALH Bronze/Silver/Gold knowledge and domain mapping for architecture questions.")

echo "Creating issues..."

create_issue \
  "ADR: ontology-aware retrieval architecture" \
  "v0.2.1 — Ontology-aware retrieval" \
  "$(cat <<'EOF'
## Goal
Document the v0.2.1 ontology-aware retrieval design before implementation.

## Tasks
- [ ] Add `docs/adr/0002-ontology-aware-retrieval.md`
- [ ] Define `OntologyGraph` schema (classes, properties, relationships)
- [ ] Describe entity-first retrieval strategy (detect entity → boost/filter chunks)
- [ ] Clarify fallback to curated `one_record_schema.py` when parsing fails

## Files
- `docs/adr/0002-ontology-aware-retrieval.md`
- Cross-link from `docs/architecture.md`

## Acceptance criteria
- ADR reviewed and merged
- Next issues (#2–#6) can implement without ambiguity

## References
- `data/raw/ontology/one_record_core.ttl`
- `backend/app/domain/one_record_schema.py`
- `docs/v0.2_development_plan.md` § v0.2.1 step 1.1
EOF
)"

create_issue \
  "Implement ontology parser and OntologyGraph" \
  "v0.2.1 — Ontology-aware retrieval" \
  "$(cat <<'EOF'
## Goal
Parse the ONE Record ontology TTL into a queryable in-memory graph.

## Tasks
- [ ] Add `backend/app/domain/ontology_parser.py` (rdflib)
- [ ] Add `backend/app/domain/ontology_graph.py` with `get_related()`, `get_class()`, etc.
- [ ] Unit tests against `data/raw/ontology/one_record_core.ttl`

## Acceptance criteria
- Parser extracts OWL classes and object/datatype properties
- `OntologyGraph.get_related("Shipment")` returns parsed neighbors
- Tests pass offline (`uv run pytest`)

## Depends on
- ADR issue (design agreed)

## References
- `backend/app/rag/chunker.py` (`_chunk_ontology` already uses rdflib)
EOF
)"

create_issue \
  "Enrich chunk metadata from ontology during ingest" \
  "v0.2.1 — Ontology-aware retrieval" \
  "$(cat <<'EOF'
## Goal
Ensure ingested chunks carry `entity` and `related_entities` from ontology parsing.

## Tasks
- [ ] Update `rag/chunker.py` ontology strategy to set richer metadata
- [ ] Wire `OntologyGraph` into `rag/ingest.py` if needed
- [ ] Verify Qdrant payload stores entity fields (`rag/retriever.py`)

## Acceptance criteria
- After `POST /ingest`, Piece/Shipment chunks have correct `metadata.entity`
- `related_entities` populated from ontology where available

## Depends on
- OntologyGraph implementation

## References
- `backend/app/models/source.py` (`ChunkMetadata`)
EOF
)"

create_issue \
  "Entity-first retrieval strategy" \
  "v0.2.1 — Ontology-aware retrieval" \
  "$(cat <<'EOF'
## Goal
When the query mentions a ONE Record entity, prioritize chunks for that entity.

## Tasks
- [ ] Extend `Retriever.search()` or add wrapper in `rag/retriever.py`
- [ ] Use `one_record_schema.detect_entities()` + ontology graph for boosting
- [ ] Optional: metadata filter / score boost before `rerank()`

## Acceptance criteria
- Query `"What is a Piece?"` returns Piece ontology/API chunks in top-k
- Vector search still runs as baseline; entity boost is additive
- Offline mode unchanged

## Depends on
- OntologyGraph + enriched chunk metadata

## References
- `backend/app/rag/reranker.py` (may extend instead of no-op)
EOF
)"

create_issue \
  "Integrate ontology into pipeline and related_concepts" \
  "v0.2.1 — Ontology-aware retrieval" \
  "$(cat <<'EOF'
## Goal
Use parsed ontology for `related_concepts`; keep manual map as fallback.

## Tasks
- [ ] Update `domain/one_record_schema.py` to prefer `OntologyGraph`
- [ ] Update `rag/pipeline.py` `_related_concepts()` if needed
- [ ] Log when fallback to curated map is used

## Acceptance criteria
- Relationship questions show ontology-derived related concepts
- Manual `ONE_RECORD_RELATIONSHIPS` still works if ontology parse fails
- `/chat` contract unchanged

## Depends on
- Entity-first retrieval

## References
- `backend/app/rag/pipeline.py`
EOF
)"

create_issue \
  "Tests, eval, and docs for v0.2.1" \
  "v0.2.1 — Ontology-aware retrieval" \
  "$(cat <<'EOF'
## Goal
Lock in v0.2.1 quality with tests, eval, and documentation.

## Tasks
- [ ] Add pytest coverage for parser, graph, entity-first search
- [ ] Extend `data/eval/questions.yaml` with 2–3 ontology-focused questions
- [ ] Run `scripts/evaluate_rag.py` — no regression on existing 12 questions
- [ ] Update `docs/architecture.md`, `docs/demo_script.md`

## Acceptance criteria
- `uv run pytest` green
- Eval set passes
- Demo script mentions ontology-aware retrieval

## Depends on
- All other v0.2.1 issues

## References
- `docs/v0.2_development_plan.md` § v0.2.1 step 1.8–1.9
EOF
)"

create_issue \
  "Add AviationLakehouse knowledge document" \
  "v0.2.6 — AviationLakehouse narrative" \
  "$(cat <<'EOF'
## Goal
Add ingestible content explaining ONE Record → ALH Bronze/Silver/Gold mapping.

## Tasks
- [ ] Create `data/raw/one_record_docs/aviation_lakehouse.md`
- [ ] Cover: what ALH is, layer definitions, example ONE Record object landing
- [ ] Run ingest and verify chunks indexed

## Acceptance criteria
- Document is retrieved for ALH architecture questions
- Sources panel shows the new doc after ingest

## References
- `docs/v0.2_development_plan.md` § v0.2.6 step 6.1
EOF
)"

create_issue \
  "Implement alh_mapping domain module" \
  "v0.2.6 — AviationLakehouse narrative" \
  "$(cat <<'EOF'
## Goal
Structured Bronze / Silver / Gold mapping for ONE Record entities.

## Tasks
- [ ] Add `backend/app/domain/alh_mapping.py`
- [ ] Map key entities (Piece, Shipment, Waybill, TransportMovement, LogisticsEvent)
- [ ] Expose helpers for pipeline/prompt enrichment

## Acceptance criteria
- `get_alh_layers("Piece")` returns layer-specific explanations
- Module is independent of RAG plumbing (SPEC layering)

## Depends on
- ALH knowledge doc (for consistency)

## References
- `backend/app/domain/jsonld_generator.py` (template pattern)
EOF
)"

create_issue \
  "Extend classifier and prompts for ALH architecture questions" \
  "v0.2.6 — AviationLakehouse narrative" \
  "$(cat <<'EOF'
## Goal
Route and answer AviationLakehouse / platform architecture questions with grounded context.

## Tasks
- [ ] Extend `classify_query()` or add ALH keyword routing in `rag/pipeline.py`
- [ ] Enrich `rag/prompt.py` with ALH mapping context when relevant
- [ ] Supplement `domain/glossary.py` with ALH terms

## Acceptance criteria
- `"How could ONE Record data be connected to an AviationLakehouse?"` cites ALH doc
- Answer mentions Bronze, Silver, Gold with grounded sources

## Depends on
- `alh_mapping.py` + ALH knowledge doc

## References
- `docs/roadmap.md` v0.2.6
EOF
)"

create_issue \
  "Eval, glossary, and demo updates for ALH narrative" \
  "v0.2.6 — AviationLakehouse narrative" \
  "$(cat <<'EOF'
## Goal
Make ALH narrative demo-ready and testable.

## Tasks
- [ ] Add eval questions q013+ for ALH / platform narrative
- [ ] Update `docs/demo_script.md` and `docs/demo_cheat_sheet.md`
- [ ] Cross-link in `docs/architecture.md` future integration section

## Acceptance criteria
- `evaluate_rag.py` passes new ALH questions
- Demo flow #5 (AviationLakehouse) has stronger grounded answers

## Depends on
- ALH classifier/prompt work

## References
- `docs/v0.2_development_plan.md` § v0.2.6
EOF
)"

create_issue \
  "Define workflow connector abstraction and orchestration config" \
  "v0.2.4 — Workflow orchestration" \
  "$(cat <<'EOF'
## Goal
Establish the connector seam for real ONE Record business workflows and external tools.

## Tasks
- [ ] Add `backend/app/connectors/base.py` with `Connector` ABC
- [ ] Add orchestration-related env vars and placeholders for downstream connectors
- [ ] Write `docs/adr/0003-workflow-orchestration.md`

## Acceptance criteria
- Connector pattern documented and importable
- Missing downstream connector config → clear non-RAG error path defined

## References
- `docs/architecture.md` Future integration points
EOF
)"

create_issue \
  "Add workflow-oriented query routing and execution intent types" \
  "v0.2.4 — Workflow orchestration" \
  "$(cat <<'EOF'
## Goal
Detect requests that should trigger business workflow execution rather than plain QA.

## Tasks
- [ ] Add execution-oriented query types in `models/chat.py`
- [ ] Extend `classify_query()` in `rag/pipeline.py`
- [ ] Mirror new types in frontend API models

## Acceptance criteria
- Classifier routes orchestration prompts explicitly
- Existing query types unaffected (tests)

## Depends on
- Connector abstraction

## References
- `docs/roadmap.md` v0.2.4
EOF
)"

create_issue \
  "Implement RecordForge client (HTTP or stub)" \
  "v0.2.5 — RecordForge integration" \
  "$(cat <<'EOF'
## Goal
Call RecordForge (or a local stub) to produce synthetic JSON-LD payloads.

## Tasks
- [ ] Add `backend/app/connectors/recordforge.py`
- [ ] Stub mode: generate N objects from existing `jsonld_generator` templates
- [ ] HTTP mode: POST to `RECORDFORGE_URL` when configured
- [ ] Unit tests with mocked HTTP

## Acceptance criteria
- Returns `list[dict]` of valid JSON-LD objects
- Stub works offline with zero external deps

## Depends on
- Connector abstraction + query type

## References
- `backend/app/domain/jsonld_generator.py`
EOF
)"

create_issue \
  "Pipeline, frontend, and tests for RecordForge flow" \
  "v0.2.5 — RecordForge integration" \
  "$(cat <<'EOF'
## Goal
End-to-end synthetic data generation in `/chat` response.

## Tasks
- [ ] Pipeline branch: call RecordForge connector → `structured_output`
- [ ] Support array of JSON-LD in `ChatResponse` (or wrapper object)
- [ ] Update `JsonLdViewer.tsx` for multiple payloads
- [ ] Add eval questions + pytest; update demo script

## Acceptance criteria
- `"Generate 5 synthetic shipments with pieces"` returns structured JSON-LD list
- RecordForge unavailable → clear fallback message + single template
- `uv run pytest` green

## Depends on
- RecordForge client + query type

## References
- `docs/v0.2_development_plan.md` § v0.2.5
EOF
)"

create_issue \
  "Add LLM streaming and POST /chat/stream (SSE)" \
  "v0.2.3 — Frontend upgrade" \
  "$(cat <<'EOF'
## Goal
Stream answer tokens to the frontend; keep synchronous `/chat` for eval.

## Tasks
- [ ] Add `complete_stream()` to `LLMProvider` (+ local + OpenAI-compat + Claude)
- [ ] Add `answer_stream()` in `rag/pipeline.py`
- [ ] Add `POST /chat/stream` SSE endpoint in `api/chat.py`
- [ ] Event format: `token` chunks + final `metadata` (sources, query_type, structured_output)
- [ ] Tests for stream endpoint

## Acceptance criteria
- `curl -N POST /chat/stream` yields incremental tokens
- `/chat` JSON API unchanged

## References
- `docs/roadmap.md` v0.2.3 Streaming
EOF
)"

create_issue \
  "Scaffold frontend from Vercel AI Chatbot template" \
  "v0.2.3 — Frontend upgrade" \
  "$(cat <<'EOF'
## Goal
Replace v0.1 hand-rolled UI with Vercel AI Chatbot foundation.

## Tasks
- [ ] Adopt [vercel/chatbot](https://github.com/vercel/chatbot) structure
- [ ] Install Vercel AI SDK, shadcn/ui, AI Elements
- [ ] Preserve env: `NEXT_PUBLIC_API_BASE_URL`, VPS auto-detect from v0.1
- [ ] `npm run build` passes; Docker frontend image builds

## Acceptance criteria
- New chat layout renders with template components
- Logo/branding retained (RecordChat)
- Sidebar example questions ported or equivalent

## Depends on
- Can start in parallel; full wiring needs `/chat/stream`

## References
- https://vercel.com/templates/next.js/chatbot
EOF
)"

create_issue \
  "FastAPI adapter route for AI SDK useChat" \
  "v0.2.3 — Frontend upgrade" \
  "$(cat <<'EOF'
## Goal
Connect AI SDK `useChat` to RecordChat FastAPI backend (not Vercel AI Gateway).

## Tasks
- [ ] Add `frontend/app/api/chat/route.ts` adapter
- [ ] Proxy to backend `POST /chat/stream` (SSE → AI SDK stream protocol)
- [ ] Handle errors and CORS for VPS deployment

## Acceptance criteria
- `useChat` streams tokens from RecordChat RAG pipeline
- Works with `http://<vps>:3000` → `http://<vps>:8000` auto-detect

## Depends on
- `/chat/stream` backend + scaffolded frontend

## References
- `frontend/lib/api.ts` (v0.1 client to replace)
EOF
)"

create_issue \
  "Port domain UI: sources, related concepts, JSON-LD viewer" \
  "v0.2.3 — Frontend upgrade" \
  "$(cat <<'EOF'
## Goal
Keep RecordChat domain-specific UI in the new Vercel template layout.

## Tasks
- [ ] Port/adapt `Sources.tsx`, `JsonLdViewer.tsx`, query-type badge
- [ ] Show `related_concepts` tags after stream completes
- [ ] Render `structured_output` from metadata event

## Acceptance criteria
- Demo prompts show sources, related concepts, JSON-LD as in v0.1
- UI does not look like a generic ChatGPT clone

## Depends on
- AI SDK adapter route

## References
- `frontend/components/` (v0.1)
EOF
)"

create_issue \
  "Markdown rendering and UI polish" \
  "v0.2.3 — Frontend upgrade" \
  "$(cat <<'EOF'
## Goal
Improve answer readability and loading states.

## Tasks
- [ ] Add `react-markdown` + syntax highlighting for code blocks
- [ ] Streaming cursor / typing indicator via AI Elements
- [ ] Responsive layout; mobile-friendly chat

## Acceptance criteria
- JSON-LD and markdown answers render cleanly
- Loading state during stream is polished

## Depends on
- Domain UI port

## References
- https://elements.ai-sdk.dev
EOF
)"

create_issue \
  "Docker, README, and E2E demo verification for v0.2.3" \
  "v0.2.3 — Frontend upgrade" \
  "$(cat <<'EOF'
## Goal
Ship v0.2.3 with updated ops docs and verified demo flow.

## Tasks
- [ ] Update `docker-compose.yml`, `README.md`, `.env.example`
- [ ] Update `docs/demo_script.md`, `docs/demo_cheat_sheet.md`
- [ ] Run full demo 5-question flow on VPS
- [ ] Confirm `evaluate_rag.py` still uses sync `/chat`

## Acceptance criteria
- `docker compose up --build` works
- All 5 demo questions pass with streaming UI
- v0.2 development plan checklist for § v0.2.3 complete

## Depends on
- All other v0.2.3 issues

## References
- `docs/v0.2_development_plan.md`
EOF
)"

echo "Done. List issues:"
gh issue list --repo "$REPO" --limit 30
