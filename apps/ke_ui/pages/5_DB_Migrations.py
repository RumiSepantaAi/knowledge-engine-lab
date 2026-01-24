"""DB Migrations Page - View applied migrations and drift status."""

import streamlit as st

st.set_page_config(page_title="DB Migrations - Knowledge Engine", page_icon="🗄️", layout="wide")

st.title("🗄️ Database Migrations")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load Migrations
# ─────────────────────────────────────────────────────────────────────────────
try:
    from apps.ke_ui.ui_lib.db import (
        check_db_connection,
        check_migration_drift,
        get_applied_migrations,
    )

    # Check DB connection first
    is_connected, message = check_db_connection()

    if not is_connected:
        st.error(f"❌ Database not reachable: {message}")
        st.info("💡 Start the database with: `make db-up`")
        st.stop()

    st.success("✅ Database connected")

    # Get migrations
    migrations = get_applied_migrations()

    if not migrations:
        st.warning("⚠️ No migrations applied yet")
        st.info("💡 Run migrations with: `make db-migrate`")
        st.stop()

    # Check for drift
    migrations = check_migration_drift(migrations)

    # Count drift warnings
    drift_count = sum(1 for m in migrations if m.has_drift)

    if drift_count > 0:
        st.warning(f"⚠️ {drift_count} migration(s) have drifted since application!")
        st.markdown("""
        **Drift** means the migration file has been modified after it was applied.
        This could indicate:
        - Intentional changes (may need to reset DB and re-apply)
        - Accidental modifications
        """)

    # ─────────────────────────────────────────────────────────────────────────
    # Migrations Table
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader(f"📋 Applied Migrations ({len(migrations)})")

    # Build table data
    table_data = []
    for m in migrations:
        row = {
            "Filename": m.filename,
            "SHA256": (m.content_sha256[:16] + "...") if m.content_sha256 else "N/A",
            "Applied At": m.applied_at,
            "Status": "⚠️ DRIFT" if m.has_drift else "✅ OK",
        }
        table_data.append(row)

    st.table(table_data)

    # ─────────────────────────────────────────────────────────────────────────
    # Drift Details
    # ─────────────────────────────────────────────────────────────────────────
    if drift_count > 0:
        with st.expander("🔍 Drift Details"):
            for m in migrations:
                if m.has_drift:
                    st.markdown(f"### {m.filename}")
                    st.markdown(f"- **Stored SHA256**: `{m.content_sha256[:16]}...`")
                    st.markdown(f"- **Current SHA256**: `{m.current_sha256[:16] if m.current_sha256 else 'N/A'}...`")

except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.info("💡 Ensure psycopg is installed: `uv sync --extra dev`")
