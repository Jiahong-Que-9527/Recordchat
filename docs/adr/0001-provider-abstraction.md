# ADR 0001: Provider abstraction for external model APIs

## Status
Accepted (v0.1)

## Context
RecordChat must work across multiple LLM/embedding vendors (Qwen, OpenAI,
Claude) without business-logic changes, while tests use explicit stubs rather
than production fallbacks.

## Decision
- Define abstract `LLMProvider`, `EmbeddingProvider`, and `Retriever` interfaces.
- Concrete implementations are selected by environment variables via factories
  in `core/` and `rag/retriever.py`.
- Production providers are API-backed and selected by environment variables via
  factories in `core/` and `rag/retriever.py`.
- A configured provider with a missing API key is treated as a configuration
  error and fails fast.
- Tests use explicit fake providers when they need to avoid external calls.

## Consequences
- Switching vendors is a config change, not a code change.
- Misconfigured secrets fail early instead of silently degrading answer quality.
- Tests remain deterministic because they inject fake providers directly.
