# RecordChat v0.1 Demo Cheat Sheet

Use this page during a live demo. It is the compressed version of
`docs/demo_script.md`.

## 1. Open With This

Use this positioning line:

> "RecordChat is a domain-specific AI assistant for IATA ONE Record. In v0.1,
> it already supports ingest, embeddings, vector retrieval, grounded answers,
> citations, and template-based JSON-LD generation."

If you want the shorter version:

> "This is a production-minded MVP for querying ONE Record concepts,
> relationships, API ideas, and JSON-LD examples through a grounded RAG flow."

## 2. Before Anyone Joins

Run:

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/ingest
cd backend && uv run pytest -q
cd ../frontend && npm run build
```

Check:

- `/health` is OK
- `/ingest` indexes chunks
- backend tests pass
- frontend build passes

If you are demoing from a VPS:

- run `curl -s -X POST http://127.0.0.1:8000/ingest` on the VPS shell
- open `http://<your-vps-host>:3000` from your laptop browser
- if you explicitly set frontend/backend hosts, use:
  `CORS_ORIGINS=http://<your-vps-host>:3000`
  `NEXT_PUBLIC_API_BASE_URL=http://<your-vps-host>:8000`

## 3. What To Say About The Current Runtime

Default v0.1 demo mode:

- data from `data/raw/*` plus curated glossary
- external embedding API
- Qdrant for vector retrieval
- external LLM API
- template-based JSON-LD generator

One-line explanation:

> "The default demo already uses provider abstraction for external embedding and
> generation APIs, while Qdrant stays local or remote depending on deployment."

Important qualifier:

> "The demo loop is complete, but the source base is still intentionally small.
> The next priority is broadening official ONE Record and NE:ONE coverage
> before piling on more features."

## 4. Core Demo Flow

### Prompt 1

Ask:

`What is ONE Record?`

Say:

> "I start here to orient the user and show that the answer is grounded in
> retrieved source material."

Highlight:

- source-grounded answer
- visible citations

### Prompt 2

Ask:

`What is a LogisticsObject in ONE Record?`

Say:

> "This shows the assistant understands the backbone of the data model, not
> just isolated terms."

Highlight:

- core entity explanation
- related concepts in UI

### Prompt 3

Ask:

`Explain the relationship between Shipment and Piece.`

Say:

> "This shows relationship-oriented retrieval and enrichment, which is a key
> part of making a domain assistant useful."

Highlight:

- relationship question routing
- related concept tags

### Prompt 4

Ask:

`Generate a JSON-LD example for a Piece.`

Say:

> "The structure is generated from templates, so the data shape is stable and
> not left to freeform LLM generation."

Highlight:

- `@context`
- `@type`
- `@id`
- JSON-LD code block

### Prompt 5

Ask:

`How could ONE Record data be connected to an AviationLakehouse?`

Say:

> "This places RecordChat inside a broader platform story, not just as a chat
> interface."

Highlight:

- platform narrative
- v0.2 and v0.3 roadmap setup

## 5. Best Backup Prompts

If a live answer feels weak, switch to one of these:

- `What is a Piece in ONE Record?`
- `What is a LogisticsObject in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `Generate a JSON-LD example for a Piece.`
- `What is the role of JSON-LD in ONE Record?`

## 6. Best Prompt Packs By Audience

### Engineering audience

- `What is a LogisticsObject in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `How does the ONE Record API let me create a LogisticsObject?`
- `Generate a JSON-LD example for a Piece.`

Focus on:

- retrieval pipeline
- provider abstraction
- API-backed model calls
- template-based structured output

### Product or platform audience

- `What is ONE Record?`
- `How does ONE Record support data sharing across the supply chain?`
- `Generate a JSON-LD example for a Piece.`
- `How could ONE Record data be connected to an AviationLakehouse?`

Focus on:

- accessibility
- trust through citations
- future platform narrative

### Logistics-domain audience

- `What is a Shipment?`
- `What is a Piece?`
- `What is a Waybill in ONE Record?`
- `Explain the relationship between Shipment and Piece.`
- `How do subscription and notification work in ONE Record?`

Focus on:

- terminology clarity
- relationships between entities
- operational meaning

## 7. If Someone Asks About Limitations

Use this:

> "This version is intentionally focused. It already has the full RAG path, but
> it still uses a small curated knowledge base and external model APIs. The
> immediate next step is
> expanding the official and NE:ONE source base; richer downstream features
> come after that."

If they ask whether it uses a real hosted model:

> "By default, no. The demo is designed to run offline. But the provider
> abstraction is already in place, so hosted models can be enabled by config
> rather than code changes."

## 8. If You Only Have 3 Minutes

Do this and stop:

1. `What is ONE Record?`
2. `Explain the relationship between Shipment and Piece.`
3. `Generate a JSON-LD example for a Piece.`

Closing line:

> "So v0.1 already proves the loop: ONE Record knowledge can be ingested,
> embedded, retrieved, explained with citations, and rendered in a focused UI."
