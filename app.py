"""
Module-Wise: GraphRAG for Terraform module dependencies.
"""
from pathlib import Path

import streamlit as st

from src.router.langgraph_router import ask

st.set_page_config(page_title="Module-Wise", page_icon="🧩", layout="centered")

st.title("🧩 Module-Wise")
st.caption("Ask about Terraform module usage, versions, blast radius, or find existing modules by purpose.")

with st.sidebar:
    st.subheader("About")
    st.write(
        "Routes questions between a Neo4j knowledge graph (structural/relational "
        "questions) and a vector store (semantic 'is there a module for X' questions), "
        "using a LangGraph router with automatic fallback."
    )
    st.divider()
    st.subheader("Try asking")
    st.markdown(
        "- *What repos would be affected if rds-postgres changes?*\n"
        "- *Is sqs-queue still in use anywhere?* (expect: no consumers found - it's an orphaned module)\n"
        "- *Is there a module for provisioning an S3 bucket?*\n"
        "- *Do we have a module for running containerized services?*"
    )

tab_chat, tab_repos = st.tabs(["💬 Chat", "📁 Browse Repos"])

with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("path_used"):
                st.caption(f"🔀 routed to: **{msg['path_used']}**")

    if question := st.chat_input("Ask about the module registry..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = ask(question)
            st.markdown(result["answer"])
            st.caption(f"🔀 routed to: **{result['path_used']}**" + (
                f" (fallback from {result['attempted_paths'][0]})" if len(result["attempted_paths"]) > 1 else ""
            ))

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "path_used": result["path_used"],
        })

with tab_repos:
    st.subheader("Sample repos in this project")

    DATA_DIR = Path("data/github-repos")

    if not DATA_DIR.exists():
        st.warning("No repos found under data/github-repos.")
    else:
        repo_names = sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir())
        selected_repo = st.selectbox("Choose a repo", repo_names)

        repo_path = DATA_DIR / selected_repo
        modules_dir = repo_path / "modules"

        if modules_dir.exists():
            st.caption("This is the shared modules registry repo.")
            module_names = sorted(p.name for p in modules_dir.iterdir() if p.is_dir())
            selected_module = st.selectbox("Choose a module", module_names)
            module_path = modules_dir / selected_module

            readme_path = module_path / "README.md"
            if readme_path.exists():
                st.markdown(readme_path.read_text())

            st.divider()
            tf_files = sorted(module_path.glob("*.tf"))
            file_names = [f.name for f in tf_files]
            if file_names:
                selected_file = st.selectbox("View .tf file", file_names)
                st.code((module_path / selected_file).read_text(), language="hcl")
        else:
            st.caption("This is a consumer repo (uses modules from infra-modules).")
            readme_path = repo_path / "README.md"
            if readme_path.exists():
                st.markdown(readme_path.read_text())

            st.divider()
            tf_files = sorted(repo_path.glob("*.tf"))
            file_names = [f.name for f in tf_files]
            if file_names:
                selected_file = st.selectbox("View .tf file", file_names)
                st.code((repo_path / selected_file).read_text(), language="hcl")

with st.sidebar:
    st.divider()
    st.subheader("Admin")
    if st.button("🔄 Rebuild Graph + Vector Index"):
        with st.spinner("Rebuilding..."):
            from src.graph.build_graph import build_full_graph
            from src.vector.build_index import build_vector_store
            build_full_graph(clear_first=True)
            build_vector_store(clear_first=True)
        st.success("Rebuilt from current repo state.")