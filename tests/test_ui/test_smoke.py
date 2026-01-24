"""Smoke tests for UI module.

These tests verify the UI can be imported without side effects.
"""

import pytest


class TestUIImport:
    """Test that UI modules can be imported safely."""

    def test_ui_lib_db_import(self) -> None:
        """Test that db module imports without connecting to DB."""
        from apps.ke_ui.ui_lib import db

        assert hasattr(db, "check_db_connection")
        assert hasattr(db, "get_applied_migrations")

    def test_ui_lib_state_import(self) -> None:
        """Test that state module imports without side effects."""
        from apps.ke_ui.ui_lib import state

        assert hasattr(state, "get_taxonomy_tree")
        assert hasattr(state, "get_dq_report")

    def test_ke_db_import(self) -> None:
        """Test that ke_db module imports without side effects."""
        from apps import ke_db

        assert hasattr(ke_db, "get_connection")
        assert hasattr(ke_db, "create_document")
        assert hasattr(ke_db, "check_quality_gate")

    def test_ke_db_utils(self) -> None:
        """Test ke_db utilities work without DB."""
        from apps.ke_db.utils import validate_doc_id, validate_confidence

        assert validate_doc_id("DOC-0001") is True
        assert validate_doc_id("invalid") is False
        assert validate_confidence(0.5) is True

    def test_streamlit_optional(self) -> None:
        """Test that streamlit is available when ui extra is installed."""
        try:
            import streamlit

            assert streamlit.__version__
        except ImportError:
            pytest.skip("Streamlit not installed (ui extra not enabled)")


class TestUIIntegration:
    """Integration tests requiring database."""

    @pytest.fixture
    def db_available(self):
        """Check if database is available."""
        try:
            from apps.ke_db.connection import get_connection

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except Exception:
            pytest.skip("Database not available")

    def test_list_documents_empty(self, db_available) -> None:
        """Test listing documents (may be empty)."""
        from apps.ke_db.connection import get_connection
        from apps.ke_db.documents import list_documents

        with get_connection() as conn:
            docs = list_documents(conn, limit=10)
            assert isinstance(docs, list)

    def test_quality_gate_query(self, db_available) -> None:
        """Test quality gate query structure."""
        from uuid import uuid4

        from apps.ke_db.connection import get_connection
        from apps.ke_db.quality import check_quality_gate

        # Use random UUID (won't exist, but query should work)
        fake_rev_id = uuid4()
        with get_connection() as conn:
            result = check_quality_gate(conn, fake_rev_id)
            assert "passed" in result
            assert "total_claims" in result
            assert result["total_claims"] == 0  # No claims for fake revision
