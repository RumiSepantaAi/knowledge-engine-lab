"""Importer Page - Upload and process taxonomy CSVs."""

import streamlit as st

st.set_page_config(page_title="Importer - Knowledge Engine", page_icon="📥", layout="wide")

st.title("📥 Taxonomy Importer")
st.markdown("---")

st.markdown("""
Upload one or more CSV files containing taxonomy data. The importer will:
- Parse and normalize terms
- Split Level 4 on semicolons (preserving parenthetical content)
- Generate deterministic UUIDs
- Produce clean outputs
""")

# ─────────────────────────────────────────────────────────────────────────────
# File Upload
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📁 Upload CSV Files")

uploaded_files = st.file_uploader(
    "Choose CSV files",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload taxonomy CSV files with columns: Level 1, Level 2, Level 3, Level 4",
)

# Options
col1, col2 = st.columns(2)
with col1:
    strict_mode = st.checkbox(
        "Strict mode",
        value=False,
        help="Fail on any data quality issues",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Run Import
# ─────────────────────────────────────────────────────────────────────────────
if uploaded_files:
    st.markdown("---")
    st.subheader("📋 Files to Process")

    for f in uploaded_files:
        st.text(f"  • {f.name} ({f.size:,} bytes)")

    if st.button("🚀 Run Import", type="primary"):
        with st.spinner("Processing..."):
            try:
                from apps.ke_ui.ui_lib.importer import run_import
                from apps.ke_ui.ui_lib.state import set_last_import_results

                # Prepare files
                input_files = [(f.name, f.getvalue()) for f in uploaded_files]

                # Run import
                result = run_import(input_files, strict=strict_mode)

                if result.success:
                    st.success(f"✅ {result.message}")

                    # Store results in session state
                    set_last_import_results({
                        "files": result.files,
                        "stats": result.stats,
                    })

                    # Show stats
                    if result.stats:
                        st.subheader("📊 Statistics")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Files Processed", result.stats.files_processed)
                        with col2:
                            st.metric("Rows Processed", result.stats.rows_processed)
                        with col3:
                            st.metric("Unique Terms", result.stats.unique_terms)
                        with col4:
                            issues = (
                                len(result.stats.missing_levels)
                                + len(result.stats.duplicate_terms)
                                + len(result.stats.empty_terms)
                            )
                            st.metric("Issues Found", issues)

                    # Download buttons
                    st.subheader("📥 Download Outputs")

                    if result.files:
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.download_button(
                                "📄 taxonomy_clean.csv",
                                result.files.get("taxonomy_clean.csv", b""),
                                "taxonomy_clean.csv",
                                "text/csv",
                            )
                            st.download_button(
                                "📄 terms_normalized.csv",
                                result.files.get("terms_normalized.csv", b""),
                                "terms_normalized.csv",
                                "text/csv",
                            )

                        with col2:
                            st.download_button(
                                "📄 taxonomy_tree.json",
                                result.files.get("taxonomy_tree.json", b""),
                                "taxonomy_tree.json",
                                "application/json",
                            )
                            st.download_button(
                                "📄 taxonomy_tree.yaml",
                                result.files.get("taxonomy_tree.yaml", b""),
                                "taxonomy_tree.yaml",
                                "text/yaml",
                            )

                        with col3:
                            st.download_button(
                                "📄 dq_report.md",
                                result.files.get("dq_report.md", b""),
                                "dq_report.md",
                                "text/markdown",
                            )
                else:
                    st.error(f"❌ {result.message}")

            except Exception as e:
                st.error(f"❌ Import failed: {e}")
else:
    st.info("👆 Upload CSV files to get started")

# ─────────────────────────────────────────────────────────────────────────────
# Expected Format
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📖 Expected CSV Format"):
    st.markdown("""
    ### Column Names (case-insensitive)

    | Level | Accepted Names |
    |-------|----------------|
    | Level 1 | `Level 1`, `L1`, `Domain`, `Category` |
    | Level 2 | `Level 2`, `L2`, `Subdomain`, `Subcategory` |
    | Level 3 | `Level 3`, `L3`, `Topic`, `Area` |
    | Level 4 | `Level 4`, `L4`, `Term`, `Terms` |

    ### Example

    ```csv
    Level 1,Level 2,Level 3,Level 4
    AI,Machine Learning,Supervised,Linear Regression; Logistic Regression
    AI,Machine Learning,Unsupervised,K-Means; 3-Layer Vector DB (Evidence; Implication)
    ```

    **Note**: Semicolons inside parentheses are preserved.
    """)
