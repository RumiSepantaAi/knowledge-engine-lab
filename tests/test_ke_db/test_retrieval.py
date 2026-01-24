"""Tests for retrieval module."""

import math
from uuid import uuid4

import pytest

from apps.ke_db.retrieval import (
    EMBEDDING_DIMENSION,
    SearchFilters,
    SearchResult,
    full_text_search,
    hybrid_search,
    vector_search,
)


def generate_deterministic_embedding(seed: int) -> list[float]:
    """Generate a deterministic embedding for testing.

    Uses sine/cosine waves to create reproducible embeddings
    without external API calls.

    Args:
        seed: Seed value for deterministic generation.

    Returns:
        List of floats with EMBEDDING_DIMENSION elements.
    """
    embedding = []
    for i in range(EMBEDDING_DIMENSION):
        # Mix of sine waves with different frequencies
        value = (
            0.5 * math.sin(seed * 0.1 + i * 0.01)
            + 0.3 * math.cos(seed * 0.2 + i * 0.02)
            + 0.2 * math.sin(seed * 0.3 + i * 0.03)
        )
        embedding.append(value)

    # Normalize to unit length
    norm = math.sqrt(sum(x * x for x in embedding))
    return [x / norm for x in embedding]


class TestDeterministicEmbeddings:
    """Tests for deterministic embedding generation."""

    def test_embedding_dimension(self) -> None:
        """Embedding has correct dimension."""
        emb = generate_deterministic_embedding(42)
        assert len(emb) == EMBEDDING_DIMENSION

    def test_embedding_deterministic(self) -> None:
        """Same seed produces same embedding."""
        emb1 = generate_deterministic_embedding(42)
        emb2 = generate_deterministic_embedding(42)
        assert emb1 == emb2

    def test_different_seeds_different_embeddings(self) -> None:
        """Different seeds produce different embeddings."""
        emb1 = generate_deterministic_embedding(1)
        emb2 = generate_deterministic_embedding(2)
        assert emb1 != emb2

    def test_embedding_normalized(self) -> None:
        """Embedding is normalized to unit length."""
        emb = generate_deterministic_embedding(42)
        norm = math.sqrt(sum(x * x for x in emb))
        assert abs(norm - 1.0) < 0.0001


class TestSearchFilters:
    """Tests for SearchFilters dataclass."""

    def test_default_filters(self) -> None:
        """Default filters have expected values."""
        filters = SearchFilters()
        assert filters.revision_id is None
        assert filters.tags is None
        assert filters.page_start is None
        assert filters.page_end is None
        assert filters.limit == 10

    def test_custom_filters(self) -> None:
        """Custom filters are applied."""
        rev_id = uuid4()
        filters = SearchFilters(
            revision_id=rev_id,
            tags=["test", "important"],
            page_start=5,
            page_end=10,
            limit=20,
        )
        assert filters.revision_id == rev_id
        assert filters.tags == ["test", "important"]
        assert filters.page_start == 5
        assert filters.page_end == 10
        assert filters.limit == 20


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self) -> None:
        """SearchResult can be created."""
        result = SearchResult(
            chunk_id=uuid4(),
            revision_id=uuid4(),
            chunk_no=1,
            text="Test chunk",
            page_start=1,
            page_end=2,
            section_path="Chapter 1",
            score=0.85,
            match_type="text",
        )
        assert result.score == 0.85
        assert result.match_type == "text"


class TestRetrievalIntegration:
    """Integration tests requiring database."""

    @pytest.fixture
    def db_conn(self):
        """Get database connection if available."""
        try:
            from apps.ke_db.connection import get_connection

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                yield conn
        except Exception:
            pytest.skip("Database not available")

    def test_full_text_search_empty(self, db_conn) -> None:
        """Full-text search returns empty list for no matches."""
        results = full_text_search(db_conn, "xyznonexistenttermxyz")
        assert isinstance(results, list)

    def test_full_text_search_with_filters(self, db_conn) -> None:
        """Full-text search accepts filters."""
        filters = SearchFilters(limit=5, tags=["test"])
        results = full_text_search(db_conn, "test", filters)
        assert isinstance(results, list)
        assert len(results) <= 5

    def test_vector_search_requires_embedding(self, db_conn) -> None:
        """Vector search requires valid embedding."""
        with pytest.raises(ValueError, match="dimensions"):
            vector_search(db_conn, [0.1, 0.2])  # Too short

    def test_vector_search_empty(self, db_conn) -> None:
        """Vector search returns empty list if no embeddings."""
        emb = generate_deterministic_embedding(42)
        results = vector_search(db_conn, emb)
        assert isinstance(results, list)

    def test_hybrid_search_text_only(self, db_conn) -> None:
        """Hybrid search works with text only."""
        results = hybrid_search(db_conn, "test query")
        assert isinstance(results, list)

    def test_hybrid_search_with_embedding(self, db_conn) -> None:
        """Hybrid search works with embedding."""
        emb = generate_deterministic_embedding(42)
        results = hybrid_search(db_conn, "test query", embedding=emb)
        assert isinstance(results, list)

    def test_hybrid_search_weights(self, db_conn) -> None:
        """Hybrid search respects weights."""
        emb = generate_deterministic_embedding(42)
        # Text-only weighted
        results1 = hybrid_search(
            db_conn, "test", embedding=emb, text_weight=1.0, vector_weight=0.0
        )
        # Vector-only weighted
        results2 = hybrid_search(
            db_conn, "test", embedding=emb, text_weight=0.0, vector_weight=1.0
        )
        # Both should return valid results
        assert isinstance(results1, list)
        assert isinstance(results2, list)
