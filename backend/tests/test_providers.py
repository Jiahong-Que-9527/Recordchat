from app.core.config import Settings
from app.core.embeddings import LocalHashEmbeddingProvider, build_embedding_provider
from app.core.llm import LocalLLMProvider, build_llm_provider


def test_embedding_factory_falls_back_to_local_without_key():
    s = Settings(embedding_provider="openai", embedding_api_key="")
    assert isinstance(build_embedding_provider(s), LocalHashEmbeddingProvider)


def test_llm_factory_falls_back_to_local_without_key():
    s = Settings(llm_provider="openai", llm_api_key="")
    assert isinstance(build_llm_provider(s), LocalLLMProvider)


def test_local_embedding_is_deterministic_and_normalized():
    p = LocalHashEmbeddingProvider(dim=128)
    a = p.embed_one("ONE Record Piece")
    b = p.embed_one("ONE Record Piece")
    assert a == b
    assert len(a) == 128
    norm = sum(x * x for x in a) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_local_llm_grounds_in_context():
    llm = LocalLLMProvider()
    out = llm.complete(
        system="sys",
        user="CONTEXT:\nA Piece is the smallest unit.\n\nQUESTION: What is a Piece?",
    )
    assert "Piece" in out
