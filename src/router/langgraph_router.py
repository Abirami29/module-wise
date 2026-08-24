"""
Epic 6: routes a natural-language question to either the graph chain (4.2)
or the vector chain (5), based on question shape. Falls back to the other
path if the first attempt looks empty/unhelpful.
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END

from src.graph.qa_chain import ask_graph
from src.vector.build_index import load_vector_store
from src.llm.nebius_client import get_llm, invoke_json

CLASSIFY_PROMPT = """Classify this question about a Terraform module registry as either
"structural" or "semantic".

"structural" = about relationships, versions, usage, dependencies, blast radius,
  orphaned/unused modules, consistency across repos - anything answerable by
  querying a graph of repos/modules/consumption edges.
Examples: "what's the blast radius of X", "is X used anywhere", "which repos
  are behind on version", "what depends on X".

"semantic" = about finding a module by purpose/description/capability - anything
  answerable by matching meaning against documentation text.
Examples: "is there a module for X", "what should I use to provision Y",
  "do we have something that does Z".

Question: {question}

Respond ONLY with valid JSON, no other text:
{{"category": "structural" or "semantic"}}
"""


class RouterState(TypedDict):
    question: str
    category: str
    answer: str
    path_used: str
    attempted_paths: list[str]


def classify_question(state: RouterState) -> RouterState:
    llm = get_llm(max_tokens=256, frequency_penalty=0.4)
    result = invoke_json(llm, CLASSIFY_PROMPT.format(question=state["question"]))
    category = result.get("category", "structural") if "_error" not in result else "structural"
    return {**state, "category": category, "attempted_paths": []}


def run_graph_path(state: RouterState) -> RouterState:
    result = ask_graph(state["question"])
    answer = result["answer"]
    attempted = state["attempted_paths"] + ["graph"]
    return {**state, "answer": answer, "path_used": "graph", "attempted_paths": attempted}


def run_vector_path(state: RouterState) -> RouterState:
    store = load_vector_store()
    results = store.similarity_search(state["question"], k=3)
    if results:
        summary = "\n\n".join(
            f"[{r.metadata.get('module_name', r.metadata.get('source_path'))}]\n{r.page_content[:300]}"
            for r in results
        )
        answer = f"Found relevant documentation:\n\n{summary}"
    else:
        answer = ""
    attempted = state["attempted_paths"] + ["vector"]
    return {**state, "answer": answer, "path_used": "vector", "attempted_paths": attempted}


def is_answer_weak(answer: str) -> bool:
    """Heuristic: empty, or a hedge/non-answer phrase, counts as weak."""
    if not answer or not answer.strip():
        return True
    weak_phrases = ["cannot determine", "don't have", "no information", "not sure"]
    return any(p in answer.lower() for p in weak_phrases)


def route_decision(state: RouterState) -> str:
    return "graph" if state["category"] == "structural" else "vector"


def fallback_decision(state: RouterState) -> str:
    """After the first path runs, decide whether to try the other one."""
    if is_answer_weak(state["answer"]) and len(state["attempted_paths"]) < 2:
        # try whichever path hasn't been attempted yet
        return "vector" if "graph" in state["attempted_paths"] else "graph"
    return "end"


def build_router():
    graph = StateGraph(RouterState)

    graph.add_node("classify", classify_question)
    graph.add_node("graph_path", run_graph_path)
    graph.add_node("vector_path", run_vector_path)

    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route_decision, {"graph": "graph_path", "vector": "vector_path"})

    graph.add_conditional_edges("graph_path", fallback_decision, {"vector": "vector_path", "end": END})
    graph.add_conditional_edges("vector_path", fallback_decision, {"graph": "graph_path", "end": END})

    return graph.compile()


def ask(question: str) -> dict:
    router = build_router()
    final_state = router.invoke({"question": question, "attempted_paths": []})
    return {
        "question": question,
        "answer": final_state["answer"],
        "category": final_state["category"],
        "path_used": final_state["path_used"],
        "attempted_paths": final_state["attempted_paths"],
    }