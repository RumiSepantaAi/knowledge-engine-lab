"""Document Detail - Chunks, Claims, Evidence."""

from uuid import UUID

import streamlit as st

st.set_page_config(page_title="Document Detail - Knowledge Engine", page_icon="📄", layout="wide")

st.title("📄 Document Detail")

# Get selected document from session state
doc_id_str = st.session_state.get("selected_document_id")
doc_id_display = st.session_state.get("selected_doc_id", "Unknown")

if not doc_id_str:
    st.warning("No document selected. Go to Dashboard first.")
    if st.button("📊 Go to Dashboard"):
        st.switch_page("pages/6_Dashboard.py")
    st.stop()

st.markdown(f"**Document:** `{doc_id_display}`")
st.markdown("---")

try:
    from apps.ke_db.chunks import list_chunks_for_revision
    from apps.ke_db.claims import list_claims_for_revision
    from apps.ke_db.connection import get_connection
    from apps.ke_db.documents import list_revisions
    from apps.ke_db.evidence import list_evidence_for_claim
    from apps.ke_db.quality import check_quality_gate

    doc_uuid = UUID(doc_id_str)

    with get_connection() as conn:
        revisions = list_revisions(conn, doc_uuid)

    if not revisions:
        st.warning("No revisions found for this document.")
        st.stop()

    # Select revision
    rev_options = {f"Rev {r['revision_no']} ({r['created_at'].date()})": r["id"] for r in revisions}
    selected_rev_label = st.selectbox("Select Revision", list(rev_options.keys()))
    rev_id = rev_options[selected_rev_label]

    # Tabs for different views
    tab_chunks, tab_claims, tab_quality = st.tabs(["📦 Chunks", "📝 Claims", "🔍 Quality Gate"])

    with tab_chunks:
        st.subheader("Chunks")

        with get_connection() as conn:
            chunks = list_chunks_for_revision(conn, rev_id)

        if not chunks:
            st.info("No chunks yet.")
        else:
            for c in chunks:
                with st.expander(f"Chunk #{c['chunk_no']} (Page {c['page_start'] or '-'})"):
                    st.write(c["preview"])
                    st.caption(f"ID: {c['id']}")

        if st.button("➕ Add Chunks"):
            st.session_state["add_to_revision_id"] = str(rev_id)
            st.switch_page("pages/9_Add_Chunks.py")

    with tab_claims:
        st.subheader("Claims")

        with get_connection() as conn:
            claims = list_claims_for_revision(conn, rev_id)

        if not claims:
            st.info("No claims yet.")
        else:
            for c in claims:
                with st.expander(f"{c['claim_type'].upper()}: {c['preview'][:50]}..."):
                    st.write(f"**Confidence:** {c['confidence']:.2f}")
                    st.caption(f"ID: {c['id']}")

                    # Show evidence for this claim
                    with get_connection() as conn:
                        evidence = list_evidence_for_claim(conn, c["id"])

                    if evidence:
                        st.write("**Evidence:**")
                        for e in evidence:
                            st.write(f"  - [{e['role']}] {e['preview']}")
                    else:
                        st.warning("⚠️ No evidence linked")

                    if st.button("🔗 Add Evidence", key=f"add_ev_{c['id']}"):
                        st.session_state["add_evidence_claim_id"] = str(c["id"])
                        st.session_state["add_evidence_revision_id"] = str(rev_id)
                        st.switch_page("pages/11_Add_Evidence.py")

        if st.button("➕ Add Claims"):
            st.session_state["add_to_revision_id"] = str(rev_id)
            st.switch_page("pages/10_Add_Claims.py")

    with tab_quality:
        st.subheader("Quality Gate")

        with get_connection() as conn:
            result = check_quality_gate(conn, rev_id)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Claims", result["total_claims"])
        with col2:
            st.metric("With Evidence", result["claims_with_evidence"])
        with col3:
            st.metric("Without Evidence", result["claims_without_evidence"])

        if result["passed"]:
            st.success("✅ PASS - All claims have evidence!")

            if st.button("Mark Document as Validated"):
                from apps.ke_db.quality import set_document_validated

                with get_connection() as conn:
                    set_document_validated(conn, doc_uuid)
                    conn.commit()
                st.success("Document marked as validated!")
        else:
            st.error(f"❌ FAIL - {result['claims_without_evidence']} claim(s) missing evidence")

except Exception as e:
    st.error(f"❌ Error: {e}")
