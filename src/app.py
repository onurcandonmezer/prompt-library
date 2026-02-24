"""Streamlit UI for the Prompt Library.

Provides a web interface for browsing, searching, testing,
and managing prompts in the library.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from src.prompt_manager import PromptManager
from src.prompt_tester import PromptTester

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def init_session_state():
    if "manager" not in st.session_state:
        st.session_state.manager = PromptManager(PROMPTS_DIR)
    if "test_results" not in st.session_state:
        st.session_state.test_results = []


def main():
    st.set_page_config(
        page_title="Prompt Library",
        page_icon="📝",
        layout="wide",
    )

    init_session_state()
    manager = st.session_state.manager

    st.title("📝 Prompt Library")
    st.caption("Enterprise prompt engineering library with testing and management")

    # Sidebar — Navigation & Stats
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to",
            ["Browse", "Search", "Test", "Statistics"],
            label_visibility="collapsed",
        )

        st.divider()
        stats = manager.get_stats()
        st.metric("Total Prompts", stats["total_prompts"])
        st.metric("Categories", stats["categories"])

    if page == "Browse":
        render_browse_page(manager)
    elif page == "Search":
        render_search_page(manager)
    elif page == "Test":
        render_test_page(manager)
    elif page == "Statistics":
        render_stats_page(manager)


def render_browse_page(manager: PromptManager):
    st.header("Browse Prompts")

    categories = manager.get_categories()
    if not categories:
        st.warning("No prompts found. Add YAML files to the prompts/ directory.")
        return

    selected_category = st.selectbox("Category", ["All"] + categories)

    if selected_category == "All":
        prompts = manager.list_prompts()
    else:
        prompts = manager.get_by_category(selected_category)

    for prompt in prompts:
        with st.expander(f"**{prompt.name}** — {prompt.description}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Category:** {prompt.category}")
                st.write(f"**Version:** {prompt.version}")
                st.write(f"**Model:** {prompt.metadata.recommended_model}")
            with col2:
                st.write(f"**Temperature:** {prompt.metadata.temperature}")
                st.write(f"**Expected Tokens:** {prompt.metadata.expected_tokens}")
                if prompt.metadata.tags:
                    st.write(f"**Tags:** {', '.join(prompt.metadata.tags)}")

            st.subheader("Template")
            st.code(prompt.template, language="text")

            if prompt.parameters:
                st.subheader("Parameters")
                for p in prompt.parameters:
                    req = "Required" if p.required else "Optional"
                    st.write(f"- `{p.name}` ({p.type}, {req}): {p.description}")


def render_search_page(manager: PromptManager):
    st.header("Search Prompts")

    query = st.text_input("Search by name, description, or tags")
    if query:
        results = manager.search(query)
        st.write(f"Found {len(results)} results")
        for p in results:
            st.write(f"- **[{p.category}] {p.name}** — {p.description}")
    else:
        st.info("Enter a search term to find prompts.")


def render_test_page(manager: PromptManager):
    st.header("Test Prompts")

    default_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key", type="password", value=default_key)

    if not api_key:
        st.warning("Enter your Gemini API key to test prompts.")
        return

    prompts = manager.list_prompts()
    if not prompts:
        st.warning("No prompts available for testing.")
        return

    prompt_names = [p.name for p in prompts]
    selected = st.selectbox("Select Prompt", prompt_names)
    prompt = manager.get_prompt(selected)

    if prompt:
        st.subheader("Template Preview")
        st.code(prompt.template, language="text")

        st.subheader("Input Parameters")
        inputs = {}
        for param in prompt.parameters:
            default = ""
            if prompt.examples:
                default = prompt.examples[0].input.get(param.name, "")
            inputs[param.name] = st.text_area(
                f"{param.name} ({param.type})",
                value=default,
                key=f"input_{param.name}",
            )

        if st.button("Run Test", type="primary"):
            with st.spinner("Testing prompt..."):
                tester = PromptTester(api_key=api_key)
                result = tester.test_prompt(prompt.file_path, test_input=inputs)

            if result.passed:
                score = result.quality_score
                latency = result.latency_ms
                st.success(f"Passed — Quality: {score:.1f}/10, Latency: {latency:.0f}ms")
            else:
                st.error(f"Failed — {result.error or 'Missing keywords'}")

            st.subheader("Output")
            st.write(result.output)


def render_stats_page(manager: PromptManager):
    st.header("Library Statistics")

    stats = manager.get_stats()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Prompts", stats["total_prompts"])
    with col2:
        st.metric("Categories", stats["categories"])

    st.subheader("Prompts by Category")
    for cat, count in stats["category_counts"].items():
        st.progress(count / max(stats["category_counts"].values()), text=f"{cat}: {count}")

    st.subheader("Models Used")
    for model in stats["models_used"]:
        st.write(f"- {model}")


if __name__ == "__main__":
    main()
