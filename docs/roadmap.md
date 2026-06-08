# RecordChat Roadmap

## Status

- **v0.1**: complete and demoable
- **Data Foundation**: partially landed; `_staging` is now excluded from ingest
  and a first normalized official/NE:ONE source batch is in final folders
- **v0.2.1 ontology-aware retrieval**: landed and validated on the broadened
  official source pack, including official OWL ingest, ontology-aware reranking,
  and multilingual ontology queries
- **v0.2.2 NE:ONE implementation knowledge**: landed at a useful baseline with
  implementation query routing, NE:ONE source citation, and eval/demo coverage
- **next priority**: move from knowledge-quality validation into stronger user
  interaction and execution layers: streaming UI first, workflow orchestration
  second

Source acquisition and import plan:
[docs/data_source_plan.md](data_source_plan.md)

GitHub issue starting points:

- data foundation and source import: `#21` - `#26`
- existing downstream milestone issues: `#7` - `#20`

## v0.1 — ONE Record RAG assistant (completed baseline)

Delivered:

- FastAPI backend: `/health`, `/chat`, `/ingest`
- RAG pipeline: classify -> retrieve (Qdrant) -> prompt -> LLM -> cited answer
- Provider abstraction (Qwen / OpenAI / Claude)
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

Current remaining work:

- finish converting HTML/PDF/manual-download material into ingestible text
- add sidecar metadata for imported source families
- rerun `/ingest` on the normalized corpus and verify source/chunk coverage
- extend eval so official docs and NE:ONE materials are exercised directly

Canonical data-foundation conventions:

- `data/raw/_staging/` is raw intake only and is not part of the live corpus
- normalized files must move into final `data/raw` folders before ingest
- loader and ontology traversal explicitly skip `_staging`
- governed source batches should use `<filename>.<ext>.meta.json` sidecars with
  `source_name`, `version`, `url`, `document_type`, `domain`, `registry_id`,
  `batch_id`, and `ingested_at`

Canonical final destinations for the current core source pack:

- `data/raw/one_record_docs/spec_development/`
- `data/raw/one_record_docs/spec_2025_07/`
- `data/raw/ontology/official/`
- `data/raw/api_specs/official/`
- `data/raw/examples/official/`
- `data/raw/one_record_docs/ne_one/`
- `data/raw/api_specs/ne_one/`
- `data/raw/examples/ne_one/`

Primary GitHub issues:

- [#21](https://github.com/Jiahong-Que-9527/Recordchat/issues/21) raw-data conventions and metadata
- [#22](https://github.com/Jiahong-Que-9527/Recordchat/issues/22) official ONE Record source pack
- [#23](https://github.com/Jiahong-Que-9527/Recordchat/issues/23) manual download pack
- [#24](https://github.com/Jiahong-Que-9527/Recordchat/issues/24) NE:ONE staging and normalization
- [#25](https://github.com/Jiahong-Que-9527/Recordchat/issues/25) NE:ONE implementation Q&A coverage
- [#26](https://github.com/Jiahong-Que-9527/Recordchat/issues/26) ontology-aware retrieval validation

## Recommended Next Order

1. **Data Foundation**
   Finish normalization, metadata, ingest verification, and eval coverage for the
   required official and NE:ONE sources.
2. **v0.2.1 Validation**
   Re-run ontology-aware retrieval against the expanded source set and close any
   quality gaps.
3. **v0.2.2 NE:ONE implementation knowledge**
   Make the assistant useful for setup, config, payload, and troubleshooting questions.
4. **v0.2.3 Frontend upgrade**
   Replace the hand-rolled UI with a streaming AI-chat surface.
5. **v0.2.4 Workflow orchestration**
   Add connector abstractions and business-flow execution paths for ONE Record
   tasks before integrating external generators.
6. **v0.2.5 RecordForge integration**
   Add synthetic data generation and workflow execution once the orchestration
   layer and UI are ready.
7. **v0.2.6 AviationLakehouse narrative**
   Defer the Bronze/Silver/Gold platform story until the ONE Record core
   assistant, streaming UX, and workflow integrations are strong.

## v0.2.1 — Ontology-aware retrieval

Goal:

- parse richer official ONE Record ontology sources
- use entity-first retrieval and ontology neighbors
- reduce reliance on the manual relationship map

Current state:

- official ontology TTL and OWL files are indexed from the normalized source pack
- ontology chunks, entity-first reranking, and `related_concepts` ontology neighbors
  are already active in the pipeline
- eval and multilingual spot checks have been extended to cover ontology questions

## v0.2.2 — NE:ONE implementation knowledge

Goal:

- answer practical questions about NE:ONE setup, config, API interaction,
  example payloads, and troubleshooting

Current state:

- NE:ONE docs/configs/examples/tests are normalized into final `data/raw` folders
- implementation questions have dedicated classifier and prompt steering
- eval/demo coverage includes NE:ONE setup and troubleshooting flows

## v0.2.3 — Frontend upgrade

Goal:

- move from the v0.1 hand-rolled UI to a more capable streaming chat UI

Needs:

- streaming `POST /chat/stream`
- AI SDK / Vercel chatbot style frontend
- preserve RecordChat-specific domain panels: sources, related concepts, JSON-LD

## v0.2.4 — Workflow orchestration

Goal:

- support real business workflow questions and multi-step execution flows around
  ONE Record operations, not just static Q&A

Scope:

- connector abstraction for external business workflow tools
- query routing for execution / orchestration intents
- structured workflow results that the frontend can render cleanly

## v0.2.5 — RecordForge integration

Goal:

- support synthetic data generation requests such as:
  `"Generate 5 synthetic shipments with pieces and transport events"`

Needs:

- build on the workflow orchestration layer rather than bypass it
- query type for synthetic data generation
- RecordForge stub or HTTP client
- frontend support for multi-object JSON-LD results

## v0.2.6 — AviationLakehouse narrative

Goal:

- answer how ONE Record objects map into Bronze / Silver / Gold layers
- support architecture and platform narrative questions with grounded sources

Needs:

- ALH knowledge document
- `alh_mapping` domain module
- eval/demo/glossary updates

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
AviationLakehouse = analytical backend (Bronze/Silver/Gold, deferred)
```
