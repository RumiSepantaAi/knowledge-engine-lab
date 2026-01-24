"""Dashboard - Document listing with status."""

import streamlit as st

st.set_page_config(page_title="Dashboard - Knowledge Engine", page_icon="📊", layout="wide")

st.title("📊 Dashboard")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load Documents
# ─────────────────────────────────────────────────────────────────────────────
try:
    from apps.ke_db.connection import get_connection
    from apps.ke_db.documents import list_documents

    with get_connection() as conn:
        docs = list_documents(conn, limit=50)

    if not docs:
        st.info("No documents found. Use **Add Document** to create one.")
        if st.button("➕ Add Document"):
            st.switch_page("pages/7_Add_Document.py")
    else:
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", len(docs))
        with col2:
            validated = sum(1 for d in docs if d["status"] == "validated")
            st.metric("Validated", validated)
        with col3:
            inbox = sum(1 for d in docs if d["status"] == "inbox")
            st.metric("Inbox", inbox)
        with col4:
            st.metric("Other", len(docs) - validated - inbox)

        st.markdown("---")

        # Document table
        st.subheader("📄 Documents")

        # Add button
        if st.button("➕ Add Document"):
            st.switch_page("pages/7_Add_Document.py")

        # Display as table
        for doc in docs:
            status_icon = "✅" if doc["status"] == "validated" else "📥" if doc["status"] == "inbox" else "⏳"
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            with col1:
                st.write(f"**{doc['doc_id']}**")
            with col2:
                st.write(doc["title"][:60])
            with col3:
                st.write(f"{status_icon} {doc['status']}")
            with col4:
                if st.button("View", key=f"view_{doc['id']}"):
                    st.session_state["selected_document_id"] = doc["id"]
                    st.session_state["selected_doc_id"] = doc["doc_id"]
                    st.switch_page("pages/8_Document_Detail.py")

except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.info("💡 Ensure database is running: `make db-up && make db-migrate`")
