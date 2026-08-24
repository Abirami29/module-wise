"""
Epic 7: runs the eval question set through graph-only, vector-only, and the
router, logs all three answers per question, writes a comparison report.

Run: python -m eval.run_comparison
"""
from datetime import datetime
from pathlib import Path

from src.graph.qa_chain import ask_graph
from src.vector.qa_chain import ask_vector
from src.router.langgraph_router import ask as ask_router

OUTPUT_PATH = Path("docs/comparison_report.md")

# (question, expected_category) - matches GROUND_TRUTH.md
EVAL_QUESTIONS = [
    ("Is vpc-base used consistently across all service repos? Which are behind?", "graph"),
    ("What's the blast radius if I change security-group-web?", "graph"),
    ("Is sqs-queue module still in use anywhere?", "graph"),
    ("Which modules have no consumers?", "graph"),
    ("What repos would be affected if rds-postgres changes?", "graph"),
    ("Is there an existing module for provisioning an S3 bucket?", "vector"),
    ("Do we have a module for running containerized services?", "vector"),
    ("What module should I use to set up a Postgres database?", "vector"),
    ("Are there any modules that do almost the same thing?", "ambiguous"),
    ("What's the difference between s3-bucket-standard and s3-bucket-logging?", "ambiguous"),
]


def run_all():
    results = []
    for question, expected_category in EVAL_QUESTIONS:
        print(f"\n=== {question} ===")

        print("  running graph-only...")
        try:
            graph_result = ask_graph(question)
            graph_answer = graph_result["answer"]
        except Exception as e:
            graph_answer = f"[ERROR: {e}]"

        print("  running vector-only...")
        try:
            vector_result = ask_vector(question)
            vector_answer = vector_result["answer"]
        except Exception as e:
            vector_answer = f"[ERROR: {e}]"

        print("  running router...")
        try:
            router_result = ask_router(question)
            router_answer = router_result["answer"]
            router_path = router_result["path_used"]
        except Exception as e:
            router_answer = f"[ERROR: {e}]"
            router_path = "error"

        results.append({
            "question": question,
            "expected_category": expected_category,
            "graph_answer": graph_answer,
            "vector_answer": vector_answer,
            "router_answer": router_answer,
            "router_path": router_path,
        })

    return results


def write_report(results: list[dict]):
    lines = [
        "# GraphRAG vs. Vector RAG Comparison Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Each question below was run through three configurations: the graph-only ",
        "path (GraphCypherQAChain), the vector-only path (embedding similarity search ",
        "+ synthesis), and the LangGraph router (which selects automatically between them).",
        "",
        "---",
        "",
    ]

    for i, r in enumerate(results, 1):
        lines.append(f"## Q{i}: {r['question']}")
        lines.append(f"*Expected category: {r['expected_category']}*")
        lines.append("")
        lines.append(f"**Graph-only answer:**\n> {r['graph_answer']}")
        lines.append("")
        lines.append(f"**Vector-only answer:**\n> {r['vector_answer']}")
        lines.append("")
        lines.append(f"**Router answer** (routed to: `{r['router_path']}`):\n> {r['router_answer']}")
        lines.append("")
        lines.append("**Analysis:** _[fill in: which answer was most correct/useful, and why]_")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("_[fill in after reviewing all 10: overall pattern of when graph wins vs. ")
    lines.append("vector wins vs. they tie; how often the router matched the better path]_")
    lines.append("")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines))
    print(f"\nReport written to {OUTPUT_PATH}")


if __name__ == "__main__":
    all_results = run_all()
    write_report(all_results)