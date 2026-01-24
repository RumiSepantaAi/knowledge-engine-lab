"""Taxonomy Browser Page - Explore and search taxonomy tree."""

import streamlit as st

st.set_page_config(page_title="Taxonomy Browser - Knowledge Engine", page_icon="🌳", layout="wide")

st.title("🌳 Taxonomy Browser")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Load Taxonomy Tree
# ─────────────────────────────────────────────────────────────────────────────
try:
    from apps.ke_ui.ui_lib.state import get_taxonomy_tree

    tree = get_taxonomy_tree()

    if tree is None:
        st.warning("⚠️ No taxonomy tree available")
        st.info("👆 Use the **Importer** page to process CSV files first")
        st.stop()

    # ─────────────────────────────────────────────────────────────────────────
    # Search
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("🔍 Search")

    search_query = st.text_input(
        "Search terms",
        placeholder="Type to search across all terms...",
    )

    if search_query:
        # Flatten tree and search
        results = []
        query_lower = search_query.lower()

        for l1, l1_data in tree.items():
            if query_lower in l1.lower():
                results.append({"Level 1": l1, "Level 2": "-", "Level 3": "-", "Term": l1})

            if isinstance(l1_data, dict):
                for l2, l2_data in l1_data.items():
                    if query_lower in l2.lower():
                        results.append({"Level 1": l1, "Level 2": l2, "Level 3": "-", "Term": l2})

                    if isinstance(l2_data, dict):
                        for l3, terms in l2_data.items():
                            if query_lower in l3.lower():
                                results.append({"Level 1": l1, "Level 2": l2, "Level 3": l3, "Term": l3})

                            if isinstance(terms, list):
                                for term in terms:
                                    if query_lower in term.lower():
                                        results.append({
                                            "Level 1": l1,
                                            "Level 2": l2,
                                            "Level 3": l3,
                                            "Term": term,
                                        })

        st.write(f"Found {len(results)} result(s)")
        if results:
            st.table(results[:50])  # Limit to 50 results
    else:
        st.caption("Enter a search term above or browse below")

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # Browse Tree
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("📂 Browse Taxonomy")

    # Level 1 selector
    l1_options = sorted(tree.keys())
    selected_l1 = st.selectbox("Level 1 (Domain)", ["(Select...)"] + l1_options)

    if selected_l1 and selected_l1 != "(Select...)":
        l1_data = tree.get(selected_l1, {})

        if isinstance(l1_data, dict):
            # Level 2 selector
            l2_options = sorted(l1_data.keys())
            selected_l2 = st.selectbox("Level 2 (Category)", ["(Select...)"] + l2_options)

            if selected_l2 and selected_l2 != "(Select...)":
                l2_data = l1_data.get(selected_l2, {})

                if isinstance(l2_data, dict):
                    # Level 3 selector
                    l3_options = sorted(l2_data.keys())
                    selected_l3 = st.selectbox("Level 3 (Subcategory)", ["(Select...)"] + l3_options)

                    if selected_l3 and selected_l3 != "(Select...)":
                        terms = l2_data.get(selected_l3, [])

                        if isinstance(terms, list) and terms:
                            st.markdown("### 📝 Terms")
                            for term in sorted(terms):
                                st.markdown(f"- {term}")
                        else:
                            st.info("No terms found for this category")

    # ─────────────────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Tree Statistics")

    # Count nodes
    l1_count = len(tree)
    l2_count = 0
    l3_count = 0
    term_count = 0

    for l1_data in tree.values():
        if isinstance(l1_data, dict):
            l2_count += len(l1_data)
            for l2_data in l1_data.values():
                if isinstance(l2_data, dict):
                    l3_count += len(l2_data)
                    for terms in l2_data.values():
                        if isinstance(terms, list):
                            term_count += len(terms)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Level 1 (Domains)", l1_count)
    with col2:
        st.metric("Level 2 (Categories)", l2_count)
    with col3:
        st.metric("Level 3 (Subcategories)", l3_count)
    with col4:
        st.metric("Level 4 (Terms)", term_count)

except ImportError as e:
    st.error(f"❌ Import error: {e}")
