<div align="center">
  <img src="assets/recordchat-logo.png" alt="RecordChat logo" width="480">
</div>

# RecordChat

**A domain-specific AI assistant for IATA ONE Record.**

RecordChat helps developers and logistics stakeholders understand the ONE Record
data model, API concepts, JSON-LD payloads, and the semantic relationships between
logistics objects. It uses retrieval-augmented generation (RAG) with **source-grounded,
cited answers** — not an ungrounded chatbot.

> **Disclaimer:** RecordChat is a **personal, independent project**. It is **not** an
> official IATA ONE Record product, and is not affiliated with, endorsed by, or
> maintained by IATA. All reference materials used in this repository (specifications,
> ontologies, examples, etc.) come from **publicly available open-source resources**.

> RecordChat is the first interface layer for a future aviation data platform ecosystem:
> **RecordChat** (AI interface) · **RecordForge** (synthetic data) ·
> **ONE Record Server** (exchange layer) · **AviationLakehouse** (analytics backend).

See [SPEC.md](SPEC.md) for the full specification and execution plan.

## Why ONE Record?

[IATA ONE Record](https://www.iata.org/en/programs/cargo/e/one-record/) is the air-cargo
data-sharing standard: a single shared record of truth per shipment, modeled as
interlinked **LogisticsObjects** exposed over a REST API and serialized as JSON-LD.
RecordChat makes that standard approachable and queryable.

## Current Status

- `v0.2.3` frontend upgrade is now landed and demoable
- official ONE Record, ontology, and NE:ONE source packs are ingested under the
  governed `data/raw` layout
- ontology-aware retrieval and NE:ONE implementation Q&A are validated
- the frontend now streams through AI SDK `useChat` with RecordChat-specific
  grounded panels for sources, related concepts, and JSON-LD
- the next priority is workflow orchestration, then RecordForge integration

See [docs/data_source_plan.md](docs/data_source_plan.md) for the source
acquisition and import plan.

### Data Foundation Conventions

The current raw-data contract is:

- `data/raw/_staging/` is a download-and-normalization workspace only
- loader-facing files must live in final `data/raw` folders, not under `_staging`
- `backend/app/rag/loader.py` and `backend/app/domain/ontology_graph.py`
  explicitly skip `_staging`
- loader-ingestible file types are `.ttl`, `.owl`, `.md`, `.markdown`, `.txt`,
  `.json`, `.jsonld`, `.yaml`, and `.yml`

The canonical final homes for the current P0 source families are:

- `data/raw/one_record_docs/spec_development/`
- `data/raw/one_record_docs/spec_2025_07/`
- `data/raw/ontology/official/`
- `data/raw/api_specs/official/`
- `data/raw/examples/official/`
- `data/raw/one_record_docs/ne_one/`
- `data/raw/api_specs/ne_one/`
- `data/raw/examples/ne_one/`

Governed files should carry a sidecar at `<filename>.<ext>.meta.json` with at
least:

- `source_name`
- `version`
- `url`
- `document_type`
- `domain`
- `registry_id`
- `batch_id`
- `ingested_at`

## Architecture

```
Frontend (Next.js)  ──HTTP──▶  Backend (FastAPI)
                                 └─ rag/pipeline ─▶ retriever (Qdrant)
                                                  ─▶ prompt + llm (provider-abstracted)
                                                  ─▶ domain (relationships, JSON-LD)
Ingestion:  data/raw ─▶ loader ─▶ chunker ─▶ embeddings ─▶ Qdrant
```

Details in [docs/architecture.md](docs/architecture.md).

## Quickstart

### Option A — Docker Compose (backend + frontend + Qdrant)

```bash
cp .env.example .env
docker compose up --build
# backend  -> http://localhost:8000
# frontend -> http://localhost:3000
curl -X POST http://127.0.0.1:8000/ingest
```

`POST /ingest` now rebuilds the collection by default. This avoids stale-vector
dimension mismatches after you change the embedding model or dimension.

If you are developing on a VPS and opening the UI from your local browser:

- open `http://<your-vps-host>:3000` in your browser
- run `curl -X POST http://127.0.0.1:8000/ingest` on the VPS shell
- if needed, set:
  `CORS_ORIGINS=http://<your-vps-host>:3000`
- `NEXT_PUBLIC_API_BASE_URL` can stay empty because the frontend now auto-detects
  `http://<current-host>:8000`

### Option B — Backend only (external model APIs, no Docker)

```bash
cd backend
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
curl -X POST localhost:8000/ingest
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is a Piece in ONE Record?"}'
```

RecordChat expects both generation and retrieval to use external model APIs.
Configure `LLM_PROVIDER` / `LLM_API_KEY` and `EMBEDDING_PROVIDER` /
`EMBEDDING_API_KEY` before starting the backend. Qdrant can still run in-process
via `QDRANT_URL=:memory:` if you do not want Docker.

If you want to use different vendors for generation and retrieval, configure
them independently. For example:

```env
LLM_PROVIDER=openai
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=your_deepseek_key
LLM_BASE_URL=your_deepseek_openai_compatible_base_url

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=your_openai_key
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_DIM=1536
```

Any time you change the embedding model or provider, rerun `/ingest` so the
stored document vectors and query vectors stay in the same embedding space.

By default, the frontend auto-detects the API host from the page URL. If you
open `http://<your-vps-host>:3000`, it will call `http://<your-vps-host>:8000`
unless `NEXT_PUBLIC_API_BASE_URL` is explicitly set.

The current demo corpus is no longer just a tiny glossary seed. It now includes
broadened official ONE Record, ontology, and NE:ONE materials listed in
[docs/data_source_plan.md](docs/data_source_plan.md).

## Try these questions

- What is ONE Record?
- What is a LogisticsObject?
- Explain the relationship between Shipment and Piece.
- Generate a JSON-LD example for a Piece.
- How does ONE Record support data sharing?

## Repository layout

```
assets/     project branding (logo, etc.)
backend/    FastAPI service (API, RAG pipeline, domain layer, tests)
frontend/   Next.js + Tailwind + shadcn-style chat UI
data/       raw sources, processed artifacts, eval questions
docs/       architecture, roadmap, demo script, ADRs
scripts/    ingest_docs.py, evaluate_rag.py, reset_index.py, governance/data workflow helpers
SPEC.md     single source of truth (contracts, structure, acceptance)
```

## Roadmap

- **v0.1** initial demoable ONE Record RAG assistant
- **v0.2.1/v0.2.2** ontology validation + NE:ONE implementation knowledge
- **v0.2.3** streaming frontend upgrade with AI SDK chat shell
- **next** workflow orchestration
- **later** RecordForge integration, then ALH narrative and broader live ecosystem connectors

See [docs/roadmap.md](docs/roadmap.md).

## Data Compliance

See [docs/data_compliance_report.md](docs/data_compliance_report.md) for the
current data-compliance review and operating boundaries for source usage.

The project does not fine-tune foundation models on third-party source content.
It uses citation-first retrieval over reviewed public materials, with source
tracking moving toward a structured registry in
[docs/data_sources_registry.yaml](docs/data_sources_registry.yaml).

For a shorter external-facing statement of source usage and compliance
boundaries, see [docs/source_usage_policy.md](docs/source_usage_policy.md).

In short: RecordChat uses reviewed public materials for retrieval and citation,
does not claim official affiliation with source publishers, does not ingest
access-restricted materials, and is designed to avoid republishing raw
third-party source bundles as public assets.

The curated core corpus is also protected by a lightweight source-governance
check so key official and NE:ONE materials keep registry-linked provenance and
`_staging` does not drift back into the live ingest surface.

For the standardized data-addition SOP and the command used after each new batch,
see [docs/data_addition_workflow.md](docs/data_addition_workflow.md). The
canonical local entrypoint is:

```bash
python3 scripts/run_data_addition_workflow.py
```
