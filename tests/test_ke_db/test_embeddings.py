"""Tests for embedding providers."""

import pytest

from apps.ke_db.embeddings import (
    EMBEDDING_DIMENSION,
    DummyProvider,
    EmbeddingProvider,
    RemoteProvider,
    get_provider,
)


class TestDummyProvider:
    """Tests for DummyProvider."""

    def test_implements_interface(self) -> None:
        """DummyProvider implements EmbeddingProvider."""
        provider = DummyProvider()
        assert isinstance(provider, EmbeddingProvider)

    def test_dimension(self) -> None:
        """Dimension matches EMBEDDING_DIMENSION."""
        provider = DummyProvider()
        assert provider.dimension == EMBEDDING_DIMENSION

    def test_embed_single_text(self) -> None:
        """Can embed a single text."""
        provider = DummyProvider()
        embeddings = provider.embed_texts(["Hello world"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == EMBEDDING_DIMENSION

    def test_embed_multiple_texts(self) -> None:
        """Can embed multiple texts."""
        provider = DummyProvider()
        embeddings = provider.embed_texts(["Text 1", "Text 2", "Text 3"])
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == EMBEDDING_DIMENSION

    def test_deterministic(self) -> None:
        """Same text produces same embedding."""
        provider = DummyProvider()
        emb1 = provider.embed_texts(["test text"])[0]
        emb2 = provider.embed_texts(["test text"])[0]
        assert emb1 == emb2

    def test_different_texts_different_embeddings(self) -> None:
        """Different texts produce different embeddings."""
        provider = DummyProvider()
        emb1 = provider.embed_texts(["text one"])[0]
        emb2 = provider.embed_texts(["text two"])[0]
        assert emb1 != emb2

    def test_normalized(self) -> None:
        """Embeddings are normalized to unit length."""
        import math

        provider = DummyProvider()
        emb = provider.embed_texts(["test"])[0]
        norm = math.sqrt(sum(x * x for x in emb))
        assert abs(norm - 1.0) < 0.0001


class TestRemoteProvider:
    """Tests for RemoteProvider."""

    def test_implements_interface(self) -> None:
        """RemoteProvider implements EmbeddingProvider."""
        provider = RemoteProvider()
        assert isinstance(provider, EmbeddingProvider)

    def test_dimension(self) -> None:
        """Dimension matches EMBEDDING_DIMENSION."""
        provider = RemoteProvider()
        assert provider.dimension == EMBEDDING_DIMENSION

    def test_raises_without_api_key(self, monkeypatch) -> None:
        """Raises error when API key not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = RemoteProvider()
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            provider.embed_texts(["test"])


class TestGetProvider:
    """Tests for get_provider factory."""

    def test_get_dummy_provider(self) -> None:
        """Can get DummyProvider by name."""
        provider = get_provider("dummy")
        assert isinstance(provider, DummyProvider)

    def test_get_openai_provider(self) -> None:
        """Can get RemoteProvider by name."""
        provider = get_provider("openai")
        assert isinstance(provider, RemoteProvider)

    def test_auto_without_key(self, monkeypatch) -> None:
        """Auto selects DummyProvider when no API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = get_provider("auto")
        assert isinstance(provider, DummyProvider)

    def test_auto_with_key(self, monkeypatch) -> None:
        """Auto selects RemoteProvider when API key set."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        provider = get_provider("auto")
        assert isinstance(provider, RemoteProvider)

    def test_unknown_provider(self) -> None:
        """Raises error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent")


class TestEmbeddingIntegration:
    """Integration tests requiring database."""

    @pytest.fixture
    def db_conn(self):
        """Get database connection if available."""
        try:
            from apps.ke_db.connection import get_connection

            with get_connection() as conn:
                yield conn
        except Exception:
            pytest.skip("Database not available")

    def test_dummy_provider_with_retrieval(self, db_conn) -> None:
        """DummyProvider works with retrieval module."""
        from apps.ke_db.retrieval import vector_search

        provider = DummyProvider()
        emb = provider.embed_texts(["test query"])[0]

        # Should not raise even if no results
        results = vector_search(db_conn, emb)
        assert isinstance(results, list)
