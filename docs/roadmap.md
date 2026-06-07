# RecordChat Roadmap

## v0.1 — ONE Record RAG assistant (current)

A production-minded MVP:
- FastAPI backend: `/health`, `/chat`, `/ingest`
- RAG pipeline: classify → retrieve (Qdrant) → prompt → LLM → cited answer
- Provider abstraction (Qwen / OpenAI / Claude) + offline `local` fallback
- Domain-aware chunking (ontology / OpenAPI / markdown / JSON-LD)
- Curated glossary as graceful-degradation knowledge base
- Template-based JSON-LD generator (Piece, Shipment, Waybill, TransportMovement)
- Manually curated relationship map
- Minimal Next.js + Tailwind chat UI (hand-rolled MVP) with sources + JSON-LD
  viewer — intentionally basic; polished UI deferred to v0.2 (see below)
- Evaluation set (12 questions) + `evaluate_rag.py`
- Docs: architecture, roadmap, demo script

## v0.2 — Semantics + first ecosystem hook

- **v0.2.1 Ontology-aware retrieval**: parse the official ONE Record ontology to
  extract classes/properties/relationships; entity-first search (detect the
  entity in the query, then prioritize its chunks).
- **v0.2.2 RecordForge integration**: `"Generate 5 synthetic shipments with
  pieces and transport events"` → RecordChat calls RecordForge → JSON-LD output.
- **v0.2.3 AviationLakehouse narrative**: answer "how would this land in ALH?"
  with the Bronze → Silver → Gold mapping.
- **v0.2.4 Frontend upgrade (Vercel AI Chatbot template)**: replace the v0.1
  hand-rolled UI with the official [Vercel AI Chatbot](https://github.com/vercel/chatbot)
  template ([deploy starter](https://vercel.com/templates/next.js/chatbot)).
  - **Stack**: Next.js App Router, [Vercel AI SDK](https://ai-sdk.dev),
    shadcn/ui, [AI Elements](https://elements.ai-sdk.dev) (streaming conversation
    primitives).
  - **Streaming**: backend adds `POST /chat/stream` (SSE); frontend uses
    `useChat` / AI SDK hooks so answers render token-by-token instead of
    blocking on the full JSON response.
  - **Keep RecordChat domain UI**: port sources panel, related-concept tags,
    query-type badge, and JSON-LD viewer into the new layout — not a generic
    ChatGPT clone.
  - **Backend contract unchanged**: FastAPI RAG pipeline stays the source of
    truth; the template's default AI Gateway / direct-provider routes are
    adapted to call RecordChat `/chat` and `/chat/stream`, not replace ingest
    or Qdrant retrieval.
  - **Polish**: Markdown rendering, code highlighting, loading states, responsive
    layout. v0.1's synchronous `POST /chat` remains for scripts and eval.

## v0.3 — Real platform

- **v0.3.1 Chat platform features** (extends v0.2.4 template):
  - Authentication and user sessions (template auth patterns)
  - Conversation memory and persisted chat history (Neon Postgres / Redis per
    Vercel template defaults)
  - Optional one-click deploy to Vercel with environment-based API routing
- Source versioning, OpenTelemetry tracing, evaluation dashboard
- Admin ingestion UI
- Live connectors: ONE Record Server · RecordForge · AviationLakehouse

## Positioning

```
RecordChat        = AI interface for ONE Record knowledge
RecordForge       = synthetic ONE Record data generator
ONE Record Server = standardized data exchange layer
AviationLakehouse = analytical backend (Bronze/Silver/Gold)
```
