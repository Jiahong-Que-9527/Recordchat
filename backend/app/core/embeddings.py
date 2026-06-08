"""Embedding provider abstraction (SPEC section 7 / 14).

Switching providers must not require touching business code — call
`get_embedding_provider()` and use the `EmbeddingProvider` interface.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from itertools import islice

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_EMBED_BATCH_SIZE = 128
_EMBED_TIMEOUT_SECONDS = 180
_EMBED_MAX_RETRIES = 3
_EMBED_RETRY_DELAY_SECONDS = 2


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class OpenAICompatEmbeddingProvider(EmbeddingProvider):
    """Works with OpenAI and Qwen (DashScope OpenAI-compatible) embedding APIs."""

    def __init__(self, *, model: str, api_key: str, base_url: str, dim: int) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for batch in _batched(texts, _EMBED_BATCH_SIZE):
            resp = _post_embedding_batch(
                base_url=self.base_url,
                api_key=self.api_key,
                model=self.model,
                batch=batch,
            )
            data = resp.json()["data"]
            data.sort(key=lambda d: d["index"])
            vectors.extend(d["embedding"] for d in data)
        return vectors


def _batched(items: list[str], size: int) -> list[list[str]]:
    it = iter(items)
    out: list[list[str]] = []
    while batch := list(islice(it, size)):
        out.append(batch)
    return out


def _post_embedding_batch(*, base_url: str, api_key: str, model: str, batch: list[str]) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(1, _EMBED_MAX_RETRIES + 1):
        try:
            resp = httpx.post(
                f"{base_url}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "input": batch},
                timeout=_EMBED_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            return resp
        except httpx.TimeoutException as exc:
            last_error = exc
            if attempt == _EMBED_MAX_RETRIES:
                break
            logger.warning(
                "Embedding batch timed out (attempt %d/%d, batch_size=%d); retrying in %ds",
                attempt,
                _EMBED_MAX_RETRIES,
                len(batch),
                _EMBED_RETRY_DELAY_SECONDS,
            )
            time.sleep(_EMBED_RETRY_DELAY_SECONDS)
    assert last_error is not None
    raise last_error


# Default OpenAI-compatible base URLs per provider.
_EMBED_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if not settings.embedding_api_key:
        raise ValueError(
            f"Embedding provider {provider!r} requires EMBEDDING_API_KEY to be configured."
        )

    base_url = settings.embedding_base_url or _EMBED_BASE_URLS.get(provider, "")
    if not base_url:
        raise ValueError(
            f"Unknown embedding provider {provider!r}. Expected one of: openai, qwen."
        )

    return OpenAICompatEmbeddingProvider(
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        base_url=base_url,
        dim=settings.embedding_dim,
    )


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = build_embedding_provider(get_settings())
    return _provider
