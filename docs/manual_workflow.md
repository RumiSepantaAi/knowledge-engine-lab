# Manual Workflow Guide

The `ke` CLI provides a 15–20 minute interactive workflow for adding documents, extracting claims, and linking evidence.

## Quick Reference

```bash
# Document management
ke doc add          # Add new document interactively
ke doc list         # List documents
ke doc show DOC-0001

# Chunk management
ke chunk add -r <revision-uuid> -n 4  # Add 4 chunks
ke chunk list <revision-uuid>

# Claim management
ke claim add -r <revision-uuid> -n 10  # Add 10 claims
ke claim list <revision-uuid>

# Evidence linking
ke evidence add -c <claim-uuid> -k <chunk-uuid>
ke evidence list <claim-uuid>

# Quality gate
ke quality gate <revision-uuid>
ke quality gate <revision-uuid> --validate  # Set validated if passing
```

## Example Session

```
$ ke doc add

📄 Add New Document

Document ID (e.g. DOC-0001): RFC-8446
Title: The Transport Layer Security (TLS) Protocol Version 1.3
Authors: E. Rescorla
Publisher Organization: IETF
Published Date (YYYY-MM-DD): 2018-08-01
Source URL: https://datatracker.ietf.org/doc/html/rfc8446
File path (PDF): ./docs/rfc8446.pdf
Tags (comma-separated): security, tls, cryptography

Computing SHA256...
  SHA256: a1b2c3d4e5f6...

Summary:
  Doc ID     RFC-8446
  Title      The Transport Layer Security (TLS) Protocol Version 1.3
  Authors    E. Rescorla
  Publisher  IETF
  Published  2018-08-01
  File       ./docs/rfc8446.pdf
  SHA256     a1b2c3d4e5f6789...
  Tags       security, tls, cryptography

Commit to database? [y/N]: y

✅ Document created successfully!
  Document UUID: 123e4567-e89b-12d3-a456-426614174000
  Revision UUID: 789a0123-e89b-12d3-a456-426614174001
```

Then add chunks:

```
$ ke chunk add -r 789a0123-e89b-12d3-a456-426614174001 -n 4

📦 Add Chunks

Chunk #1
Text content: TLS 1.3 eliminates older cryptographic algorithms...
Page number: 1
Section path: Introduction

Continue to next chunk? [Y/n]: y
...

Summary: 4 chunk(s)
...
Commit to database? [y/N]: y
✅ 4 chunk(s) created!
```

Add claims:

```
$ ke claim add -r 789a0123-... -n 3

📝 Add Claims

Claim #1
Claim text: TLS 1.3 removes support for RSA key exchange
Type: fact
Confidence: 0.95
...
```

Link evidence:

```
$ ke evidence add -c <claim-uuid> -k <chunk-uuid>

🔗 Add Evidence Span

Role: supports
Page number: 5
Evidence snippet: "TLS 1.3 eliminates RSA key transport..."
Support strength: 0.90
...
```

Run quality gate:

```
$ ke quality gate 789a0123-...

🔍 Quality Gate Check

  Total claims: 3
  With evidence: 3
  Without evidence: 0

✅ PASS - All claims have evidence!
```
