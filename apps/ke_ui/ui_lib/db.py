"""Database connectivity and migration utilities for UI."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MigrationInfo:
    """Information about an applied migration."""

    filename: str
    content_sha256: str | None
    applied_at: str
    has_drift: bool = False
    current_sha256: str | None = None


def get_db_connection_string() -> str:
    """Build connection string from environment variables."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "ke_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme")
    database = os.getenv("POSTGRES_DB", "knowledge_engine")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def check_db_connection() -> tuple[bool, str]:
    """Check if database is reachable.

    Returns:
        Tuple of (is_connected, message)
    """
    try:
        import psycopg

        conn_string = get_db_connection_string()
        with psycopg.connect(conn_string, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True, "Connected"
    except ImportError:
        return False, "psycopg not installed"
    except Exception as e:
        return False, str(e)


def get_applied_migrations() -> list[MigrationInfo]:
    """Get list of applied migrations from database.

    Returns:
        List of MigrationInfo objects, empty if DB not reachable.
    """
    try:
        import psycopg

        conn_string = get_db_connection_string()
        with psycopg.connect(conn_string, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT filename, content_sha256, applied_at::text
                    FROM public.schema_migrations
                    ORDER BY filename
                """)
                rows = cur.fetchall()

        migrations = []
        for filename, sha256, applied_at in rows:
            info = MigrationInfo(
                filename=filename,
                content_sha256=sha256,
                applied_at=applied_at,
            )
            migrations.append(info)

        return migrations
    except Exception:
        return []


def check_migration_drift(migrations: list[MigrationInfo]) -> list[MigrationInfo]:
    """Check for drift between applied and current migration files.

    Args:
        migrations: List of applied migrations

    Returns:
        Updated list with drift detection
    """
    # Try to find migrations directory
    migrations_dir = Path("db/migrations")
    if not migrations_dir.exists():
        # Try relative to script
        script_dir = Path(__file__).parent.parent.parent.parent
        migrations_dir = script_dir / "db" / "migrations"

    if not migrations_dir.exists():
        return migrations

    for migration in migrations:
        filepath = migrations_dir / migration.filename
        if filepath.exists():
            current_sha = compute_sha256(filepath)
            migration.current_sha256 = current_sha
            if migration.content_sha256 and current_sha != migration.content_sha256:
                migration.has_drift = True

    return migrations


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_migration_count() -> int | None:
    """Get count of applied migrations.

    Returns:
        Count or None if DB not reachable.
    """
    try:
        import psycopg

        conn_string = get_db_connection_string()
        with psycopg.connect(conn_string, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.schema_migrations")
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception:
        return None
