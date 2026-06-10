"""LLM provider abstraction (SPEC section 7 / 14).

Business code depends ONLY on the `LLMProvider` interface and
`get_llm_provider()`. Switching between external providers is a config
change, not a code change.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, *, system: str, user: str) -> str:
        """Return the model's text completion for a system+user prompt."""

    @abstractmethod
    def complete_stream(self, *, system: str, user: str) -> Iterator[str]:
        """Yield text deltas for a system+user prompt."""


class OpenAICompatLLMProvider(LLMProvider):
    """Chat-completions client for OpenAI and Qwen (DashScope compat mode)."""

    def __init__(self, *, model: str, api_key: str, base_url: str) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def complete(self, *, system: str, user: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def complete_stream(self, *, system: str, user: str) -> Iterator[str]:
        with httpx.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
                "stream": True,
            },
            timeout=180,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                data = json.loads(payload)
                delta = data["choices"][0]["delta"].get("content", "")
                if delta:
                    yield delta


class ClaudeLLMProvider(LLMProvider):
    """Anthropic Messages API client."""

    def __init__(self, *, model: str, api_key: str, base_url: str) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")

    def complete(self, *, system: str, user: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def complete_stream(self, *, system: str, user: str) -> Iterator[str]:
        with httpx.stream(
            "POST",
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": f"{self.api_key}",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": self.model,
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": user}],
                "stream": True,
            },
            timeout=180,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                data = json.loads(payload)
                if data.get("type") != "content_block_delta":
                    continue
                delta = data.get("delta", {}).get("text", "")
                if delta:
                    yield delta


_LLM_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


ALLOWED_CHAT_MODELS = {"deepseek-v4-fast", "deepseek-v4-pro"}


def build_llm_provider(settings: Settings, *, model: str | None = None) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if not settings.llm_api_key:
        raise ValueError(
            f"LLM provider {provider!r} requires LLM_API_KEY to be configured."
        )
    selected_model = model or settings.llm_model
    if model and model not in ALLOWED_CHAT_MODELS:
        raise ValueError(
            f"Unsupported chat model {model!r}. Expected one of: {', '.join(sorted(ALLOWED_CHAT_MODELS))}."
        )

    if provider == "claude":
        return ClaudeLLMProvider(
            model=selected_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    base_url = settings.llm_base_url or _LLM_BASE_URLS.get(provider, "")
    if not base_url:
        raise ValueError(
            f"Unknown LLM provider {provider!r}. Expected one of: openai, qwen, claude."
        )

    return OpenAICompatLLMProvider(
        model=selected_model,
        api_key=settings.llm_api_key,
        base_url=base_url,
    )
_providers: dict[str, LLMProvider] = {}


def get_llm_provider(*, model: str | None = None) -> LLMProvider:
    settings = get_settings()
    selected_model = model or settings.llm_model
    if selected_model not in _providers:
        _providers[selected_model] = build_llm_provider(settings, model=model)
    return _providers[selected_model]
