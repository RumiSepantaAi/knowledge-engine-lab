"""Integration tests for database schema.

These tests verify that the database schema is correctly set up.
They are skipped if the database is not reachable.

Run with: pytest tests/test_db/ -v
"""

import os

import pytest

# Skip all tests if psycopg is not available or DB is not configured
try:
    import psycopg

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


def get_db_connection_string() -> str:
    """Build connection string from environment variables."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "ke_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme")
    database = os.getenv("POSTGRES_DB", "knowledge_engine")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@pytest.fixture(scope="module")
def db_connection():
    """Create a database connection for tests."""
    if not DB_AVAILABLE:
        pytest.skip("psycopg not installed")

    conn_string = get_db_connection_string()
    try:
        conn = psycopg.connect(conn_string)
        yield conn
        conn.close()
    except psycopg.OperationalError as e:
        pytest.skip(f"Database not reachable: {e}")


class TestDatabaseConnection:
    """Basic database connectivity tests."""

    def test_connection_works(self, db_connection) -> None:
        """Verify database connection is working."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result == (1,)

    def test_extensions_enabled(self, db_connection) -> None:
        """Verify required extensions are enabled."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pgcrypto')")
            extensions = {row[0] for row in cur.fetchall()}
            assert "vector" in extensions, "pgvector extension not enabled"
            assert "pgcrypto" in extensions, "pgcrypto extension not enabled"


class TestMetaSchema:
    """Tests for meta schema tables."""

    def test_taxonomy_node_exists(self, db_connection) -> None:
        """Verify meta.taxonomy_node table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('meta.taxonomy_node')")
            result = cur.fetchone()
            assert result[0] is not None, "meta.taxonomy_node table not found"

    def test_glossary_term_exists(self, db_connection) -> None:
        """Verify meta.glossary_term table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('meta.glossary_term')")
            result = cur.fetchone()
            assert result[0] is not None, "meta.glossary_term table not found"

    def test_control_exists(self, db_connection) -> None:
        """Verify meta.control table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('meta.control')")
            result = cur.fetchone()
            assert result[0] is not None, "meta.control table not found"


class TestEvidenceSchema:
    """Tests for evidence schema tables."""

    def test_document_exists(self, db_connection) -> None:
        """Verify evidence.document table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.document')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.document table not found"

    def test_document_revision_exists(self, db_connection) -> None:
        """Verify evidence.document_revision table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.document_revision')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.document_revision table not found"

    def test_chunk_exists(self, db_connection) -> None:
        """Verify evidence.chunk table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.chunk')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.chunk table not found"

    def test_claim_exists(self, db_connection) -> None:
        """Verify evidence.claim table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.claim')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.claim table not found"

    def test_evidence_span_exists(self, db_connection) -> None:
        """Verify evidence.evidence_span table exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.evidence_span')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.evidence_span table not found"


class TestQualityGates:
    """Tests for quality gate views and functions."""

    def test_claims_without_evidence_view_exists(self, db_connection) -> None:
        """Verify v_claims_without_evidence view exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.v_claims_without_evidence')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.v_claims_without_evidence view not found"

    def test_document_validation_summary_view_exists(self, db_connection) -> None:
        """Verify v_document_validation_summary view exists."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT to_regclass('evidence.v_document_validation_summary')")
            result = cur.fetchone()
            assert result[0] is not None, "evidence.v_document_validation_summary view not found"

    def test_check_document_validation_function_exists(self, db_connection) -> None:
        """Verify check_document_validation function exists."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT proname FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'evidence' AND p.proname = 'check_document_validation'
            """)
            result = cur.fetchone()
            assert result is not None, "evidence.check_document_validation function not found"

    def test_validate_document_function_exists(self, db_connection) -> None:
        """Verify validate_document function exists."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT proname FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'evidence' AND p.proname = 'validate_document'
            """)
            result = cur.fetchone()
            assert result is not None, "evidence.validate_document function not found"


class TestEnums:
    """Tests for enum types."""

    def test_doc_status_enum_exists(self, db_connection) -> None:
        """Verify evidence.doc_status enum exists with expected values."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT enumlabel FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE n.nspname = 'evidence' AND t.typname = 'doc_status'
                ORDER BY e.enumsortorder
            """)
            values = [row[0] for row in cur.fetchall()]
            expected = ["inbox", "annotated", "claims_done", "validated", "deprecated"]
            assert values == expected, f"doc_status values: {values}"

    def test_claim_type_enum_exists(self, db_connection) -> None:
        """Verify evidence.claim_type enum exists."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT enumlabel FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE n.nspname = 'evidence' AND t.typname = 'claim_type'
            """)
            values = [row[0] for row in cur.fetchall()]
            assert len(values) == 7, f"Expected 7 claim_type values, got {len(values)}"

    def test_evidence_role_enum_exists(self, db_connection) -> None:
        """Verify evidence.evidence_role enum exists."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT enumlabel FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE n.nspname = 'evidence' AND t.typname = 'evidence_role'
            """)
            values = [row[0] for row in cur.fetchall()]
            expected = ["supports", "contradicts", "mentions"]
            assert values == expected, f"evidence_role values: {values}"


class TestQualityGateDistinctCounts:
    """Tests for the DISTINCT count fix in check_document_validation.

    This test verifies that claims with multiple evidence_spans are counted
    correctly (as 1 claim, not N rows from the JOIN).
    """

    def test_check_document_validation_counts_distinct_claims(self, db_connection) -> None:
        """Verify check_document_validation uses DISTINCT counts.

        Setup:
        - 1 document with 1 revision, 1 chunk
        - claim_A with 2 evidence_spans (should count as 1 claim WITH evidence)
        - claim_B with 0 evidence_spans (should count as 1 claim WITHOUT evidence)

        Expected: "1 claims without evidence (of 2 total)"
        BUG would show: "of 3 total" (counting JOIN rows, not distinct claims)
        """
        # Use a savepoint so we can rollback after test
        with db_connection.cursor() as cur:
            cur.execute("SAVEPOINT test_distinct_counts")

            try:
                # Insert test document
                cur.execute("""
                    INSERT INTO evidence.document (id, doc_id, title, file_uri, sha256)
                    VALUES (
                        'aaaaaaaa-0000-0000-0000-000000000001'::uuid,
                        'TST-0001',
                        'Test Document',
                        '/test/file.pdf',
                        'abc123'
                    )
                """)

                # Insert revision
                cur.execute("""
                    INSERT INTO evidence.document_revision (id, document_id, revision_no, sha256, file_uri)
                    VALUES (
                        'bbbbbbbb-0000-0000-0000-000000000001'::uuid,
                        'aaaaaaaa-0000-0000-0000-000000000001'::uuid,
                        1,
                        'rev123',
                        '/test/file_v1.pdf'
                    )
                """)

                # Insert chunk
                cur.execute("""
                    INSERT INTO evidence.chunk (id, revision_id, chunk_no, text)
                    VALUES (
                        'cccccccc-0000-0000-0000-000000000001'::uuid,
                        'bbbbbbbb-0000-0000-0000-000000000001'::uuid,
                        1,
                        'Test chunk text'
                    )
                """)

                # Insert claim_A (will have 2 evidence spans)
                cur.execute("""
                    INSERT INTO evidence.claim (id, revision_id, claim_text)
                    VALUES (
                        'dddddddd-0000-0000-0000-000000000001'::uuid,
                        'bbbbbbbb-0000-0000-0000-000000000001'::uuid,
                        'Claim A - has evidence'
                    )
                """)

                # Insert claim_B (will have 0 evidence spans)
                cur.execute("""
                    INSERT INTO evidence.claim (id, revision_id, claim_text)
                    VALUES (
                        'dddddddd-0000-0000-0000-000000000002'::uuid,
                        'bbbbbbbb-0000-0000-0000-000000000001'::uuid,
                        'Claim B - no evidence'
                    )
                """)

                # Insert 2 evidence spans for claim_A
                cur.execute("""
                    INSERT INTO evidence.evidence_span (id, claim_id, chunk_id, snippet)
                    VALUES
                        ('eeeeeeee-0000-0000-0000-000000000001'::uuid,
                         'dddddddd-0000-0000-0000-000000000001'::uuid,
                         'cccccccc-0000-0000-0000-000000000001'::uuid,
                         'Evidence 1'),
                        ('eeeeeeee-0000-0000-0000-000000000002'::uuid,
                         'dddddddd-0000-0000-0000-000000000001'::uuid,
                         'cccccccc-0000-0000-0000-000000000001'::uuid,
                         'Evidence 2')
                """)

                # Call the validation function
                cur.execute("""
                    SELECT evidence.check_document_validation(
                        'aaaaaaaa-0000-0000-0000-000000000001'::uuid
                    )
                """)
                result = cur.fetchone()[0]

                # Verify the message
                assert result is not None, "Should return error message (claim_B has no evidence)"
                assert "1 claims without evidence" in result, f"Wrong count: {result}"
                assert "(of 2 total)" in result, f"BUG: Got wrong total count: {result}"

            finally:
                # Rollback to savepoint (clean up test data)
                cur.execute("ROLLBACK TO SAVEPOINT test_distinct_counts")

