# RecordChat Backend

FastAPI backend for RecordChat — a domain-specific AI assistant for IATA ONE Record.

See the top-level [SPEC.md](../SPEC.md) and [README.md](../README.md) for the full picture.

## Quickstart (local, offline)

```bash
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
# in another shell:
curl -X POST localhost:8000/ingest
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is a Piece in ONE Record?"}' | jq
```

With no API keys configured the backend runs fully offline: `local` LLM +
`local` hashing embeddings + in-memory Qdrant. Set the `LLM_*` / `EMBEDDING_*`
/ `QDRANT_*` env vars (see [../.env.example](../.env.example)) for real models.

Note:

- the current backend is fully usable for `v0.1` demos
- the next project priority is broadening the imported official ONE Record and
  NE:ONE source pack, not adding more backend features first
- see [../docs/data_source_plan.md](../docs/data_source_plan.md)

## Tests

```bash
uv run pytest -q
```
