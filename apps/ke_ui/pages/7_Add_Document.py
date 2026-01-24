"""Add Document - Form with confirmation."""

import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Add Document - Knowledge Engine", page_icon="➕", layout="wide")

st.title("➕ Add Document")
st.markdown("---")

# Initialize session state for confirmation flow
if "doc_confirm_data" not in st.session_state:
    st.session_state["doc_confirm_data"] = None

# ─────────────────────────────────────────────────────────────────────────────
# Confirmation Screen
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["doc_confirm_data"] is not None:
    data = st.session_state["doc_confirm_data"]

    st.subheader("📋 Confirm Document Creation")

    st.markdown(f"""
    | Field | Value |
    |-------|-------|
    | **Doc ID** | `{data['doc_id']}` |
    | **Title** | {data['title']} |
    | **Authors** | {data['authors'] or '(none)'} |
    | **Publisher** | {data['publisher_org'] or '(none)'} |
    | **Published** | {data['published_date'] or '(none)'} |
    | **File** | `{data['file_uri']}` |
    | **SHA256** | `{data['sha256'][:32]}...` |
    | **Tags** | {', '.join(data['tags']) if data['tags'] else '(none)'} |
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm & Save", type="primary"):
            try:
                from apps.ke_db.connection import get_connection
                from apps.ke_db.documents import create_document, create_revision

                with get_connection() as conn:
                    doc_uuid = create_document(
                        conn,
                        doc_id=data["doc_id"],
                        title=data["title"],
                        file_uri=data["file_uri"],
                        sha256=data["sha256"],
                        authors=data["authors"],
                        publisher_org=data["publisher_org"],
                        published_date=data["published_date"],
                        source_url=data["source_url"],
                        tags=data["tags"],
                    )
                    rev_uuid = create_revision(
                        conn,
                        document_id=doc_uuid,
                        revision_no=1,
                        sha256=data["sha256"],
                        file_uri=data["file_uri"],
                        parser_version="ui/v1",
                        notes="Initial revision via UI",
                    )
                    conn.commit()

                st.success(f"✅ Document created!")
                st.code(f"Document UUID: {doc_uuid}\nRevision UUID: {rev_uuid}")
                st.session_state["doc_confirm_data"] = None

                if st.button("📊 Go to Dashboard"):
                    st.switch_page("pages/6_Dashboard.py")

            except Exception as e:
                st.error(f"❌ Error: {e}")

    with col2:
        if st.button("❌ Cancel"):
            st.session_state["doc_confirm_data"] = None
            st.rerun()

else:
    # ─────────────────────────────────────────────────────────────────────────
    # Form
    # ─────────────────────────────────────────────────────────────────────────
    with st.form("add_document_form"):
        st.subheader("Document Details")

        col1, col2 = st.columns(2)
        with col1:
            doc_id = st.text_input("Document ID *", placeholder="DOC-0001", help="Format: XXX-NNNN")
            title = st.text_input("Title *", placeholder="Document title")
            authors = st.text_input("Authors", placeholder="Author names")
            publisher_org = st.text_input("Publisher Organization")

        with col2:
            published_date = st.date_input("Published Date", value=None)
            source_url = st.text_input("Source URL", placeholder="https://...")
            tags_str = st.text_input("Tags", placeholder="tag1, tag2, tag3")
            file_path = st.text_input("File Path *", placeholder="/path/to/document.pdf")

        # Optional file upload
        uploaded_file = st.file_uploader("Or upload file", type=["pdf", "txt", "md"])

        submitted = st.form_submit_button("Review Before Saving", type="primary")

        if submitted:
            # Validation
            errors = []

            import re
            if not doc_id or not re.match(r"^[A-Z]{3}-[0-9]{4,}$", doc_id):
                errors.append("Invalid Doc ID format (use XXX-NNNN)")

            if not title:
                errors.append("Title is required")

            # Determine file path and compute SHA256
            actual_path = None
            sha256 = None

            if uploaded_file:
                # Save to temp and compute SHA256
                import hashlib
                content = uploaded_file.read()
                sha256 = hashlib.sha256(content).hexdigest()
                actual_path = f"uploads/{uploaded_file.name}"
            elif file_path:
                path = Path(file_path)
                if path.exists():
                    from apps.ke_db.utils import compute_sha256
                    sha256 = compute_sha256(path)
                    actual_path = str(path.absolute())
                else:
                    errors.append(f"File not found: {file_path}")
            else:
                errors.append("File path or upload required")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                # Store for confirmation
                tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
                st.session_state["doc_confirm_data"] = {
                    "doc_id": doc_id,
                    "title": title,
                    "authors": authors or None,
                    "publisher_org": publisher_org or None,
                    "published_date": published_date if published_date else None,
                    "source_url": source_url or None,
                    "tags": tags,
                    "file_uri": actual_path,
                    "sha256": sha256,
                }
                st.rerun()
