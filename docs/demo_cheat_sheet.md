# RecordChat v0.2.3 Demo Cheat Sheet

Use this during a live demo. It is the short companion to
`docs/demo_script.md`.

## Positioning

Use this line:

> "RecordChat is a grounded AI assistant for IATA ONE Record with streaming
> answers, citations, ontology awareness, JSON-LD output, and NE:ONE
> implementation guidance."

## Quick Checks

Run:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/ingest
cd backend && ./.venv/bin/pytest tests/test_chat_api.py tests/test_pipeline.py tests/test_providers.py tests/test_health.py -q
cd ../frontend && npm run build
```

Check:

- `/health` is OK and shows configured providers
- `/ingest` indexes chunks
- backend tests pass
- frontend build passes

## Demo Flow

1. `What is ONE Record?`
2. `What is a LogisticsObject in ONE Record?`
3. `What properties connect Shipment to Piece in the ONE Record ontology?`
4. `Generate a JSON-LD example for a Piece.`
5. `How do I start NE:ONE locally with docker compose?`

## What To Highlight

- answers stream into the UI
- query type badge is visible
- citations stay grounded
- related concepts appear for concept / ontology questions
- JSON-LD lands in the structured output panel
- implementation prompts cite NE:ONE material

## If You Are Demoing From A VPS

- open `http://<your-vps-host>:3000`
- run `curl -X POST http://127.0.0.1:8000/ingest` on the VPS shell
- set `CORS_ORIGINS=http://<your-vps-host>:3000` if needed
- leave `NEXT_PUBLIC_API_BASE_URL` empty unless you need an override

## Strong Backup Prompts

- `ONE Record 里的 Piece 是什么？`
- `Shipment 和 Piece 在 ontology 里通过什么属性关联？`
- `Explain the relationship between Shipment and Piece.`
- `What is a Waybill in ONE Record?`

## If Someone Asks About Limitations

Use this:

> "This release is strongest on ONE Record core knowledge and developer support.
> The next milestone is workflow orchestration, not a bigger platform narrative."

## 3-Minute Version

Do only these:

1. `What is ONE Record?`
2. `What properties connect Shipment to Piece in the ONE Record ontology?`
3. `How do I start NE:ONE locally with docker compose?`
