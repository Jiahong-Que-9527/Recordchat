# RecordChat Roadmap

The **current** plan (status, next slice, issue map) lives in
[project_plan.md](project_plan.md). This file is the milestone narrative.

## Status (2026-09-11)

- **v0.1**: complete and demoable
- **Data Foundation**: core official + NE:ONE pack is in final folders;
  `_staging` is excluded from ingest. Leftover: `#23` (manual overview/PDF pack)
- **v0.2.1 ontology-aware retrieval**: done
- **v0.2.2 NE:ONE implementation knowledge**: done at a useful baseline
- **v0.2.3 streaming frontend**: done
- **2026-09 audit P0/P1** (AUD-01…AUD-07): done — see
  [project_plan.md §4.7](project_plan.md#47-2026-09-audit-findings-aud-01aud-10)
- **Retrieval Quality** (`#27`–`#31`): done
- **v0.2.4 workflow** (`#11` `#12` `#32`): done
- **v0.2.5 RecordForge** (`#13` `#14`): done (live HTTP + workflow UI)
- **v0.2.6 ALH narrative** (`#7`–`#10`): done
- **next priority**: nothing scheduled (optional P2 or user-requested v0.3)

Source acquisition and import plan:
[docs/data_source_plan.md](data_source_plan.md)

GitHub tracking:

- ALH (done): `#7`–`#10`
- RecordForge (done): `#13` `#14`
- data leftover: `#23`
- closed retrieval / workflow / audit foundations: `#27`–`#32` (+ AUD-01…07)
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

- `#23` manual overview / PDF / community captures (optional; not a RecordForge blocker)
- additional community HTML/PDF ingest still needs the canonical-version policy
  (`rag/canonical.py`) — do not bypass it

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

0–3. **Done:** audit P0/P1, Retrieval Quality `#27`–`#31`, workflow `#32`,
   RecordForge `#13` `#14` (plus Local JSON-LD toggle).
4. **v0.2.6 AviationLakehouse narrative** — **done**
   ([alh_execution_brief.md](alh_execution_brief.md)).
5. **v0.3 platform** — sketch only ([v03_sketch.md](v03_sketch.md)).
6. **Data Foundation leftover (`#23`)** — optional P2.

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

Current state: **done** (2026-09-09). Canonical-version ingest, gold-chunk
eval, hybrid dense+BM25 RRF, query-type filters, follow-up rewrite, citation
filter, vector-dominant reranker. Remaining P2 only: AUD-08…AUD-10.

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

Status: **done**. Connector ABC, synthetic routing, structured
`workflow_result`, RecordForge HTTP (`#13`) and frontend workflow view (`#14`).

Scope:

- connector abstraction for external business workflow tools
- query routing for execution / orchestration intents
- structured workflow results that the frontend can render cleanly

## v0.2.5 — RecordForge integration

Status: **done**. HTTP client when `RECORDFORGE_URL` is set; unconfigured
blocked workflow; Local JSON-LD templates via `synthetic_mode`. Generation
is displayed only — no ONE Record Server persist.

## v0.2.6 — AviationLakehouse narrative

Status: **done**. See [alh_execution_brief.md](alh_execution_brief.md).

Goal met:

- answer how ONE Record objects map into Bronze / Silver / Gold layers
- `architecture_question` routing with grounded ALH doc + glossary
- no live lakehouse

## v0.3 — Real platform

Sketch only: [v03_sketch.md](v03_sketch.md). Not scheduled.

## Positioning

```text
RecordChat        = AI interface for ONE Record knowledge
RecordForge       = synthetic ONE Record data generator
ONE Record Server = standardized data exchange layer
AviationLakehouse = analytical backend (Bronze/Silver/Gold, deferred)
```
