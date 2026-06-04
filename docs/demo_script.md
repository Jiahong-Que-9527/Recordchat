# RecordChat Demo Script

A 3–5 minute walkthrough. Works fully offline (local providers).

## Setup

```bash
# Backend (offline mode, no keys needed)
cd backend && uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --port 8000 &
curl -X POST localhost:8000/ingest

# Frontend
cd ../frontend && npm install && npm run dev
# open http://localhost:3000
```

> For higher-quality, synthesized answers, set `LLM_PROVIDER=qwen` (or `openai`
> / `claude`) and the matching `*_API_KEY` in `.env`, then restart the backend.

## The five demo questions

Ask each from the UI (or click the example in the sidebar). Talking points note
what to highlight for a reviewer.

### 1. What is ONE Record?
- Concept answer with **Sources** panel → shows answers are grounded, not invented.

### 2. What is a LogisticsObject?
- Note the `concept_explanation` type chip and the related-concept tags
  (Shipment, Piece, Waybill) — the relationship map enriching the answer.

### 3. Explain Shipment vs Piece.
- Classified as `relationship_question`; related concepts show how the entities
  connect. Mention the curated `ONE_RECORD_RELATIONSHIPS` map (v0.2 will derive
  this from the ontology).

### 4. Generate a JSON-LD example for a Piece.
- Classified as `jsonld_generation`; a formatted **JSON-LD** block appears with
  `@context` / `@type` / `@id`. Emphasize: the structure comes from a
  **template** (always valid), the LLM only explains it.

### 5. How could ONE Record data be connected to an AviationLakehouse?
- Shows the platform narrative: this is an interface layer for a federated
  aviation data platform (RecordChat → RecordForge → ONE Record Server → ALH),
  not just a chatbot. (Deeper ALH mapping is on the v0.2 roadmap.)

## What to emphasize to a reviewer

- **Source-grounded** answers with citations.
- **Provider abstraction** + offline fallback (runs with zero secrets).
- **Domain-aware** ingestion (ontology/OpenAPI/markdown/JSON-LD chunked differently).
- **Separation of concerns**: thin API → pipeline → retriever/prompt/llm/domain.
- **Evaluation from day one**: `python scripts/evaluate_rag.py`.
