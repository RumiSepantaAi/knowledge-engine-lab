"""Status Page - System health and connectivity checks."""

import os
import sys
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Status - Knowledge Engine", page_icon="📊", layout="wide")

st.title("📊 System Status")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Python Environment
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🐍 Python Environment")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

with col2:
    uv_lock_exists = Path("uv.lock").exists()
    st.metric("uv.lock", "✅ Present" if uv_lock_exists else "⚠️ Missing")

with col3:
    venv_exists = Path(".venv").exists()
    st.metric(".venv", "✅ Present" if venv_exists else "⚠️ Missing")

# ─────────────────────────────────────────────────────────────────────────────
# Environment Variables
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🔑 Environment Variables")

env_vars = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]

env_status = []
for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask password
        display = "****" if "PASSWORD" in var else value
        env_status.append({"Variable": var, "Status": "✅ Set", "Value": display})
    else:
        env_status.append({"Variable": var, "Status": "⚠️ Using default", "Value": "(default)"})

st.table(env_status)

# ─────────────────────────────────────────────────────────────────────────────
# Database Connectivity
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("🐘 Database Connectivity")

# Import here to avoid import errors if psycopg not installed
try:
    from apps.ke_ui.ui_lib.db import check_db_connection, get_migration_count

    is_connected, message = check_db_connection()

    if is_connected:
        st.success(f"✅ Database connected: {message}")

        # Migration count
        migration_count = get_migration_count()
        if migration_count is not None:
            st.metric("Applied Migrations", migration_count)
        else:
            st.warning("Could not query migration count")
    else:
        st.error(f"❌ Database not reachable: {message}")
        st.info("💡 Start the database with: `make db-up`")

except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.info("💡 Ensure psycopg is installed: `uv sync --extra dev`")

# ─────────────────────────────────────────────────────────────────────────────
# Project Structure
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("📁 Project Structure")

paths_to_check = [
    ("db/migrations/", "SQL migrations"),
    ("meta/importer/", "Importer modules"),
    ("tests/fixtures/expected/", "Golden test fixtures"),
    ("docs/", "Documentation"),
]

path_status = []
for path, description in paths_to_check:
    exists = Path(path).exists()
    path_status.append({
        "Path": path,
        "Description": description,
        "Status": "✅ Found" if exists else "❌ Missing",
    })

st.table(path_status)
