# RecordChat v0.1 Demo Guide

This guide is designed for a full v0.1 walkthrough, not just a quick smoke test.
It is written for a 5-10 minute live demo and assumes the project is running in
its default API-backed mode unless otherwise noted.

## 1. Demo Goal

The demo should make three points clear:

1. RecordChat is a domain-specific assistant for IATA ONE Record, not a generic chatbot.
2. Answers are grounded in retrievable sources and can show citations.
3. The v0.1 system already has an end-to-end architecture: ingest -> embeddings ->
   vector retrieval -> prompt assembly -> answer -> UI rendering.

## 2. What You Are Demoing

In the default v0.1 setup, the live system is using:

- `data/raw/ontology/one_record_core.ttl`
- `data/raw/one_record_docs/data_sharing.md`
- `data/raw/api_specs/one_record_api.yaml`
- `data/raw/examples/piece_example.jsonld`
- the curated glossary from `backend/app/domain/glossary.py`

And the runtime path is:

- external embedding API
- Qdrant: vector storage and retrieval
- external LLM API
- template-based JSON-LD generation from `backend/app/domain/jsonld_generator.py`

That means the v0.1 demo is about a complete working retrieval pipeline backed
by production-style model APIs rather than offline fallbacks.

Important framing:

- this demo proves the end-to-end product loop
- it does **not** mean the source base is already broad enough for the final
  intended scope
- after `v0.1`, the next priority is expanding the official ONE Record and
  NE:ONE source base before piling on more downstream features

## 3. Recommended Demo Modes

### Option A: Docker demo

Best when you want the cleanest "one command stack" story.

```bash
cp .env.example .env
docker compose up --build
curl -X POST localhost:8000/ingest
```

Open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

If you are running the stack on a VPS but opening the frontend in a browser on
your laptop:

- open `http://<your-vps-host>:3000`
- run `curl -X POST http://127.0.0.1:8000/ingest` on the VPS shell
- if needed, set:
  `CORS_ORIGINS=http://<your-vps-host>:3000`
  `NEXT_PUBLIC_API_BASE_URL=http://<your-vps-host>:8000`

The frontend now auto-detects the backend host from the page URL when
`NEXT_PUBLIC_API_BASE_URL` is empty, so `http://<your-vps-host>:3000` will
default to calling `http://<your-vps-host>:8000`.

### Option B: Local dev demo

Best when you want to narrate the backend and frontend separately.

Backend:

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
curl -X POST localhost:8000/ingest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## 4. Pre-Demo Checklist

Run these before anyone is watching:

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/ingest
cd backend && uv run pytest -q
cd ../frontend && npm run build
```

What you want to confirm:

- `/health` returns `status=ok` plus the active LLM / embedding provider summary
- `/ingest` reports non-zero `chunks_indexed`
- backend tests pass
- frontend build passes

## 5. Suggested Demo Narrative

Use this story arc:

1. Explain the problem:
   ONE Record is important, but the ontology, API concepts, and JSON-LD shape
   are hard to approach quickly.
2. Explain the product:
   RecordChat is an interface layer over ONE Record knowledge.
3. Explain the trust model:
   it uses retrieval and citations instead of freeform answering.
4. Explain the engineering point:
   it uses production-style external model APIs, provider abstraction, and a
   governed source base rather than a generic chatbot prompt.

Short positioning line:

> "This v0.1 is a production-minded MVP for querying ONE Record concepts,
> relationships, API ideas, and JSON-LD examples through a grounded RAG flow."

## 6. Main Demo Flow

These are the recommended live prompts in order.

### Prompt 1: open with the standard

Ask:

`What is ONE Record?`

What to highlight:

- The answer is concept-oriented, not generic logistics fluff.
- The Sources section is visible.
- This establishes that the assistant is grounded in retrieved domain material.

Suggested narration:

> "I start here because the system should orient a new user quickly and show
> that the answer is tied to a source, not just invented."

### Prompt 2: establish the core data model

Ask:

`What is a LogisticsObject in ONE Record?`

What to highlight:

- The answer should mention it as a base object in the model.
- Related concepts should appear in the UI.
- This shows the system is not only retrieving text, but also enriching the
  result with domain relationships.

Suggested narration:

> "This is a good example of the project knowing the backbone of the domain:
> LogisticsObject, Shipment, Piece, and related entities."

### Prompt 3: demonstrate relationship reasoning

Ask:

`Explain the relationship between Shipment and Piece.`

What to highlight:

- The query is routed as a relationship question.
- Related concepts should reinforce the entity graph.
- This is where you mention the curated relationship map in v0.1 and the
  future ontology-aware path in v0.2.

Suggested narration:

> "In v0.2.1, relationships are boosted using the parsed ONE Record ontology —
> object properties like containedPieces and subClassOf links — with the curated
> map as fallback."

### Prompt 4: show JSON-LD generation

Ask:

`Generate a JSON-LD example for a Piece.`

What to highlight:

- A JSON-LD block appears in the UI.
- `@context`, `@type`, and `@id` are present.
- The structure is template-generated, not freehand LLM output.

Suggested narration:

> "This matters because I don't want the model hallucinating data structure.
> The structure is controlled by templates, and the assistant explains it."

### Prompt 5: show implementation support beyond pure concepts

Ask:

`How do I start NE:ONE locally with docker compose?`

What to highlight:

- The system can answer practical implementation questions, not just glossary questions.
- The answer should cite NE:ONE-derived sources.
- This shows the broadened source pack is actually being used.

Suggested narration:

> "This is where the product becomes useful for developers, not just explainers:
> the assistant can bridge from ONE Record concepts into NE:ONE setup and
> implementation guidance with citations."

Useful closing line:

> "The next step is not just adding more features. The next step is broadening
> the knowledge base so these answers are grounded in a richer official and
> implementation-level source pack."

## 7. Strong Prompt Examples

These are good prompts to have ready in a notes app during a live session.

### Concept prompts

- `What is ONE Record?`
- `What is a LogisticsObject?`
- `What is a Piece in ONE Record?`
- `What is a Shipment?`
- `What is a Waybill in ONE Record?`
- `What is a TransportMovement?`
- `What is the role of JSON-LD in ONE Record?`
- `What is a Subscription in ONE Record?`
- `What is a Notification in ONE Record?`

### Relationship prompts

- `Explain the relationship between Shipment and Piece.`
- `What is the difference between a Waybill and a Shipment?`
- `How is a Piece related to a LogisticsObject?`
- `How do TransportMovement and LogisticsEvent connect?`
- `How are Subscription and Notification related in ONE Record?`

### API and workflow prompts

- `How does the ONE Record API let me create a LogisticsObject?`
- `How does subscription and notification work in ONE Record?`
- `What kind of API concepts are represented in this knowledge base?`
- `How would a ONE Record server expose logistics objects?`

### JSON-LD prompts

- `Generate a JSON-LD example for a Piece.`
- `Generate a JSON-LD example for a Shipment.`
- `Generate a JSON-LD example for a Waybill.`
- `Generate a JSON-LD example for a TransportMovement.`
- `Explain the fields in this JSON-LD example for a Piece.`

### Ontology and implementation prompts

- `How does ONE Record support data sharing across the supply chain?`
- `Why is JSON-LD useful for ONE Record?`
- `Which class is Shipment a subclass of?`
- `What properties connect Shipment to Piece in the ONE Record ontology?`
- `How do I start NE:ONE locally with docker compose?`
- `How do I create a LogisticsObject against NE:ONE?`

## 8. Best Prompt Sets by Audience

### For an engineering audience

Use these:

- `What is a LogisticsObject in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `How does the ONE Record API let me create a LogisticsObject?`
- `Generate a JSON-LD example for a Piece.`

What to emphasize:

- retrieval architecture
- provider abstraction
- API-backed model calls
- template-based structured output

### For a product or platform audience

Use these:

- `What is ONE Record?`
- `How does ONE Record support data sharing across the supply chain?`
- `What properties connect Shipment to Piece in the ONE Record ontology?`
- `Generate a JSON-LD example for a Piece.`
- `How do I start NE:ONE locally with docker compose?`

What to emphasize:

- domain accessibility
- trust through citations
- progression from concept understanding to implementation help

### For a logistics-domain audience

Use these:

- `What is a Shipment?`
- `What is a Piece?`
- `What is a Waybill in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `How do subscription and notification work in ONE Record?`
- `How do I start NE:ONE locally with docker compose?`
- `How do I create a LogisticsObject against NE:ONE?`

What to emphasize:

- terminology clarity
- entity relationships
- operational meaning
- implementation guidance when NE:ONE sources are relevant

## 9. Fallback Prompts If a Live Answer Feels Weak

Because the current demo is strongest on ONE Record core concepts, ontology, and
NE:ONE implementation support, some prompts are better than others. If a
response feels too thin, move to these:

- `What is a Piece in ONE Record?`
- `What is a LogisticsObject in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `Generate a JSON-LD example for a Piece.`
- `What is the role of JSON-LD in ONE Record?`
- `How do I start NE:ONE locally with docker compose?`

These tend to align most strongly with the current glossary + raw source set.

## 10. What to Say About Limitations

If someone asks what is not yet in v0.1, use this answer:

> "This version is intentionally focused: it already has an end-to-end RAG
> path, but it still uses a small curated knowledge base and external model
> APIs. The immediate next steps are strengthening streaming UI and workflow
> execution, not broad platform storytelling first."

If someone asks whether it uses a real hosted model:

> "Yes. The current runtime uses external APIs for both embeddings and text
> generation, while keeping provider selection configurable."

## 11. CLI Prompt Examples

If you want to demo from terminal instead of the UI:

```bash
curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"What is ONE Record?"}'
```

```bash
curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"Explain the relationship between Shipment and Piece."}'
```

```bash
curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"Generate a JSON-LD example for a Piece."}'
```

```bash
curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"How do I start NE:ONE locally with docker compose?"}'
```

## 12. A Clean 5-Minute Version

If you only have five minutes, do exactly this:

1. Show the UI and say what the project is.
2. Ask `What is ONE Record?`
3. Ask `What is a LogisticsObject in ONE Record?`
4. Ask `Explain the relationship between Shipment and Piece.`
5. Ask `Generate a JSON-LD example for a Piece.`
6. Close with `How do I start NE:ONE locally with docker compose?`

Closing line:

> "So v0.1 already proves the full loop: curated and raw ONE Record knowledge
> can be ingested, embedded, retrieved, explained with citations, and rendered
> in a focused UI, including ontology-aware answers and stable JSON-LD generation."
