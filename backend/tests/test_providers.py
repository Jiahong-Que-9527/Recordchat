from pytest import raises

from app.core.config import Settings
from app.core.embeddings import OpenAICompatEmbeddingProvider, build_embedding_provider
from app.core.llm import ClaudeLLMProvider, OpenAICompatLLMProvider, build_llm_provider


def test_embedding_factory_requires_api_key():
    with raises(ValueError, match="EMBEDDING_API_KEY"):
        build_embedding_provider(Settings(embedding_provider="openai", embedding_api_key=""))


def test_llm_factory_requires_api_key():
    with raises(ValueError, match="LLM_API_KEY"):
        build_llm_provider(Settings(llm_provider="openai", llm_api_key=""))


def test_embedding_factory_builds_openai_compat_provider():
    provider = build_embedding_provider(
        Settings(
            embedding_provider="openai",
            embedding_api_key="test-key",
            embedding_model="text-embedding-3-small",
            embedding_base_url="https://api.openai.com/v1",
            embedding_dim=1536,
        )
    )
    assert isinstance(provider, OpenAICompatEmbeddingProvider)
    assert provider.dim == 1536


def test_llm_factory_builds_openai_compat_provider():
    provider = build_llm_provider(
        Settings(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4o-mini",
            llm_base_url="https://api.openai.com/v1",
        )
    )
    assert isinstance(provider, OpenAICompatLLMProvider)


def test_llm_factory_builds_claude_provider():
    provider = build_llm_provider(
        Settings(
            llm_provider="claude",
            llm_api_key="test-key",
            llm_model="claude-3-5-sonnet-latest",
            llm_base_url="https://api.anthropic.com",
        )
    )
    assert isinstance(provider, ClaudeLLMProvider)
