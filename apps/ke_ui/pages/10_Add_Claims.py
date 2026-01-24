"""Add Claims - Form with confirmation."""

from uuid import UUID

import streamlit as st

st.set_page_config(page_title="Add Claims - Knowledge Engine", page_icon="📝", layout="wide")

st.title("📝 Add Claims")
st.markdown("---")

rev_id_str = st.session_state.get("add_to_revision_id")
if not rev_id_str:
    st.warning("No revision selected.")
    st.stop()

st.markdown(f"**Revision:** `{rev_id_str[:8]}...`")

CLAIM_TYPES = ["fact", "definition", "requirement", "recommendation", "metric", "other"]

# State
if "pending_claims" not in st.session_state:
    st.session_state["pending_claims"] = []

if "confirm_claims" not in st.session_state:
    st.session_state["confirm_claims"] = False

# ─────────────────────────────────────────────────────────────────────────────
# Confirmation
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["confirm_claims"] and st.session_state["pending_claims"]:
    st.subheader("📋 Confirm Claims")

    for c in st.session_state["pending_claims"]:
        st.write(f"**[{c['claim_type']}]** {c['claim_text'][:80]}...")
        st.caption(f"Confidence: {c['confidence']:.2f}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm & Save", type="primary"):
            try:
                from apps.ke_db.claims import create_claim
                from apps.ke_db.connection import get_connection

                rev_uuid = UUID(rev_id_str)
                with get_connection() as conn:
                    for c in st.session_state["pending_claims"]:
                        create_claim(
                            conn,
                            revision_id=rev_uuid,
                            claim_text=c["claim_text"],
                            claim_type=c["claim_type"],
                            confidence=c["confidence"],
                        )
                    conn.commit()

                st.success(f"✅ {len(st.session_state['pending_claims'])} claim(s) created!")
                st.session_state["pending_claims"] = []
                st.session_state["confirm_claims"] = False

            except Exception as e:
                st.error(f"❌ Error: {e}")

    with col2:
        if st.button("❌ Cancel"):
            st.session_state["confirm_claims"] = False
            st.rerun()

else:
    # ─────────────────────────────────────────────────────────────────────────
    # Form
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("Add Claim")

    with st.form("add_claim_form"):
        claim_text = st.text_area("Claim Text *", height=100)
        col1, col2 = st.columns(2)
        with col1:
            claim_type = st.selectbox("Type", CLAIM_TYPES, index=5)
        with col2:
            confidence = st.slider("Confidence", 0.0, 1.0, 0.70, 0.05)

        submitted = st.form_submit_button("Add to Batch")

        if submitted and claim_text:
            st.session_state["pending_claims"].append({
                "claim_text": claim_text,
                "claim_type": claim_type,
                "confidence": confidence,
            })
            st.rerun()

    # Pending
    if st.session_state["pending_claims"]:
        st.markdown("---")
        st.subheader(f"Pending: {len(st.session_state['pending_claims'])} claim(s)")

        for c in st.session_state["pending_claims"]:
            st.write(f"• [{c['claim_type']}] {c['claim_text'][:60]}...")

        if st.button("📋 Review & Confirm"):
            st.session_state["confirm_claims"] = True
            st.rerun()

        if st.button("🗑️ Clear All"):
            st.session_state["pending_claims"] = []
            st.rerun()
