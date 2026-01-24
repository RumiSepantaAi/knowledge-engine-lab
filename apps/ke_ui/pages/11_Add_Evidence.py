"""Add Evidence - Link claim to chunk."""

from uuid import UUID

import streamlit as st

st.set_page_config(page_title="Add Evidence - Knowledge Engine", page_icon="🔗", layout="wide")

st.title("🔗 Add Evidence")
st.markdown("---")

claim_id_str = st.session_state.get("add_evidence_claim_id")
rev_id_str = st.session_state.get("add_evidence_revision_id")

if not claim_id_str:
    st.warning("No claim selected.")
    st.stop()

st.markdown(f"**Claim:** `{claim_id_str[:8]}...`")

EVIDENCE_ROLES = ["supports", "contradicts", "mentions"]

# State
if "evidence_confirm_data" not in st.session_state:
    st.session_state["evidence_confirm_data"] = None

# ─────────────────────────────────────────────────────────────────────────────
# Confirmation
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["evidence_confirm_data"]:
    data = st.session_state["evidence_confirm_data"]

    st.subheader("📋 Confirm Evidence")

    st.markdown(f"""
    | Field | Value |
    |-------|-------|
    | **Claim** | `{data['claim_id'][:16]}...` |
    | **Chunk** | `{data['chunk_id'][:16]}...` |
    | **Role** | {data['role']} |
    | **Strength** | {data['support_strength']:.2f} |
    | **Snippet** | {data['snippet'][:80]}... |
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm & Save", type="primary"):
            try:
                from apps.ke_db.connection import get_connection
                from apps.ke_db.evidence import create_evidence_span

                with get_connection() as conn:
                    span_id = create_evidence_span(
                        conn,
                        claim_id=UUID(data["claim_id"]),
                        chunk_id=UUID(data["chunk_id"]),
                        snippet=data["snippet"],
                        role=data["role"],
                        page_no=data["page_no"],
                        support_strength=data["support_strength"],
                    )
                    conn.commit()

                st.success(f"✅ Evidence created!")
                st.code(f"Span UUID: {span_id}")
                st.session_state["evidence_confirm_data"] = None

            except Exception as e:
                st.error(f"❌ Error: {e}")

    with col2:
        if st.button("❌ Cancel"):
            st.session_state["evidence_confirm_data"] = None
            st.rerun()

else:
    # ─────────────────────────────────────────────────────────────────────────
    # Form
    # ─────────────────────────────────────────────────────────────────────────
    from apps.ke_db.chunks import list_chunks_for_revision
    from apps.ke_db.connection import get_connection

    # Load chunks for selection
    with get_connection() as conn:
        chunks = list_chunks_for_revision(conn, UUID(rev_id_str))

    if not chunks:
        st.warning("No chunks available. Add chunks first.")
        st.stop()

    chunk_options = {f"#{c['chunk_no']}: {c['preview'][:40]}...": str(c["id"]) for c in chunks}

    with st.form("add_evidence_form"):
        selected_chunk_label = st.selectbox("Select Chunk", list(chunk_options.keys()))
        role = st.selectbox("Role", EVIDENCE_ROLES)
        snippet = st.text_area("Evidence Snippet *", height=100, help="Quote from the chunk")
        col1, col2 = st.columns(2)
        with col1:
            page_no = st.number_input("Page Number", min_value=1, value=1)
        with col2:
            strength = st.slider("Support Strength", 0.0, 1.0, 0.80, 0.05)

        submitted = st.form_submit_button("Review Before Saving", type="primary")

        if submitted and snippet:
            st.session_state["evidence_confirm_data"] = {
                "claim_id": claim_id_str,
                "chunk_id": chunk_options[selected_chunk_label],
                "role": role,
                "snippet": snippet,
                "page_no": page_no,
                "support_strength": strength,
            }
            st.rerun()
