from pytest import raises

from app.core.config import Settings
from app.core.embeddings import OpenAICompatEmbeddingProvider, build_embedding_provider
from app.core.llm import (
    ALLOWED_CHAT_MODELS,
    ClaudeLLMProvider,
    OpenAICompatLLMProvider,
    build_llm_provider,
)


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


def test_llm_factory_rejects_unsupported_chat_model_override():
    with raises(ValueError, match="Unsupported chat model"):
        build_llm_provider(
            Settings(
                llm_provider="openai",
                llm_api_key="test-key",
                llm_model="deepseek-v4-flash",
                llm_base_url="https://api.deepseek.com",
            ),
            model="deepseek-v4-fast",
        )


def test_allowed_chat_models_match_supported_deepseek_variants():
    assert ALLOWED_CHAT_MODELS == {"deepseek-v4-flash", "deepseek-v4-pro"}
