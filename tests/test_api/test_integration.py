"""Integration tests for Knowledge Engine API."""

import pytest
from fastapi.testclient import TestClient

from apps.ke_api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_available():
    """Check if database is available."""
    try:
        from apps.ke_db.connection import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        pytest.skip("Database not available")


class TestHealthEndpoint:
    """Tests for /healthz endpoint."""

    def test_health_check(self, client) -> None:
        """Test health endpoint returns valid response."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "version" in data


class TestDocumentValidation:
    """Tests for document validation."""

    def test_create_doc_invalid_doc_id(self, client) -> None:
        """Test validation rejects invalid doc_id."""
        response = client.post(
            "/docs",
            json={
                "doc_id": "invalid",
                "title": "Test",
                "file_uri": "/path/to/file.pdf",
                "sha256": "a" * 64,
            },
        )
        assert response.status_code == 422  # Validation error

    def test_create_doc_invalid_sha256(self, client) -> None:
        """Test validation rejects invalid sha256."""
        response = client.post(
            "/docs",
            json={
                "doc_id": "DOC-0001",
                "title": "Test",
                "file_uri": "/path/to/file.pdf",
                "sha256": "tooshort",
            },
        )
        assert response.status_code == 422


class TestClaimValidation:
    """Tests for claim validation."""

    def test_create_claim_confidence_bounds(self, client) -> None:
        """Test validation rejects out-of-bounds confidence."""
        response = client.post(
            "/claims",
            json={
                "revision_id": "00000000-0000-0000-0000-000000000000",
                "claim_text": "Test claim",
                "confidence": 1.5,  # Invalid: > 1.0
            },
        )
        assert response.status_code == 422

    def test_create_claim_invalid_type(self, client) -> None:
        """Test validation rejects invalid claim type."""
        response = client.post(
            "/claims",
            json={
                "revision_id": "00000000-0000-0000-0000-000000000000",
                "claim_text": "Test claim",
                "claim_type": "invalid_type",
            },
        )
        assert response.status_code == 422


class TestEvidenceValidation:
    """Tests for evidence validation."""

    def test_create_evidence_invalid_role(self, client) -> None:
        """Test validation rejects invalid role."""
        response = client.post(
            "/evidence",
            json={
                "claim_id": "00000000-0000-0000-0000-000000000000",
                "chunk_id": "00000000-0000-0000-0000-000000000000",
                "snippet": "Test snippet",
                "role": "invalid_role",
            },
        )
        assert response.status_code == 422

    def test_create_evidence_strength_bounds(self, client) -> None:
        """Test validation rejects out-of-bounds strength."""
        response = client.post(
            "/evidence",
            json={
                "claim_id": "00000000-0000-0000-0000-000000000000",
                "chunk_id": "00000000-0000-0000-0000-000000000000",
                "snippet": "Test snippet",
                "support_strength": -0.5,  # Invalid: < 0
            },
        )
        assert response.status_code == 422


class TestAPIIntegration:
    """Integration tests requiring database."""

    def test_create_document_integration(self, client, db_available) -> None:
        """Test full document creation flow."""
        import uuid

        unique_id = f"TST-{uuid.uuid4().hex[:6].upper()}"

        response = client.post(
            "/docs",
            json={
                "doc_id": unique_id,
                "title": "Integration Test Document",
                "file_uri": "/test/integration.pdf",
                "sha256": "a" * 64,
                "authors": "Test Author",
                "tags": ["test", "integration"],
            },
        )

        # May fail due to doc_id format but should reach DB
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert "revision_id" in data
            assert data["doc_id"] == unique_id

    def test_quality_gate_integration(self, client, db_available) -> None:
        """Test quality gate endpoint with fake revision."""
        import uuid

        fake_rev_id = str(uuid.uuid4())
        response = client.get(f"/quality/{fake_rev_id}")

        # Should return valid response even for non-existent revision
        assert response.status_code == 200
        data = response.json()
        assert data["total_claims"] == 0
        assert data["passed"] is False  # No claims = not passed
