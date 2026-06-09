# RecordChat Architecture

## Overview

RecordChat is a retrieval-augmented (RAG) assistant for IATA ONE Record. A
Next.js frontend talks to a FastAPI backend over a small JSON contract. The
backend retrieves source-grounded context from Qdrant, assembles a prompt, calls
a (provider-abstracted) LLM, and enriches the answer with domain tools
(relationship map + JSON-LD templates).

Current project priority:

- `v0.1` is already demoable
- the next step is expanding the knowledge base from the current minimal subset
  to the broader official ONE Record + NE:ONE source pack
- downstream features should follow that, not outrun it

```
┌──────────────────────────── Frontend (Next.js) ────────────────────────────┐
│  Sidebar (examples/concepts) · Chat · Sources · JSON-LD viewer              │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ POST /chat  (lib/api.ts)
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                              Backend (FastAPI)                                │
│  api/{health,chat,ingest}  ── thin handlers, no business logic                │
│                                                                               │
│  rag/pipeline.answer()  ── the only orchestrator                              │
│    1. classify_query(q)            -> QueryType                               │
│    2. retriever.search(q, top_k)   -> Chunk[]   (Qdrant)                       │
│    3. rerank(q, chunks)            -> Chunk[]   (ontology boost in v0.2.1)     │
│    4. prompt.build_user_prompt()   -> str                                     │
│    5. llm.complete(system, user)   -> answer                                  │
│    6. domain enrich:                                                          │
│         jsonld_generator (if jsonld_generation)                               │
│         one_record_schema (related_concepts)                                  │
│    7. assemble ChatResponse                                                   │
└───────┬───────────────────────────┬───────────────────────────┬──────────────┘
        │                           │                           │
   core/llm.py                core/embeddings.py          rag/retriever.py
   (LLMProvider)              (EmbeddingProvider)          (Retriever -> Qdrant)
```

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

That said, "never empty" is not the same thing as "broad enough". The current
demo subset is intentionally small; the next milestone work should focus first
on expanding imported sources before piling on more feature branches.

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

## Future integration points (v0.2 / v0.3)

Recommended order:

1. expand official and NE:ONE source coverage
2. validate ontology-aware retrieval on that broader source pack
3. add NE:ONE implementation knowledge
4. upgrade the frontend with streaming and stronger interaction patterns
5. add workflow orchestration for real ONE Record business tasks
6. integrate RecordForge
7. add ALH narrative last, after the core ONE Record path is strong

- **RecordForge**: a synthetic-data tool callable from the pipeline to fulfil
  "generate N shipments" requests, returning JSON-LD.
- **AviationLakehouse**: explain/route ONE Record objects into Bronze/Silver/Gold.
- **ONE Record Server**: live retrieval of real logistics objects.

The `Retriever` abstraction remains the seam for remote/live object lookup.
The `Connector` abstraction is the new seam for optional workflow integrations
such as RecordForge and future execution-oriented ecosystem tools.
