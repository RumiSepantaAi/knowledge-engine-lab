# Retrieval Module

## Overview

The retrieval module provides search capabilities over document chunks:
- **Full-text search**: PostgreSQL tsvector-based text matching
- **Vector similarity**: pgvector cosine/L2/inner product distance
- **Hybrid search**: Combines both using Reciprocal Rank Fusion (RRF)

## Configuration

```python
from apps.ke_db.retrieval import EMBEDDING_DIMENSION

# Default: 1536 (OpenAI ada-002)
# Change in retrieval.py if using different embedding model
```

## Usage

### Full-Text Search

```python
from apps.ke_db.connection import get_connection
from apps.ke_db.retrieval import full_text_search, SearchFilters

with get_connection() as conn:
    results = full_text_search(
        conn,
        query="machine learning",
        filters=SearchFilters(
            revision_id=revision_uuid,
            tags=["ai", "ml"],
            page_start=1,
            page_end=50,
            limit=10,
        ),
    )

    for r in results:
        print(f"[{r.score:.3f}] Chunk #{r.chunk_no}: {r.text[:80]}...")
```

### Vector Similarity Search

```python
from apps.ke_db.retrieval import vector_search

# Your embedding from OpenAI/etc
embedding = get_embedding("machine learning algorithms")

with get_connection() as conn:
    results = vector_search(
        conn,
        embedding=embedding,
        filters=SearchFilters(limit=10),
        distance_metric="cosine",  # or "l2", "inner_product"
    )
```

### Hybrid Search

```python
from apps.ke_db.retrieval import hybrid_search

with get_connection() as conn:
    results = hybrid_search(
        conn,
        query="machine learning",
        embedding=embedding,  # Optional
        filters=SearchFilters(limit=10),
        text_weight=0.4,
        vector_weight=0.6,
    )
```

## Filters

| Filter | Type | Description |
|--------|------|-------------|
| `revision_id` | UUID | Limit to specific document revision |
| `tags` | list[str] | Match chunks with any of these tags |
| `page_start` | int | Minimum page number |
| `page_end` | int | Maximum page number |
| `limit` | int | Max results (default: 10) |

## ANN Index

For large datasets (>1000 chunks), enable the HNSW index:

1. Edit `db/migrations/012_vector_ann_index.sql`
2. Uncomment the `CREATE INDEX CONCURRENTLY` statement
3. Run `make db-migrate`

### When to Enable

| Chunks | Recommendation |
|--------|----------------|
| <1000 | Not needed (exact search is fast) |
| 1000-10000 | Enable for <100ms queries |
| >10000 | Required for reasonable performance |

### Trade-offs

| Parameter | Higher Value | Lower Value |
|-----------|--------------|-------------|
| `m` | Better recall, more memory | Faster build, less accurate |
| `ef_construction` | Better index quality, slower build | Faster build, lower quality |
| `ef_search` | Better recall, slower query | Faster query, lower recall |

## Testing

```bash
make test  # Includes retrieval tests
```

Tests use deterministic embeddings (no external API required):

```python
from tests.test_ke_db.test_retrieval import generate_deterministic_embedding

emb = generate_deterministic_embedding(seed=42)
```
