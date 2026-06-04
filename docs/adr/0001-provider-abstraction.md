# ADR 0001: Provider abstraction with offline-first fallback

## Status
Accepted (v0.1)

## Context
RecordChat must work across multiple LLM/embedding vendors (Qwen, OpenAI,
Claude) and be demoable/testable without secrets or network access.

## Decision
- Define abstract `LLMProvider`, `EmbeddingProvider`, and `Retriever` interfaces.
- Concrete implementations are selected by environment variables via factories
  in `core/` and `rag/retriever.py`.
- Ship a `local` implementation for both LLM (extractive, grounded in retrieved
  context) and embeddings (deterministic hashing bag-of-words), plus an
  in-process Qdrant (`QDRANT_URL=:memory:`).
- A configured provider with a **missing API key** logs a warning and falls back
  to `local` rather than crashing.

## Consequences
- Switching vendors is a config change, not a code change.
- Tests and demos run offline with zero secrets.
- The `local` providers are intentionally low-fidelity; real retrieval/answer
  quality requires configuring a real provider. This is acceptable for v0.1 and
  documented in the README.
