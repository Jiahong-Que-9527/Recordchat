# RecordChat v0.2.3 Demo Guide

This guide is the canonical live-demo script for the current frontend-upgrade
milestone. It assumes:

- API-only runtime for both LLM and embeddings
- FastAPI backend on `:8000`
- Next.js frontend on `:3000`
- Qdrant available either in Docker or via `QDRANT_URL`

## 1. Demo Goal

The current demo should establish five things:

1. RecordChat is a domain-specific ONE Record assistant, not a generic chatbot.
2. Answers stream in real time through the upgraded frontend.
3. Responses stay grounded in official / NE:ONE / ontology sources.
4. The UI surfaces domain metadata: query type, sources, related concepts, JSON-LD.
5. The stack is deployment-ready with external APIs, Docker, and a verified chat path.

## 2. What You Are Demoing

The current v0.2.3 system includes:

- broadened official ONE Record source pack
- validated ontology ingestion and ontology-aware retrieval
- NE:ONE implementation Q&A
- streaming backend endpoint: `POST /chat/stream`
- Next frontend running on AI SDK `useChat`
- RecordChat-specific inspector panel for grounded metadata

This is no longer a v0.1 “basic MVP UI” demo. It is a streaming, source-grounded
ONE Record assistant with a template-style chat shell.

## 3. Recommended Demo Modes

### Option A: Docker Compose

Best for a clean full-stack demo.

```bash
cp .env.example .env
docker compose up --build -d
curl -X POST http://127.0.0.1:8000/ingest
```

Open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

If you are running on a VPS:

- open `http://<your-vps-host>:3000` from your browser
- run `curl -X POST http://127.0.0.1:8000/ingest` on the VPS shell
- set `CORS_ORIGINS=http://<your-vps-host>:3000` if needed
- leave `NEXT_PUBLIC_API_BASE_URL` empty unless you explicitly want to override auto-detect

The frontend proxy route prefers `INTERNAL_API_BASE_URL` and otherwise infers
`http://<current-host>:8000`.

### Option B: Local Split Dev

Backend:

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Ingest:

```bash
curl -X POST http://127.0.0.1:8000/ingest
```

## 4. Pre-Demo Checklist

Run these before the live session:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/ingest
cd backend && ./.venv/bin/pytest tests/test_chat_api.py tests/test_pipeline.py tests/test_providers.py tests/test_health.py -q
cd ../frontend && npm run build
```

What to confirm:

- `/health` returns provider/model configuration summary
- `/ingest` reports non-zero indexed chunks
- backend tests pass
- frontend build passes
- the frontend is using the streaming chat shell, not the old single-response page

## 5. Suggested Positioning

Use this framing:

> "RecordChat is a grounded assistant for IATA ONE Record that can explain
> concepts, ontology relationships, JSON-LD structure, and NE:ONE implementation
> questions through a streaming chat interface with citations."

Short engineering line:

> "The frontend now runs on AI SDK chat transport, the backend streams tokens
> from the RAG pipeline, and the UI keeps RecordChat-specific domain panels."

## 6. Main Demo Flow

Use these five prompts in order.

### Prompt 1: open with the standard

Ask:

`What is ONE Record?`

Highlight:

- streamed answer starts quickly
- source-grounded explanation
- citations appear in the inspector and inline source cards

### Prompt 2: show the core data model

Ask:

`What is a LogisticsObject in ONE Record?`

Highlight:

- query type badge
- related concepts panel
- domain-specific explanation rather than generic logistics text

### Prompt 3: show ontology / relationship reasoning

Ask:

`What properties connect Shipment to Piece in the ONE Record ontology?`

Highlight:

- ontology-oriented answer
- citations should come from ontology-derived material
- this is the strongest way to show the ontology track is real, not just promised

### Prompt 4: show JSON-LD generation

Ask:

`Generate a JSON-LD example for a Piece.`

Highlight:

- JSON-LD panel renders in the inspector
- `@context`, `@type`, and `@id` are present
- answer text and structured output arrive together in the chat surface

### Prompt 5: show developer usefulness

Ask:

`How do I start NE:ONE locally with docker compose?`

Highlight:

- implementation question routing
- NE:ONE-specific citations
- this is where RecordChat stops being only a glossary assistant

## 7. Good Backup Prompts

- `ONE Record 里的 Piece 是什么？`
- `Shipment 和 Piece 在 ontology 里通过什么属性关联？`
- `What is a Waybill in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `How does ONE Record support data sharing?`

## 8. What To Say About Limitations

Use this:

> "The current milestone is strong on ONE Record concepts, ontology questions,
> JSON-LD, and NE:ONE implementation support. The next major step is workflow
> orchestration, not more ALH narrative yet."

If someone asks about model hosting:

> "The current runtime is API-only. Both generation and embeddings use external
> providers by configuration, which is the supported path going forward."

## 9. Terminal-Only Backup

If the frontend is unavailable, you can still show the backend:

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"What is ONE Record?"}'
```

And for ingestion:

```bash
curl -s -X POST http://127.0.0.1:8000/ingest
```

This is a fallback only. The preferred live demo is the streaming frontend on `:3000`.
