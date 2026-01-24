# Meta-Blueprint Importer

Import and normalize taxonomy CSV files with intelligent semicolon splitting,
typo correction, and multi-format output.

## Quick Start

```bash
# Process CSV files in meta/input/
python -m meta.importer.import_taxonomy --in meta/input --out meta/output

# Strict mode (fail on data quality issues)
python -m meta.importer.import_taxonomy --in meta/input --out meta/output --strict
```

## Input Format

### Accepted Column Names

The importer supports multiple column name variations (case-insensitive):

| Level | Accepted Names |
|-------|----------------|
| Level 1 | `Level 1`, `L1`, `Domain`, `Category`, `level_1`, `level1`, `lv1` |
| Level 2 | `Level 2`, `L2`, `Subdomain`, `Subcategory`, `level_2`, `level2`, `lv2` |
| Level 3 | `Level 3`, `L3`, `Topic`, `Area`, `level_3`, `level3`, `lv3` |
| Level 4 | `Level 4`, `L4`, `Term`, `Item`, `Terms`, `level_4`, `level4`, `lv4` |

### Example Input CSV

```csv
Level 1,Level 2,Level 3,Level 4
AI,Machine Learning,Supervised,Linear Regression; Logistic Regression
AI,Machine Learning,Unsupervised,K-Means; 3-Layer Vector DB (Evidence; Implication; Playbook)
```

## Parsing Rules

### Semicolon Splitting

Level-4 terms are split on semicolons, **but only when outside parentheses**:

| Input | Result |
|-------|--------|
| `A; B; C` | `["A", "B", "C"]` |
| `3-Layer Vector DB (Evidence; Implication; Playbook)` | `["3-Layer Vector DB (Evidence; Implication; Playbook)"]` |
| `Foo (a; b); Bar` | `["Foo (a; b)", "Bar"]` |

This ensures complex terms with embedded semicolons are preserved as single items.

### Normalization Pipeline

1. **Trim**: Remove leading/trailing whitespace from all values
2. **Typo Correction**: Apply corrections from the typo map (see below)
3. **Dedupe**: Remove duplicate terms per row while preserving order
4. **ID Generation**: Create deterministic UUIDs using `uuid5`

### ID Generation

Both `taxon_id` and `term_id` are generated using `uuid.uuid5` with a fixed namespace:

```python
# Taxon ID: based on normalized path
taxon_id = uuid5(NAMESPACE, "AI > Machine Learning > Supervised")

# Term ID: based on taxon_id + normalized term
term_id = uuid5(NAMESPACE, f"{taxon_id}|Linear Regression")
```

This ensures the same input always produces the same IDs (deterministic, reproducible).

## Output Files

### `taxonomy_clean.csv`

Cleaned taxonomy with normalized columns and split terms (one per row):

```csv
level_1,level_2,level_3,level_4
AI,Machine Learning,Supervised,Linear Regression
AI,Machine Learning,Supervised,Logistic Regression
```

### `terms_normalized.csv`

Fully normalized terms with IDs and provenance:

| Column | Description |
|--------|-------------|
| `taxon_path` | Full path: `L1 > L2 > L3` |
| `level1` | Level 1 value |
| `level2` | Level 2 value |
| `level3` | Level 3 value |
| `term_raw` | Original term (before normalization) |
| `term_norm` | Normalized term |
| `term_id` | Deterministic UUID for this term |
| `taxon_id` | Deterministic UUID for the taxon path |
| `source_file` | Input filename |
| `row_index` | 1-indexed row number |

### `taxonomy_tree.json`

Hierarchical JSON structure:

```json
{
  "AI": {
    "Machine Learning": {
      "Supervised": ["Linear Regression", "Logistic Regression"]
    }
  }
}
```

### `taxonomy_tree.yaml`

Same structure as JSON, in YAML format (requires PyYAML).

### `dq_report.md`

Data quality report with:

- **Summary**: File count, row count, term count
- **Counts by Level**: Unique values at each level
- **Missing Levels**: Rows with empty L1/L2/L3
- **Duplicate Terms**: Terms appearing multiple times
- **Empty Terms**: Rows with empty L4 after splitting
- **Suspicious Split Candidates**: Terms with `/` or `or` that might need splitting

## Extending the Typo Map

Edit `meta/importer/typo_map.py`:

```python
TYPO_MAP: dict[str, str] = {
    # Add corrections here (keys are lowercased for matching)
    "artifical intelligence": "Artificial Intelligence",
    "machien learning": "Machine Learning",
    # Your custom corrections:
    "your typo here": "Correct Spelling",
}
```

The typo map matches case-insensitively.

## CLI Reference

```
Usage: python -m meta.importer.import_taxonomy [OPTIONS]

Options:
  -i, --in PATH    Input directory containing CSV files [required]
  -o, --out PATH   Output directory for generated files [required]
  -s, --strict     Fail on any data quality issues
  --help           Show this message and exit
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Data quality issues found (strict mode only) |
| 2 | Fatal error (file not found, parse error) |

## Interpreting the DQ Report

### Missing Levels

Rows where L1, L2, or L3 are empty. These may indicate:
- Incomplete data entry
- Continuation rows that should inherit from above
- Intentionally empty hierarchy levels

### Duplicate Terms

Terms that appear multiple times across all input files. Consider:
- Are these intentional (same term in different contexts)?
- Should they be deduplicated?
- Do they indicate data entry errors?

### Suspicious Split Candidates

Terms containing `/` or ` or ` that weren't split. Review these to determine if they should be:
- Split into separate terms
- Left as-is (intentional compound terms)
- Reformatted for consistency

## Dependencies

- **Required**: `typer`, `rich` (CLI), `pyyaml` (YAML output)

All dependencies are installed via `uv sync --extra dev`.

