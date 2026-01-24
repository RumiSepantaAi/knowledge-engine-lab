"""DQ Report Page - View data quality reports."""

import streamlit as st

st.set_page_config(page_title="DQ Report - Knowledge Engine", page_icon="📋", layout="wide")

st.title("📋 Data Quality Report")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load DQ Report
# ─────────────────────────────────────────────────────────────────────────────
try:
    from apps.ke_ui.ui_lib.state import get_dq_report

    report = get_dq_report()

    if report is None:
        st.warning("⚠️ No DQ report available")
        st.info("👆 Use the **Importer** page to process CSV files first")
        st.stop()

    # Render markdown
    st.markdown(report)

except ImportError as e:
    st.error(f"❌ Import error: {e}")
