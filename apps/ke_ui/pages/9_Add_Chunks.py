"""Add Chunks - Form with confirmation."""

from uuid import UUID

import streamlit as st

st.set_page_config(page_title="Add Chunks - Knowledge Engine", page_icon="📦", layout="wide")

st.title("📦 Add Chunks")
st.markdown("---")

rev_id_str = st.session_state.get("add_to_revision_id")
if not rev_id_str:
    st.warning("No revision selected.")
    st.stop()

st.markdown(f"**Revision:** `{rev_id_str[:8]}...`")

# State for chunks being added
if "pending_chunks" not in st.session_state:
    st.session_state["pending_chunks"] = []

if "confirm_chunks" not in st.session_state:
    st.session_state["confirm_chunks"] = False

# ─────────────────────────────────────────────────────────────────────────────
# Confirmation Screen
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["confirm_chunks"] and st.session_state["pending_chunks"]:
    st.subheader("📋 Confirm Chunks")

    for i, c in enumerate(st.session_state["pending_chunks"]):
        st.write(f"**Chunk #{c['chunk_no']}** (Page {c['page_start'] or '-'})")
        st.caption(c["text"][:100] + "..." if len(c["text"]) > 100 else c["text"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm & Save", type="primary"):
            try:
                from apps.ke_db.chunks import create_chunk
                from apps.ke_db.connection import get_connection

                rev_uuid = UUID(rev_id_str)
                with get_connection() as conn:
                    for c in st.session_state["pending_chunks"]:
                        create_chunk(
                            conn,
                            revision_id=rev_uuid,
                            chunk_no=c["chunk_no"],
                            text=c["text"],
                            page_start=c["page_start"],
                            page_end=c["page_start"],
                            section_path=c["section_path"],
                        )
                    conn.commit()

                st.success(f"✅ {len(st.session_state['pending_chunks'])} chunk(s) created!")
                st.session_state["pending_chunks"] = []
                st.session_state["confirm_chunks"] = False

            except Exception as e:
                st.error(f"❌ Error: {e}")

    with col2:
        if st.button("❌ Cancel"):
            st.session_state["confirm_chunks"] = False
            st.rerun()

else:
    # ─────────────────────────────────────────────────────────────────────────
    # Form
    # ─────────────────────────────────────────────────────────────────────────
    from apps.ke_db.chunks import get_next_chunk_no
    from apps.ke_db.connection import get_connection

    with get_connection() as conn:
        next_no = get_next_chunk_no(conn, UUID(rev_id_str))

    current_no = next_no + len(st.session_state["pending_chunks"])

    st.subheader(f"Add Chunk #{current_no}")

    with st.form("add_chunk_form"):
        text = st.text_area("Text Content *", height=150)
        col1, col2 = st.columns(2)
        with col1:
            page = st.number_input("Page Number", min_value=1, value=1)
        with col2:
            section = st.text_input("Section Path", placeholder="Chapter 1 > Introduction")

        submitted = st.form_submit_button("Add to Batch")

        if submitted and text:
            st.session_state["pending_chunks"].append({
                "chunk_no": current_no,
                "text": text,
                "page_start": page,
                "section_path": section or None,
            })
            st.rerun()

    # Show pending chunks
    if st.session_state["pending_chunks"]:
        st.markdown("---")
        st.subheader(f"Pending: {len(st.session_state['pending_chunks'])} chunk(s)")

        for c in st.session_state["pending_chunks"]:
            st.write(f"• Chunk #{c['chunk_no']}: {c['text'][:50]}...")

        if st.button("📋 Review & Confirm"):
            st.session_state["confirm_chunks"] = True
            st.rerun()

        if st.button("🗑️ Clear All"):
            st.session_state["pending_chunks"] = []
            st.rerun()
