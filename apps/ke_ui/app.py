"""Knowledge Engine UI - Main Streamlit Application.

Run with: streamlit run apps/ke_ui/app.py
Or via Makefile: make ui
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Knowledge Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
st.sidebar.title("🧠 Knowledge Engine")
st.sidebar.markdown("---")

st.sidebar.markdown("### Evidence Workflow")
st.sidebar.page_link("pages/6_Dashboard.py", label="📊 Dashboard")
st.sidebar.page_link("pages/7_Add_Document.py", label="➕ Add Document")

st.sidebar.markdown("### Meta Importer")
st.sidebar.page_link("pages/2_Importer.py", label="📥 Importer")
st.sidebar.page_link("pages/3_Taxonomy_Browser.py", label="🌳 Taxonomy Browser")
st.sidebar.page_link("pages/4_DQ_Report.py", label="📋 DQ Report")

st.sidebar.markdown("### System")
st.sidebar.page_link("pages/1_Status.py", label="📊 Status")
st.sidebar.page_link("pages/5_DB_Migrations.py", label="🗄️ DB Migrations")

st.sidebar.markdown("---")
st.sidebar.caption("Knowledge Engine v0.1.0")

# Main content
st.title("🧠 Knowledge Engine Control Plane")
st.markdown("---")

st.markdown("""
## Welcome

The Knowledge Engine provides tools for managing knowledge graphs with:
- **Evidence Workflow**: Add documents, extract claims, link evidence
- **Meta-Graph**: Taxonomy, glossary, and control definitions
- **Quality Gates**: Ensure all claims have evidence

### Quick Start

| Workflow | Description |
|----------|-------------|
| **Dashboard** | View/manage documents |
| **Add Document** | Create new document with revision |
| **Document Detail** | Add chunks, claims, evidence |
| **Quality Gate** | Validate claim coverage |

### Getting Started

1. Go to **Dashboard** to view documents
2. Use **Add Document** to create a new entry
3. Open document to add **chunks** and **claims**
4. Link **evidence** to claims
5. Run **Quality Gate** to validate
""")
