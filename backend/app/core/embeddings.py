"""Embedding provider abstraction (SPEC section 7 / 14).

Switching providers must not require touching business code — call
`get_embedding_provider()` and use the `EmbeddingProvider` interface.

The `local` provider is a deterministic, dependency-free hashing
bag-of-words embedding. It is NOT semantically strong, but it makes the
whole project runnable offline with no API key (graceful degradation),
and gives reasonable lexical retrieval for the demo/tests.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class LocalHashEmbeddingProvider(EmbeddingProvider):
    """Deterministic hashing bag-of-words embedding (offline fallback)."""

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _TOKEN_RE.findall(text.lower()):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class OpenAICompatEmbeddingProvider(EmbeddingProvider):
    """Works with OpenAI and Qwen (DashScope OpenAI-compatible) embedding APIs."""

    def __init__(self, *, model: str, api_key: str, base_url: str, dim: int) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        data.sort(key=lambda d: d["index"])
        return [d["embedding"] for d in data]


# Default OpenAI-compatible base URLs per provider.
_EMBED_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "local":
        return LocalHashEmbeddingProvider(dim=settings.embedding_dim)

    if not settings.embedding_api_key:
        logger.warning(
            "EMBEDDING_PROVIDER=%s but EMBEDDING_API_KEY is empty; "
            "falling back to local hashing embeddings.",
            provider,
        )
        return LocalHashEmbeddingProvider(dim=settings.embedding_dim)

    base_url = settings.llm_base_url or _EMBED_BASE_URLS.get(provider, "")
    if not base_url:
        logger.warning("Unknown embedding provider %r; falling back to local.", provider)
        return LocalHashEmbeddingProvider(dim=settings.embedding_dim)

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
