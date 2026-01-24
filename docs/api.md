# Knowledge Engine API

## Overview

REST API for the Knowledge Engine, built with FastAPI.

**Base URL:** `http://localhost:8000`  
**OpenAPI Docs:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`

## Installation

```bash
uv sync --extra dev --extra api
```

## Running

```bash
make api
# → http://localhost:8000
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Health check |
| `POST` | `/docs` | Create document + revision |
| `POST` | `/chunks` | Create chunk |
| `POST` | `/claims` | Create claim |
| `POST` | `/evidence` | Create evidence span |
| `GET` | `/quality/{revision_id}` | Check quality gate |

## Examples

### Create Document

```bash
curl -X POST http://localhost:8000/docs \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "RFC-8446",
    "title": "TLS 1.3",
    "file_uri": "/docs/rfc8446.pdf",
    "sha256": "a1b2c3d4..."
  }'
```

Response:
```json
{
  "id": "uuid...",
  "doc_id": "RFC-8446",
  "title": "TLS 1.3",
  "status": "inbox",
  "revision_id": "uuid..."
}
```

### Create Chunk

```bash
curl -X POST http://localhost:8000/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "revision_id": "uuid...",
    "chunk_no": 1,
    "text": "TLS 1.3 eliminates older algorithms..."
  }'
```

### Create Claim

```bash
curl -X POST http://localhost:8000/claims \
  -H "Content-Type: application/json" \
  -d '{
    "revision_id": "uuid...",
    "claim_text": "TLS 1.3 removes RSA key exchange",
    "claim_type": "fact",
    "confidence": 0.95
  }'
```

### Create Evidence

```bash
curl -X POST http://localhost:8000/evidence \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "uuid...",
    "chunk_id": "uuid...",
    "snippet": "RSA key transport is removed...",
    "role": "supports",
    "support_strength": 0.90
  }'
```

### Check Quality Gate

```bash
curl http://localhost:8000/quality/{revision_id}
```

Response:
```json
{
  "revision_id": "uuid...",
  "passed": true,
  "total_claims": 5,
  "claims_with_evidence": 5,
  "claims_without_evidence": 0
}
```

## Validation

| Field | Validation |
|-------|------------|
| `doc_id` | Format: `XXX-NNNN` (3 uppercase letters, dash, 4+ digits) |
| `sha256` | 64 hex characters |
| `confidence` | 0.0 to 1.0 |
| `support_strength` | 0.0 to 1.0 |
| `claim_type` | One of: fact, definition, requirement, recommendation, metric, other |
| `role` | One of: supports, contradicts, mentions |
| `snippet` | Max 2000 characters |

## Testing

```bash
make api-test
```
