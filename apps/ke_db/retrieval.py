"""Retrieval module for full-text, vector, and hybrid search.

Supports:
- Full-text search using PostgreSQL tsvector
- Vector similarity search using pgvector
- Hybrid search combining both approaches
- Filtering by tags, status, revision_id, page ranges
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import psycopg

# Configurable embedding dimension (default: OpenAI ada-002)
EMBEDDING_DIMENSION = 1536


@dataclass
class SearchResult:
    """A single search result."""

    chunk_id: UUID
    revision_id: UUID
    chunk_no: int
    text: str
    page_start: int | None
    page_end: int | None
    section_path: str | None
    score: float
    match_type: str  # "text", "vector", "hybrid"


@dataclass
class SearchFilters:
    """Filters for search queries."""

    revision_id: UUID | None = None
    tags: list[str] | None = None
    page_start: int | None = None
    page_end: int | None = None
    limit: int = 10


def full_text_search(
    conn: psycopg.Connection,
    query: str,
    filters: SearchFilters | None = None,
) -> list[SearchResult]:
    """Full-text search over chunks using PostgreSQL tsvector.

    Args:
        conn: Database connection.
        query: Search query string.
        filters: Optional filters.

    Returns:
        List of matching chunks ranked by relevance.
    """
    filters = filters or SearchFilters()

    # Build WHERE clauses
    where_clauses = ["to_tsvector('simple', c.text) @@ plainto_tsquery('simple', %(query)s)"]
    params: dict[str, Any] = {"query": query, "limit": filters.limit}

    if filters.revision_id:
        where_clauses.append("c.revision_id = %(revision_id)s")
        params["revision_id"] = filters.revision_id

    if filters.tags:
        where_clauses.append("c.tags && %(tags)s")
        params["tags"] = filters.tags

    if filters.page_start is not None:
        where_clauses.append("c.page_start >= %(page_start)s")
        params["page_start"] = filters.page_start

    if filters.page_end is not None:
        where_clauses.append("c.page_end <= %(page_end)s")
        params["page_end"] = filters.page_end

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            c.id,
            c.revision_id,
            c.chunk_no,
            c.text,
            c.page_start,
            c.page_end,
            c.section_path,
            ts_rank(to_tsvector('simple', c.text), plainto_tsquery('simple', %(query)s)) AS score
        FROM evidence.chunk c
        WHERE {where_sql}
        ORDER BY score DESC
        LIMIT %(limit)s
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [
            SearchResult(
                chunk_id=row[0],
                revision_id=row[1],
                chunk_no=row[2],
                text=row[3],
                page_start=row[4],
                page_end=row[5],
                section_path=row[6],
                score=float(row[7]),
                match_type="text",
            )
            for row in cur.fetchall()
        ]


def vector_search(
    conn: psycopg.Connection,
    embedding: list[float],
    filters: SearchFilters | None = None,
    distance_metric: str = "cosine",
) -> list[SearchResult]:
    """Vector similarity search using pgvector.

    Args:
        conn: Database connection.
        embedding: Query embedding vector.
        filters: Optional filters.
        distance_metric: Distance metric ("cosine", "l2", "inner_product").

    Returns:
        List of matching chunks ranked by similarity.
    """
    filters = filters or SearchFilters()

    # Validate embedding dimension
    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(f"Embedding must have {EMBEDDING_DIMENSION} dimensions, got {len(embedding)}")

    # Select distance operator
    if distance_metric == "cosine":
        distance_op = "<=>"
        order_direction = "ASC"  # Lower cosine distance = more similar
    elif distance_metric == "l2":
        distance_op = "<->"
        order_direction = "ASC"
    elif distance_metric == "inner_product":
        distance_op = "<#>"
        order_direction = "DESC"  # Higher inner product = more similar
    else:
        raise ValueError(f"Unknown distance metric: {distance_metric}")

    # Build WHERE clauses
    where_clauses = ["c.embedding IS NOT NULL"]
    params: dict[str, Any] = {"embedding": embedding, "limit": filters.limit}

    if filters.revision_id:
        where_clauses.append("c.revision_id = %(revision_id)s")
        params["revision_id"] = filters.revision_id

    if filters.tags:
        where_clauses.append("c.tags && %(tags)s")
        params["tags"] = filters.tags

    if filters.page_start is not None:
        where_clauses.append("c.page_start >= %(page_start)s")
        params["page_start"] = filters.page_start

    if filters.page_end is not None:
        where_clauses.append("c.page_end <= %(page_end)s")
        params["page_end"] = filters.page_end

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT
            c.id,
            c.revision_id,
            c.chunk_no,
            c.text,
            c.page_start,
            c.page_end,
            c.section_path,
            c.embedding {distance_op} %(embedding)s::vector AS distance
        FROM evidence.chunk c
        WHERE {where_sql}
        ORDER BY distance {order_direction}
        LIMIT %(limit)s
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [
            SearchResult(
                chunk_id=row[0],
                revision_id=row[1],
                chunk_no=row[2],
                text=row[3],
                page_start=row[4],
                page_end=row[5],
                section_path=row[6],
                score=1.0 - float(row[7]) if distance_metric == "cosine" else float(row[7]),
                match_type="vector",
            )
            for row in cur.fetchall()
        ]


def hybrid_search(
    conn: psycopg.Connection,
    query: str,
    embedding: list[float] | None = None,
    filters: SearchFilters | None = None,
    text_weight: float = 0.5,
    vector_weight: float = 0.5,
) -> list[SearchResult]:
    """Hybrid search combining full-text and vector similarity.

    Uses Reciprocal Rank Fusion (RRF) to combine results.

    Args:
        conn: Database connection.
        query: Text search query.
        embedding: Optional query embedding for vector search.
        filters: Optional filters.
        text_weight: Weight for text search results (0.0 to 1.0).
        vector_weight: Weight for vector search results (0.0 to 1.0).

    Returns:
        List of matching chunks with combined scores.
    """
    filters = filters or SearchFilters()

    # Get text results
    text_results = full_text_search(conn, query, filters)

    # Get vector results if embedding provided
    vector_results: list[SearchResult] = []
    if embedding:
        vector_results = vector_search(conn, embedding, filters)

    # Combine using Reciprocal Rank Fusion
    rrf_k = 60  # Standard RRF constant
    scores: dict[UUID, float] = {}
    results_map: dict[UUID, SearchResult] = {}

    # Add text results
    for rank, result in enumerate(text_results, 1):
        rrf_score = text_weight / (rrf_k + rank)
        scores[result.chunk_id] = scores.get(result.chunk_id, 0) + rrf_score
        results_map[result.chunk_id] = result

    # Add vector results
    for rank, result in enumerate(vector_results, 1):
        rrf_score = vector_weight / (rrf_k + rank)
        scores[result.chunk_id] = scores.get(result.chunk_id, 0) + rrf_score
        if result.chunk_id not in results_map:
            results_map[result.chunk_id] = result

    # Sort by combined score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    return [
        SearchResult(
            chunk_id=results_map[cid].chunk_id,
            revision_id=results_map[cid].revision_id,
            chunk_no=results_map[cid].chunk_no,
            text=results_map[cid].text,
            page_start=results_map[cid].page_start,
            page_end=results_map[cid].page_end,
            section_path=results_map[cid].section_path,
            score=scores[cid],
            match_type="hybrid",
        )
        for cid in sorted_ids[: filters.limit]
    ]


def update_chunk_embedding(
    conn: psycopg.Connection,
    chunk_id: UUID,
    embedding: list[float],
) -> bool:
    """Update embedding for a chunk.

    Args:
        conn: Database connection.
        chunk_id: Chunk UUID.
        embedding: Embedding vector.

    Returns:
        True if updated, False otherwise.
    """
    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(f"Embedding must have {EMBEDDING_DIMENSION} dimensions")

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE evidence.chunk
            SET embedding = %(embedding)s::vector
            WHERE id = %(chunk_id)s
            """,
            {"chunk_id": chunk_id, "embedding": embedding},
        )
        return cur.rowcount > 0
