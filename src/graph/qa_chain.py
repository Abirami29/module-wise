"""
Natural-language Q&A over the Neo4j graph.

Strategy: use a small, structured LLM call to extract intent + target module
name from the question (reliable - same pattern as the router's classify
step, short prompt/output, low repetition-loop risk). If a known intent is
extracted, answer via Epic 3's proven deterministic Cypher queries (zero LLM
involvement in the actual data lookup). Only questions where extraction
returns "none" fall through to the LLM-generated-Cypher fallback path.

This replaces an earlier regex-based version, which only matched a fixed set
of exact phrasings - any variation in wording fell through to the less
reliable LLM fallback path even for common, well-understood question types.
"""
from src.graph.queries import find_unused_modules, find_version_drift, find_consumers_of
from src.llm.nebius_client import get_llm, invoke_json

INTENT_PROMPT = """Extract the intent and target module from this question about a
Terraform module registry. Always respond in English.

Intents:
- "blast_radius": asking what repos/services would be affected if a module changes,
  or who depends on / uses / relies on a module
- "unused": asking if a specific module is used/unused/still in use/has no consumers
- "unused_all": asking which modules (in general, not a specific one) have no consumers
- "version_drift": asking about version consistency, drift, or whether repos are
  behind on a specific module's version
- "none": doesn't clearly match any of the above

If a specific module name is mentioned or clearly implied, extract it exactly as
written (lowercase, hyphenated, e.g. "rds-postgres"). If no specific module is
named, use null.

Question: {question}

Respond ONLY with valid JSON, no other text:
{{"intent": "blast_radius" | "unused" | "unused_all" | "version_drift" | "none", "module_name": "exact-module-name" | null}}
"""


def _extract_intent(question: str) -> dict:
    llm = get_llm(max_tokens=256, frequency_penalty=0.4)
    result = invoke_json(llm, INTENT_PROMPT.format(question=question))
    if "_error" in result:
        return {"intent": "none", "module_name": None}
    return result


def _answer_blast_radius(module_name: str) -> str:
    consumers = find_consumers_of(module_name)
    if not consumers:
        return f"No repos currently consume '{module_name}' (based on graph data)."
    repos = ", ".join(f"{c['repo_id']} ({c['version']})" for c in consumers)
    return f"Changing '{module_name}' would affect: {repos}."


def _answer_unused_specific(module_name: str) -> str:
    unused = find_unused_modules()
    unused_names = {u["module_name"] for u in unused}
    if module_name in unused_names:
        return f"No, '{module_name}' has no consumers currently - it appears unused."
    consumers = find_consumers_of(module_name)
    if consumers:
        repos = ", ".join(c["repo_id"] for c in consumers)
        return f"Yes, '{module_name}' is consumed by: {repos}."
    return f"'{module_name}' was not found in the graph."


def _answer_unused_all() -> str:
    unused = find_unused_modules()
    if not unused:
        return "All modules currently have at least one consumer."
    names = ", ".join(u["module_name"] for u in unused)
    return f"The following module(s) have no consumers: {names}."


def _answer_version_drift(module_name: str | None) -> str:
    drift = find_version_drift()
    if module_name:
        drift = [d for d in drift if d["module_name"] == module_name]
        if not drift:
            return f"'{module_name}' is consumed at a consistent version across all repos (or is not found)."
    if not drift:
        return "All modules are consumed at consistent versions across repos."
    lines = []
    for d in drift:
        usage_str = "; ".join(f"{u['repo']} on {u['version']}" for u in d["usages"])
        lines.append(f"{d['module_name']}: {usage_str}")
    return "Version inconsistencies found - " + " | ".join(lines)


def ask_graph(question: str) -> dict:
    extracted = _extract_intent(question)
    intent = extracted.get("intent")
    module_name = extracted.get("module_name")

    answer = None
    if intent == "blast_radius" and module_name:
        answer = _answer_blast_radius(module_name)
    elif intent == "unused" and module_name:
        answer = _answer_unused_specific(module_name)
    elif intent == "unused_all":
        answer = _answer_unused_all()
    elif intent == "version_drift":
        answer = _answer_version_drift(module_name)

    if answer:
        return {
            "question": question,
            "answer": answer,
            "generated_cypher": "[deterministic - intent-based lookup, no LLM Cypher used]",
            "raw_context": None,
        }

    from src.graph.qa_chain_llm_fallback import ask_graph_llm
    return ask_graph_llm(question)