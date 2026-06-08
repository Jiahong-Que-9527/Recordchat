# RecordChat Backend

FastAPI backend for RecordChat — a domain-specific AI assistant for IATA ONE Record.

See the top-level [SPEC.md](../SPEC.md) and [README.md](../README.md) for the full picture.

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
# in another shell:
curl -X POST localhost:8000/ingest
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' \
  -d '{"message":"What is a Piece in ONE Record?"}' | jq
```

The backend now requires external APIs for both LLM generation and embeddings.
Set the `LLM_*` / `EMBEDDING_*` / `QDRANT_*` env vars (see
[../.env.example](../.env.example)) before running it.

Note:

- the current backend is fully usable for `v0.1` demos
- the next project priority is broadening the imported official ONE Record and
  NE:ONE source pack, not adding more backend features first
- see [../docs/data_source_plan.md](../docs/data_source_plan.md)

## Tests

```bash
uv run pytest -q
```
