# RecordChat Roadmap

## Status

- **v0.1**: complete and demoable
- **v0.2.1 ontology-aware retrieval**: largely landed in code; still needs to be
  validated against a broader official source set
- **next priority**: expand the knowledge base so the system matches the real
  ONE Record / NE:ONE materials defined in the source planning docs

Source acquisition and import plan:
[docs/data_source_plan.md](data_source_plan.md)

GitHub issue starting points:

- data foundation and source import: `#21` - `#26`
- existing downstream milestone issues: `#7` - `#20`

## v0.1 — ONE Record RAG assistant (completed baseline)

Delivered:

- FastAPI backend: `/health`, `/chat`, `/ingest`
- RAG pipeline: classify -> retrieve (Qdrant) -> prompt -> LLM -> cited answer
- Provider abstraction (Qwen / OpenAI / Claude) + offline `local` fallback
- Domain-aware chunking (ontology / OpenAPI / markdown / JSON-LD)
- Curated glossary as graceful-degradation knowledge base
- Template-based JSON-LD generator (Piece, Shipment, Waybill, TransportMovement)
- Relationship enrichment
- Minimal Next.js + Tailwind chat UI with sources + JSON-LD viewer
- Evaluation set + `evaluate_rag.py`
- Demo docs and VPS-friendly setup notes

## Cross-Cutting Prerequisite — Data Foundation

Before the next milestone work is considered "basically meets requirements", the
knowledge base must be expanded from the current illustrative subset to the
official and implementation-level source pack.

Scope:

- official ONE Record repo materials
- official `development` and `2025-07` spec docs
- official ontology files
- official OpenAPI files
- broader JSON-LD examples
- NE:ONE docs, configs, and example payloads

Execution details:
[docs/data_source_plan.md](data_source_plan.md)

Primary GitHub issues:

- [#21](https://github.com/Jiahong-Que-9527/Recordchat/issues/21) raw-data conventions and metadata
- [#22](https://github.com/Jiahong-Que-9527/Recordchat/issues/22) official ONE Record source pack
- [#23](https://github.com/Jiahong-Que-9527/Recordchat/issues/23) manual download pack
- [#24](https://github.com/Jiahong-Que-9527/Recordchat/issues/24) NE:ONE staging and normalization
- [#25](https://github.com/Jiahong-Que-9527/Recordchat/issues/25) NE:ONE implementation Q&A coverage
- [#26](https://github.com/Jiahong-Que-9527/Recordchat/issues/26) ontology-aware retrieval validation

## Recommended Next Order

1. **Data Foundation**
   Download, normalize, and import the required official and NE:ONE sources.
2. **v0.2.1 Validation**
   Re-run ontology-aware retrieval against the expanded source set and close any
   quality gaps.
3. **v0.2.2 NE:ONE implementation knowledge**
   Make the assistant useful for setup, config, payload, and troubleshooting questions.
4. **v0.2.3 AviationLakehouse narrative**
   Add Bronze/Silver/Gold landing explanations and domain mapping.
5. **v0.2.4 Frontend upgrade**
   Replace the hand-rolled UI with a streaming AI-chat surface.
6. **v0.2.5 RecordForge integration**
   Add synthetic data generation only after the knowledge base and UI are ready.

## v0.2.1 — Ontology-aware retrieval

Goal:

- parse richer official ONE Record ontology sources
- use entity-first retrieval and ontology neighbors
- reduce reliance on the manual relationship map

Current state:

- ADR, parser, ontology graph, reranker, and tests already exist in the repo
- the remaining concern is source breadth and validation against official files

## v0.2.2 — NE:ONE implementation knowledge

Goal:

- answer practical questions about NE:ONE setup, config, API interaction,
  example payloads, and troubleshooting

Needs:

- NE:ONE README/docs/configs/examples/tests extracted into ingestible text-like files
- classifier/prompt updates for implementation questions
- demo and eval coverage for NE:ONE flows

## v0.2.3 — AviationLakehouse narrative

Goal:

- answer how ONE Record objects map into Bronze / Silver / Gold layers
- support architecture and platform narrative questions with grounded sources

Needs:

- ALH knowledge document
- `alh_mapping` domain module
- eval/demo/glossary updates

## v0.2.4 — Frontend upgrade

Goal:

- move from the v0.1 hand-rolled UI to a more capable streaming chat UI

Scope:

- streaming `POST /chat/stream`
- AI SDK / Vercel chatbot style frontend
- preserve RecordChat-specific domain panels: sources, related concepts, JSON-LD

## v0.2.5 — RecordForge integration

Goal:

- support synthetic data generation requests such as:
  `"Generate 5 synthetic shipments with pieces and transport events"`

Needs:

- connector abstraction
- query type for synthetic data generation
- RecordForge stub or HTTP client
- frontend support for multi-object JSON-LD results

## v0.3 — Real platform

- authentication and user sessions
- conversation memory and persisted chat history
- source versioning and ingestion management
- OpenTelemetry tracing and evaluation dashboard
- live connectors: ONE Record Server, RecordForge, AviationLakehouse

## Positioning

```text
RecordChat        = AI interface for ONE Record knowledge
RecordForge       = synthetic ONE Record data generator
ONE Record Server = standardized data exchange layer
AviationLakehouse = analytical backend (Bronze/Silver/Gold)
```
