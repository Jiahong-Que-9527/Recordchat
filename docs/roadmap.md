# RecordChat Roadmap

The **current** plan (status, next slice, issue map) lives in
[project_plan.md](project_plan.md). This file is the milestone narrative.

## Status

- **v0.1**: complete and demoable
- **Data Foundation**: core official + NE:ONE pack is in final folders;
  `_staging` is excluded from ingest. Leftover: `#23` (manual overview/PDF pack)
- **v0.2.1 ontology-aware retrieval**: done (GitHub milestone closed)
- **v0.2.2 NE:ONE implementation knowledge**: done at a useful baseline
- **v0.2.3 streaming frontend**: done (GitHub milestone closed)
- **next priority**: **Retrieval Quality** (`#27`–`#31`) — pin one ontology
  version, gold-chunk eval, hybrid + filters, follow-up rewrite, citation filter
- **after that**: finish v0.2.4 workflow (`#32`), then RecordForge (`#13` `#14`)

Source acquisition and import plan:
[docs/data_source_plan.md](data_source_plan.md)

GitHub tracking:

- Retrieval Quality (current): `#27`–`#31`
- workflow remainder: `#32`
- RecordForge: `#13` `#14`
- ALH (deferred): `#7`–`#10`
- data leftover: `#23`
- closed foundation / ontology / frontend: `#1`–`#6`, `#11` `#12`, `#15`–`#22`, `#24`–`#26`

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

The core official + NE:ONE pack is in the final folders. Remaining import work
(`#23`) is optional and must not jump the Retrieval Quality queue.

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

- `#23` manual overview / PDF / community captures (not a Retrieval Quality blocker)
- do **not** ingest additional community HTML/PDF until ontology de-duplication
  (`#27`) and gold-chunk eval (`#28`) exist — more files would amplify duplicates

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

1. **Retrieval Quality** (current)
   Pin one ontology version, replace smoke eval with gold-chunk metrics, add
   hybrid retrieval and query-type filters, then follow-up rewrite and citation
   filtering. Issues `#27`–`#31`.
2. **Finish v0.2.4 workflow orchestration**
   Structured workflow results and an execution path on the existing Connector
   ABC (`#32`). `#11` / `#12` already landed the seam.
3. **v0.2.5 RecordForge integration**
   Synthetic data generation behind the connector (`#13` `#14`).
4. **v0.2.6 AviationLakehouse narrative**
   Bronze / Silver / Gold story last (`#7`–`#10`).
5. **Data Foundation leftover (`#23`)**
   Optional community / PDF pack; do not let it jump the retrieval-quality queue.

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

## Retrieval Quality

Goal:

- stop indexing overlapping ontology copies
- measure retrieval (recall@5 / MRR / source family), not just “answer non-empty”
- hybrid + metadata filters so implementation/API questions hit the right family
- follow-up questions keep entities; citations match used chunks

Current state:

- ontology-aware rerank is in the pipeline, but the index still contains
  multiple versions of the same classes
- `evaluate_rag.py` is a keyword smoke test
- search is dense-only; conversation history is not used for retrieval

Issues: `#27`–`#31`. Details: [project_plan.md](project_plan.md) §4.

## v0.2.3 — Frontend upgrade

Goal:

- move from the v0.1 hand-rolled UI to a more capable streaming chat UI

Status: **done**. Streaming `POST /chat/stream`, AI SDK chat UI, sources /
related concepts / JSON-LD panels.

## v0.2.4 — Workflow orchestration

Goal:

- support real business workflow questions and multi-step execution flows around
  ONE Record operations, not just static Q&A

Status: **partial**. Connector ABC and synthetic-generation routing exist;
structured results and execution are `#32`. Blocked on Retrieval Quality.

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
