# Embeddings Subsystem

## Overview

The embeddings subsystem generates vector embeddings for document chunks, enabling semantic search.

## Providers

| Provider | Description | API Key Required |
|----------|-------------|------------------|
| `DummyProvider` | Deterministic embeddings for testing | No |
| `RemoteProvider` | OpenAI API embeddings | Yes (`OPENAI_API_KEY`) |

## Configuration

Set in `.env` (copy from `.env.example`):

```bash
# Required for RemoteProvider
OPENAI_API_KEY=sk-...
```

**Security:** Never commit `.env` to git. The key is loaded from environment only.

## CLI Usage

### Generate Embeddings

```bash
# Auto-select provider (OpenAI if key set, else Dummy)
ke embed revision -r <revision-uuid>

# Use specific provider
ke embed revision -r <revision-uuid> --provider dummy
ke embed revision -r <revision-uuid> --provider openai

# Dry run
ke embed revision -r <revision-uuid> --dry-run

# Custom batch size
ke embed revision -r <revision-uuid> --batch-size 100
```

### Check Status

```bash
ke embed status <revision-uuid>
```

## Programmatic Usage

```python
from apps.ke_db.embeddings import get_provider, DummyProvider

# Get provider
provider = get_provider("auto")  # or "dummy", "openai"

# Generate embeddings
texts = ["First chunk text", "Second chunk text"]
embeddings = provider.embed_texts(texts)

# Each embedding is a list of floats
print(f"Dimension: {len(embeddings[0])}")  # 1536
```

## Features

### Idempotent Operation
- Only fills `NULL` embeddings
- Safe to run multiple times

### Batch Processing
- Default batch size: 50
- Configurable via `--batch-size`

### Retry with Backoff
- Max retries: 3
- Exponential backoff between retries

### Structured Logging
- Timestamps and log levels
- Batch progress tracking

## Testing

Tests use `DummyProvider` with deterministic embeddings (no API calls):

```bash
make test
```

```python
# In tests
from apps.ke_db.embeddings import DummyProvider

provider = DummyProvider()
emb = provider.embed_texts(["test"])[0]
# Always same result for same input
```

## Embedding Dimension

Default: `1536` (OpenAI ada-002)

To change, edit `EMBEDDING_DIMENSION` in:
- `apps/ke_db/embeddings.py`
- `apps/ke_db/retrieval.py`
- Database column: `evidence.chunk.embedding vector(N)`
