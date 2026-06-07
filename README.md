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

- `v0.1` is complete and demoable
- the next priority is **not** piling on more features first
- the next priority is expanding the knowledge base from the current minimal
  subset to the broader official ONE Record + NE:ONE source pack

See [docs/data_source_plan.md](docs/data_source_plan.md) for the source
acquisition and import plan.

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
cp .env.example .env        # optional: add LLM/EMBEDDING keys for real models
docker compose up --build
# backend  -> http://localhost:8000
# frontend -> http://localhost:3000
curl -X POST localhost:8000/ingest        # build the knowledge base
```

If you are developing on a VPS and opening the UI from your local browser:

- open `http://<your-vps-host>:3000` in your browser
- run `curl -X POST http://127.0.0.1:8000/ingest` on the VPS shell
- if you want explicit hostnames, set:
  `CORS_ORIGINS=http://<your-vps-host>:3000`
  `NEXT_PUBLIC_API_BASE_URL=http://<your-vps-host>:8000`

### Option B — Backend only, fully offline (no API keys, no Docker)

```bash
cd backend
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
curl -X POST localhost:8000/ingest
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is a Piece in ONE Record?"}'
```

With no keys configured, RecordChat runs in **offline mode**: `local` LLM
(extractive, source-grounded), `local` hashing embeddings, and an in-process
Qdrant. Set `LLM_PROVIDER`/`LLM_API_KEY` etc. (see [.env.example](.env.example))
to switch to Qwen / OpenAI / Claude with zero code changes.

By default, the frontend now auto-detects the API host from the page URL. So if
you open `http://<your-vps-host>:3000`, it will try `http://<your-vps-host>:8000`
unless `NEXT_PUBLIC_API_BASE_URL` is explicitly set.

> The repository currently ships a **minimal demo source set** plus the curated
> glossary. That is enough for v0.1 demos, but the next project priority is to
> import the broader official ONE Record and NE:ONE materials listed in
> [docs/data_source_plan.md](docs/data_source_plan.md).

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
scripts/    ingest_docs.py, evaluate_rag.py, reset_index.py
SPEC.md     single source of truth (contracts, structure, acceptance)
```

## Roadmap

- **v0.1** demoable ONE Record RAG assistant (this repo)
- **next** data foundation: official ONE Record + NE:ONE source expansion
- **v0.2** ontology validation + NE:ONE knowledge + ALH narrative + frontend upgrade
- **later** RecordForge integration + live ecosystem connectors

See [docs/roadmap.md](docs/roadmap.md).
