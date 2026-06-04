# RecordChat Architecture

## Overview

RecordChat is a retrieval-augmented (RAG) assistant for IATA ONE Record. A
Next.js frontend talks to a FastAPI backend over a small JSON contract. The
backend retrieves source-grounded context from Qdrant, assembles a prompt, calls
a (provider-abstracted) LLM, and enriches the answer with domain tools
(relationship map + JSON-LD templates).

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
│    3. rerank(q, chunks)            -> Chunk[]   (no-op in v0.1)                │
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

## Key design decisions

### 1. Provider abstraction (LLM + Embedding + Retriever)
`LLMProvider`, `EmbeddingProvider`, and `Retriever` are abstract base classes.
Factories in `core/` choose the concrete implementation from env vars. Switching
between Qwen / OpenAI / Claude is configuration, not code. See
[adr/0001-provider-abstraction.md](adr/0001-provider-abstraction.md).

### 2. Offline-first graceful degradation
With no API key the `local` LLM (extractive, grounded in retrieved context) and
`local` hashing embeddings keep the whole app runnable, plus an in-process Qdrant
(`QDRANT_URL=:memory:`). A missing key logs a warning and falls back — it never
crashes. This makes the project demoable and testable with zero secrets.

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

## Future integration points (v0.2 / v0.3)

- **RecordForge**: a synthetic-data tool callable from the pipeline to fulfil
  "generate N shipments" requests, returning JSON-LD.
- **AviationLakehouse**: explain/route ONE Record objects into Bronze/Silver/Gold.
- **ONE Record Server**: live retrieval of real logistics objects.
- **Ontology-aware retrieval**: entity-first search using the parsed ontology.

The `reranker.py` no-op and the `Retriever` abstraction are the seams reserved
for these upgrades.
