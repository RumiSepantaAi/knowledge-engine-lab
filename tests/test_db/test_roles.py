"""Tests for database role permissions."""

import pytest


class TestDBRoles:
    """Tests for database role security."""

    @pytest.fixture
    def ke_ro_connection(self):
        """Connection as ke_ro (read-only) role."""
        import os

        import psycopg

        # Build connection string for ke_ro
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "knowledge_engine")
        password = os.getenv("KE_RO_PASSWORD", "changeme_ro")

        try:
            conn = psycopg.connect(
                f"postgresql://ke_ro:{password}@{host}:{port}/{db}"
            )
            yield conn
            conn.close()
        except Exception:
            pytest.skip("ke_ro role not available (run: make db-create-roles)")

    @pytest.fixture
    def ke_app_connection(self):
        """Connection as ke_app (read-write) role."""
        import os

        import psycopg

        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "knowledge_engine")
        password = os.getenv("KE_APP_PASSWORD", "changeme_app")

        try:
            conn = psycopg.connect(
                f"postgresql://ke_app:{password}@{host}:{port}/{db}"
            )
            yield conn
            conn.close()
        except Exception:
            pytest.skip("ke_app role not available (run: make db-create-roles)")

    def test_ke_ro_can_read_documents(self, ke_ro_connection) -> None:
        """ke_ro can SELECT from documents table."""
        with ke_ro_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM evidence.document")
            count = cur.fetchone()[0]
            assert count >= 0

    def test_ke_ro_can_read_chunks(self, ke_ro_connection) -> None:
        """ke_ro can SELECT from chunks table."""
        with ke_ro_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM evidence.chunk")
            count = cur.fetchone()[0]
            assert count >= 0

    def test_ke_ro_can_read_schema_migrations(self, ke_ro_connection) -> None:
        """ke_ro can SELECT from schema_migrations for retrieval queries."""
        with ke_ro_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.schema_migrations")
            count = cur.fetchone()[0]
            assert count >= 0

    def test_ke_ro_cannot_insert(self, ke_ro_connection) -> None:
        """ke_ro cannot INSERT into documents table."""
        import uuid

        with pytest.raises(Exception) as exc_info:
            with ke_ro_connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO evidence.document 
                    (doc_id, title, file_uri, sha256)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (f"TST-{uuid.uuid4().hex[:4].upper()}", "Test", "/test", "a" * 64),
                )
                ke_ro_connection.commit()

        # Should fail with permission denied
        assert "permission denied" in str(exc_info.value).lower()

    def test_ke_ro_cannot_delete(self, ke_ro_connection) -> None:
        """ke_ro cannot DELETE from documents table."""
        with pytest.raises(Exception) as exc_info:
            with ke_ro_connection.cursor() as cur:
                cur.execute("DELETE FROM evidence.document WHERE 1=0")
                ke_ro_connection.commit()

        assert "permission denied" in str(exc_info.value).lower()

    def test_ke_app_can_read(self, ke_app_connection) -> None:
        """ke_app can SELECT from documents table."""
        with ke_app_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM evidence.document")
            count = cur.fetchone()[0]
            assert count >= 0

    def test_ke_app_can_write(self, ke_app_connection) -> None:
        """ke_app can INSERT into documents table."""
        import uuid

        doc_id = f"TST-{uuid.uuid4().hex[:4].upper()}"

        with ke_app_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO evidence.document 
                (doc_id, title, file_uri, sha256)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (doc_id, "Test Doc", "/test/path.pdf", "a" * 64),
            )
            result = cur.fetchone()
            assert result is not None

            # Clean up
            cur.execute("DELETE FROM evidence.document WHERE doc_id = %s", (doc_id,))
            ke_app_connection.commit()
