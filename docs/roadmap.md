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
- **2026-09 audit**: the P0 findings (AUD-01 eval set, AUD-02 canonical
  versions, AUD-03 reranker weighting, AUD-04 config/model) are now the first
  work items — details in [project_plan.md §4.7](project_plan.md#47-2026-09-audit-findings-aud-01aud-10)
- **next priority**: **Retrieval Quality** (`#27`–`#31`), starting with the
  audit P0 fixes — pin one version per source family, gold-chunk eval, hybrid +
  filters, follow-up rewrite, citation filter
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

0. **2026-09 audit P0 fixes** (AUD-01–04; §4.7 of `project_plan.md`) — restore
   and version the eval set, de-duplicate canonical sources, fix the reranker
   weighting, reconcile config/model defaults.
1. **Retrieval Quality** (current after the audit P0)
   Pin one canonical version per source family, replace smoke eval with
   gold-chunk metrics, add hybrid retrieval and query-type filters, then
   follow-up rewrite and citation filtering. Issues `#27`–`#31`.
2. **Finish v0.2.4 workflow orchestration**
   Structured workflow results and an execution path on the existing Connector
   ABC (`#32`). `#11` / `#12` already landed the seam.
3. **v0.2.5 RecordForge integration**
   Synthetic data generation behind the connector (`#13` `#14`).
4. **v0.2.6 AviationLakehouse narrative**
   Bronze / Silver / Gold story last (`#7`–`#10`).
5. **Data Foundation leftover (`#23`)**
   Optional community / PDF pack; do not let it jump the retrieval-quality queue.

## Strategic guidance (product-level)

- **Credibility before capability.** The biggest risk is not missing features,
  but retrieving unclearly and then building connectors on an unstable corpus.
  Treat `#27`–`#31` (and the audit P0) as a **release gate**, and run the
  external expert interviews (§4.6 of `project_plan.md`) before expanding the
  ecosystem.
- **RecordForge / ALH are narrative-first.** Their value is telling the
  "closed ecosystem" story for a portfolio, not full integration. Build the
  **minimum demoable connector** (generate N shipments → JSON-LD; explain
  ONE Record → Bronze/Silver/Gold) and stop there.
- **Make the differentiators visible.** The four things few other RAG projects
  have are: template-guaranteed JSON-LD, ontology-aware retrieval, Mermaid
  relationship diagrams, and citation-first grounding. Surface these as a
  shareable one-click demo entry, not just something buried inside the chat
  stream.

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

- stop indexing overlapping source copies (ontology **and** OpenAPI/spec docs)
- measure retrieval (recall@5 / MRR / source family), not just “answer non-empty”
- hybrid + metadata filters so implementation/API questions hit the right family
- follow-up questions keep entities; citations match used chunks

Current state:

- ontology-aware rerank is in the pipeline, but the index still contains
  multiple versions of the same classes — and the duplication extends to OpenAPI
  (3 versions) and spec docs (3 live versions); see AUD-02
- `evaluate_rag.py` is a keyword smoke test **and currently crashes** because
  the versioned eval set (`data/eval/questions.yaml`) is missing; see AUD-01
- search is dense-only; conversation history is not used for retrieval
- the reranker's entity boosts currently override vector similarity; see AUD-03

Issues: `#27`–`#31` plus audit items AUD-01…AUD-10.
Details: [project_plan.md](project_plan.md) §4 and §4.7.

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
