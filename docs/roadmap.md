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
- Next.js + Tailwind chat UI with sources + JSON-LD viewer
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

## v0.3 — Real platform

- Authentication, user sessions, conversation memory
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
