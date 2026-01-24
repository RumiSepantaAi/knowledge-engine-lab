import pytest
import psycopg

class TestDBIntegration:
    """Integration tests for Database schema and migration tracking."""

    def test_extensions_installed(self, db_connection):
        """Verify required extensions are installed."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            assert cur.fetchone() is not None, "pgvector extension missing"

    def test_schemas_exist(self, db_connection):
        """Verify required schemas exist."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT nspname FROM pg_namespace WHERE nspname IN ('meta', 'evidence')")
            rows = [row[0] for row in cur.fetchall()]
            assert "meta" in rows
            assert "evidence" in rows

    def test_schema_migrations_table_structure(self, db_connection):
        """Verify schema_migrations table has correct columns."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'schema_migrations'
            """)
            columns = {row[0]: row[1] for row in cur.fetchall()}
            
            assert "filename" in columns
            assert "content_sha256" in columns
            assert "applied_at" in columns

    def test_quality_gates_views_exist(self, db_connection):
        """Verify quality gate views are created."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'evidence'
            """)
            views = [row[0] for row in cur.fetchall()]
            assert "v_claims_without_evidence" in views
            assert "v_document_validation_summary" in views

    def test_advisory_lock_availability(self, db_connection):
        """Verify we can acquire a lock (basic check)."""
        LOCK_ID = 123456789
        with db_connection.cursor() as cur:
            # Try to acquire the lock used by migrate.sh
            cur.execute(f"SELECT pg_try_advisory_lock({LOCK_ID})")
            acquired = cur.fetchone()[0]
            # It might be held if a migration is running, but in test env it should be free
            # If it returns False, it means something holds it, which is also a valid state to checking existing of lock mechanism
            # But we expect True strictly here as tests run sequentially
            assert acquired is True
            
            # Release it
            cur.execute(f"SELECT pg_advisory_unlock({LOCK_ID})")
