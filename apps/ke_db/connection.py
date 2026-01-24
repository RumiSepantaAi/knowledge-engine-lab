"""Database connection management.

Connection string from environment variables.
Never commits secrets to git.
"""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg


def get_connection_string() -> str:
    """Build connection string from environment variables.

    Environment variables:
        POSTGRES_HOST: Database host (default: localhost)
        POSTGRES_PORT: Database port (default: 5432)
        POSTGRES_USER: Database user (default: ke_user)
        POSTGRES_PASSWORD: Database password (default: changeme)
        POSTGRES_DB: Database name (default: knowledge_engine)

    Returns:
        PostgreSQL connection string.
    """
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "ke_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme")
    database = os.getenv("POSTGRES_DB", "knowledge_engine")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection.

    Yields:
        Active database connection.
    """
    conn = psycopg.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()
