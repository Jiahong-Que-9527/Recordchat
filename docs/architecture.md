# RecordChat Architecture

## Overview

RecordChat is a retrieval-augmented (RAG) assistant for IATA ONE Record. A
Next.js frontend talks to a FastAPI backend over a small JSON contract. The
backend retrieves source-grounded context from Qdrant, assembles a prompt, calls
a (provider-abstracted) LLM, and enriches the answer with domain tools
(relationship map + JSON-LD templates).

Current project priority (2026-09-13):

- `v0.1` through `v0.2.6` are delivered, including Retrieval Quality, audit
  P0/P1 (AUD-01…AUD-07), RecordForge HTTP, Local/RecordForge UI toggle, and
  ALH narrative (`architecture_question`)
- retrieval is hybrid (dense + BM25-lite RRF) with canonical-version filtering,
  follow-up rewrite, and citation filtering
- synthetic intents skip RAG. `synthetic_mode=local` uses JSON-LD templates
  (JSON-LD / `@graph` panel). `synthetic_mode=recordforge` (API default) uses
  the Connector: HTTP when `RECORDFORGE_URL` is set, else `blocked`; remote
  failure → `unavailable`. **No auto-persist to a ONE Record Server.**
- frontend: `WorkflowViewer` for `kind=workflow_result`; JSON-LD canvas
  otherwise
- **next**: v0.3.1 trial-user auth ([v03_execution_brief.md](v03_execution_brief.md))

```
┌──────────────────────────── Frontend (Next.js) ────────────────────────────┐
│  Sidebar (examples/concepts) · Chat · Sources · JSON-LD viewer              │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ POST /chat  (lib/api.ts)
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                              Backend (FastAPI)                                │
│  api/{health,chat,ingest,models} ── thin handlers, no business logic          │
│                                                                               │
│  rag/pipeline.answer()  ── the only orchestrator                              │
│    1. classify_query(q)            -> QueryType                               │
│    1b. synthetic + local -> jsonld_generator batch -> JSON-LD / @graph        │
│    1c. synthetic + recordforge -> connectors.orchestration -> workflow_result │
│    2. rewrite_query_for_retrieval(q, history)                                 │
│    3. retriever.search(q, top_k, filter) -> Chunk[]  (dense + lexical RRF)    │
│    4. rerank(q, chunks)            -> Chunk[]   (vector-dominant boosts)      │
│    5. prompt.build_user_prompt()   -> str                                     │
│    6. llm.complete(system, user)   -> answer                                  │
│    7. filter_cited_chunks(answer, chunks) -> sources                          │
│    8. domain enrich: jsonld_generator / related_concepts                      │
│    9. request_log (AUD-07) + assemble ChatResponse                            │
└───────┬───────────────────────────┬───────────────────────────┬──────────────┘
        │                           │                           │
   core/llm.py                core/embeddings.py          rag/retriever.py
   (LLMProvider)              (EmbeddingProvider)     (hybrid Retriever/Qdrant)
```

Public trial (v0.3.1 — [v03_execution_brief.md](v03_execution_brief.md)):

```
Internet → Cloudflare (TLS / WAF / Tunnel) → Next.js :3000
              Clerk session cookie, BFF /api/chat
                    internal JWT (not /chat JSON)
                         → FastAPI :8000 (private)
                         → Qdrant :6333 (private + API key)
```

`plan=trial|user` (quotas) and `role=user|admin` (admin APIs). JWT is identity
only; SQLite is the source of truth for plan/role/status. Quotas and model
allowlists are enforced in the BFF and handler `Depends`; `pipeline.py` then
runs as today.

## Ingestion pipeline

```
data/raw/**            loader.py            chunker.py              retriever.py
  *.ttl/.owl    ─▶  RawDocument[]  ─▶  domain-aware Chunk[]  ─▶  embed ─▶ Qdrant
  *.md                                  (by class/endpoint/
  *.yaml (openapi)                       heading/payload)
  *.jsonld
  + curated glossary (always included → graceful degradation)
```

`rag/ingest.run_ingest()` always merges the curated `domain/glossary.py`
entries with whatever is in `data/raw/`, so the knowledge base is never empty.

That said, "never empty" is not the same thing as "clean enough to rank". The
core pack is in place, but overlapping ontology copies still share the index.
Retrieval Quality (`#27`–`#31`) is the next ingest/ranking work, not another
feature branch.

## Key design decisions

### 1. Provider abstraction (LLM + Embedding + Retriever)
`LLMProvider`, `EmbeddingProvider`, and `Retriever` are abstract base classes.
Factories in `core/` choose the concrete implementation from env vars. Switching
between Qwen / OpenAI / Claude is configuration, not code. See
[adr/0001-provider-abstraction.md](adr/0001-provider-abstraction.md).

### 2. API-first model integration
RecordChat now expects externally hosted LLM and embedding providers. Qdrant can
still run in-process via `QDRANT_URL=:memory:` or point to a remote server, but
model inference itself is API-backed and must be configured explicitly.

### 3. Domain logic separated from RAG
`domain/` (relationship map, JSON-LD templates, glossary) is independent of the
RAG plumbing. JSON-LD structures come from **templates**, not free-form LLM
output, so they are always valid; the LLM only explains them.

### 4. Thin API handlers
`api/*.py` only parse the request and call `pipeline.answer()` / `run_ingest()`.
All orchestration lives in `rag/pipeline.py`.

## Data contract

The `/chat` request/response shape is the single integration contract between
frontend and backend; see [SPEC.md](../SPEC.md) section 6 and
`backend/app/models/chat.py` (`models/chat.py` and `frontend/lib/api.ts` mirror
each other).

## Ontology-aware retrieval (v0.2.1)

See [adr/0002-ontology-aware-retrieval.md](adr/0002-ontology-aware-retrieval.md).

```
data/raw/**/*.ttl  ->  ontology_parser  ->  OntologyGraph (in-memory)
                              |
ingest/chunker     ->  chunk.metadata.related_entities
pipeline           ->  vector pool (top_k * 3)  ->  reranker entity boost  ->  top_k
one_record_schema  ->  ontology neighbors first, manual map fallback
```

## Future integration points

Recommended order (current):

1. **v0.2.6 ALH narrative** — **done** ([alh_execution_brief.md](alh_execution_brief.md))
2. **v0.3.1 trial-user auth** — **open** ([v03_execution_brief.md](v03_execution_brief.md);
   [adr/0004-trial-user-auth.md](adr/0004-trial-user-auth.md)). Public hostname
   hits Next.js only; Clerk session on the BFF; internal JWT to FastAPI;
   `plan=trial|user`; backend and Qdrant stay private.
3. **v0.3 remainder** — sketch only ([v03_sketch.md](v03_sketch.md) §3.2–3.7)

- **RecordForge** (done, optional): HTTP `/v1/generate` or local templates.
  Output is displayed; not written to a Server.
- **AviationLakehouse** (done, narrative-only): `architecture_question` +
  `domain/alh_mapping.py` + `data/raw/one_record_docs/aviation_lakehouse.md`.
  No live lakehouse cluster.
- **ONE Record Server** (later, optional connector): live objects / persist
  only if product un-freezes auto-write (v0.3 §3.6).

The `Retriever` abstraction remains the seam for remote/live object lookup.
The `Connector` abstraction is the seam for optional workflow integrations
(RecordForge today; Server persist only if explicitly scheduled).
