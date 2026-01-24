# Architecture Overview

This document describes the high-level architecture of the AI Knowledge Engine Control Plane.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Knowledge Engine Control Plane                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────┐         ┌─────────────────────────┐          │
│   │      META-GRAPH         │         │     EVIDENCE-GRAPH      │          │
│   │  "What should exist"    │◄───────►│   "Proof it exists"     │          │
│   └─────────────────────────┘         └─────────────────────────┘          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Meta-Graph: The Canonical Model

The Meta-Graph defines **what knowledge should exist** in the system. It is the authoritative source for:

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **Taxonomy** | Hierarchical classification of concepts | `Security > Access Control > Authentication` |
| **Glossary** | Canonical definitions for terms | `MFA: Multi-factor authentication requiring 2+ factors` |
| **Controls** | Governance and compliance requirements | `CTRL-001: All APIs must use TLS 1.3+` |

### Characteristics

- **Prescriptive**: Defines the expected state
- **Curated**: Human-reviewed and approved
- **Versioned**: Changes are tracked and auditable
- **Hierarchical**: Concepts form a directed acyclic graph (DAG)

---

## Evidence-Graph: The Provenance Layer

The Evidence-Graph captures **proof that knowledge claims are valid**. It connects real-world artifacts to Meta-Graph concepts.

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **Documents** | Source materials (PDFs, policies, code) | `security-policy-v2.3.pdf` |
| **Citations** | Specific references within documents | `Page 12, Section 3.2, Paragraph 1` |
| **Claims** | Assertions linking evidence to concepts | `"This document proves MFA is implemented"` |

### Characteristics

- **Descriptive**: Reflects actual observed state
- **Traceable**: Every claim links to source evidence
- **Timestamped**: Captures when evidence was collected
- **Scored**: Confidence levels for each claim

---

## How They Connect

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  META-GRAPH                           EVIDENCE-GRAPH                     │
│  ──────────                           ──────────────                     │
│                                                                          │
│  ┌─────────────┐                      ┌─────────────┐                   │
│  │  Taxonomy   │                      │  Document   │                   │
│  │  Node       │                      │  (Source)   │                   │
│  └──────┬──────┘                      └──────┬──────┘                   │
│         │                                    │                           │
│         │ defines                            │ contains                  │
│         ▼                                    ▼                           │
│  ┌─────────────┐         proves       ┌─────────────┐                   │
│  │  Glossary   │◄────────────────────│  Citation   │                   │
│  │  Term       │                      │  (Reference)│                   │
│  └──────┬──────┘                      └──────┬──────┘                   │
│         │                                    │                           │
│         │ governed by                        │ supports                  │
│         ▼                                    ▼                           │
│  ┌─────────────┐         validates    ┌─────────────┐                   │
│  │  Control    │◄────────────────────│   Claim     │                   │
│  │             │                      │ (Assertion) │                   │
│  └─────────────┘                      └─────────────┘                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Relationship Types

| Relationship | From | To | Meaning |
|--------------|------|-----|---------|
| `PROVES` | Citation | Glossary Term | Evidence supports a definition |
| `VALIDATES` | Claim | Control | Assertion confirms compliance |
| `SUPPORTS` | Citation | Claim | Reference backs up assertion |
| `DEFINES` | Taxonomy Node | Glossary Term | Classification contextualizes term |

---

## Data Flow

```
1. IMPORT          2. EXTRACT           3. LINK              4. QUERY
──────────────     ──────────────       ──────────────       ──────────────
│ CSV/Docs   │ ──► │ Parse &    │ ──►  │ Match to   │ ──►  │ CLI/API    │
│ (Sources)  │     │ Identify   │      │ Meta-Graph │      │ (Query)    │
──────────────     ──────────────       ──────────────       ──────────────
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │ PostgreSQL  │
                                       │ + pgvector  │
                                       └─────────────┘
```

---

## Database Schema (Conceptual)

### Meta Schema (`meta.*`)

```sql
-- Taxonomy: hierarchical classification
meta.taxonomy_nodes (id, parent_id, name, description, level)

-- Glossary: term definitions
meta.glossary_terms (id, term, definition, taxonomy_node_id)

-- Controls: governance requirements
meta.controls (id, code, title, description, category)
```

### Evidence Schema (`evidence.*`)

```sql
-- Documents: source materials
evidence.documents (id, uri, title, doc_type, ingested_at)

-- Citations: specific references
evidence.citations (id, document_id, location, text, embedding)

-- Claims: assertions with confidence
evidence.claims (id, citation_id, target_type, target_id, confidence)
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Database | PostgreSQL 16 + pgvector | Relational + vector storage |
| Backend | Python 3.11+ | Core logic |
| CLI | Typer + Rich | Interactive interface |
| Validation | Pydantic | Data contracts |
| Tooling | uv, ruff, mypy | Development workflow |

---

## Next Steps

1. **Schema Implementation**: Create migration files in `db/migrations/`
2. **CSV Importer**: Build parser in `meta/importer/`
3. **CLI Commands**: Add CRUD operations to `apps/ke_cli/`
4. **Vector Search**: Implement semantic search with pgvector
