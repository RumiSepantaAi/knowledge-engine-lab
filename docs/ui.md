# Knowledge Engine UI

## Overview

The Knowledge Engine includes a Streamlit-based web interface for the evidence workflow.

**Stack Choice: Streamlit**
- Local-first, no build step
- Same Python codebase as CLI
- Uses shared `ke_db` layer
- Rapid MVP iteration

## Installation

```bash
# Install UI dependencies
uv sync --extra dev --extra ui
```

## Running

```bash
make ui
# Opens http://localhost:8501
```

## Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | List documents with status |
| **Add Document** | Create new document (confirmation screen) |
| **Document Detail** | View chunks, claims, evidence, quality gate |
| **Add Chunks** | Batch add chunks to revision |
| **Add Claims** | Batch add claims to revision |
| **Add Evidence** | Link claim to chunk |
| **Importer** | CSV taxonomy import |
| **Status** | System health |
| **DB Migrations** | Applied migrations |

## Workflow

1. **Dashboard** → View documents
2. **Add Document** → Form → Confirmation → Save
3. **Document Detail** → Tabs: Chunks | Claims | Quality Gate
4. Add **Chunks** (batch) → Confirmation → Save
5. Add **Claims** (batch) → Confirmation → Save
6. Add **Evidence** per claim → Confirmation → Save
7. **Quality Gate** → PASS/FAIL → Validate

## Architecture

```
apps/ke_ui/
├── app.py              # Main entry, navigation
└── pages/
    ├── 1_Status.py
    ├── 2_Importer.py
    ├── 3_Taxonomy_Browser.py
    ├── 4_DQ_Report.py
    ├── 5_DB_Migrations.py
    ├── 6_Dashboard.py       # Document list
    ├── 7_Add_Document.py    # Doc form + confirm
    ├── 8_Document_Detail.py # Chunks/Claims/Quality
    ├── 9_Add_Chunks.py      # Batch chunks
    ├── 10_Add_Claims.py     # Batch claims
    └── 11_Add_Evidence.py   # Link claim-chunk
```

All UI pages use `apps/ke_db/` for database access (same as CLI).

## Auth (Future)

Current: No authentication (local-first).

Structure is in place for adding auth:
- Session state for user context
- Forms validate before writes
- All writes go through `ke_db` layer
