"""
Natural-language Q&A over the Neo4j graph via GraphCypherQAChain.
LLM translates a question into Cypher, runs it, and generates an answer
grounded in the actual query result - not free-form generation.
"""
import os
import re

from src.graph.queries import find_unused_modules, find_version_drift, find_consumers_of
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

from src.llm.nebius_client import get_llm

load_dotenv()


CUSTOM_CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""You translate natural language questions into Cypher queries for a
Neo4j graph with this schema:

{schema}

Example - checking version consistency across consumers of the same module:
MATCH (r:Repo)-[c:CONSUMES]->(m:ModuleDef {{name: 'MODULE_NAME'}})
RETURN r.name AS repo, c.version AS version
ORDER BY version
(Do the comparison of versions in the answer, not inside the Cypher - just
return each repo and its version, do not use aggregation functions like max()
inside WHERE or CASE clauses.)

Question: {question}

IMPORTANT: Only generate a query using labels, relationship types, and properties
that actually exist in the schema above. Only use the "cannot answer" fallback
below if the question asks about something with NO relevant nodes/properties in
the schema at all - if relevant data exists (like module names, versions, or
consumption relationships), always attempt a query rather than bailing out.
If genuinely unanswerable, respond with exactly: MATCH (n) WHERE false RETURN n

Generate ONLY the Cypher query, no explanation, no markdown formatting:""",
)


CUSTOM_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You answer questions using ONLY the data provided below. This data
comes directly from a graph database query written specifically to answer the
question below - assume the data is already correctly scoped to the question's
subject, even if the question's exact wording doesn't appear in the data itself.

IMPORTANT: Always respond in English, regardless of the language of the question or data.

Data:
{context}

Question: {question}

Instructions:
- Trust the data completely. It was retrieved specifically to answer this question.
- If the data is a non-empty list, describe what it shows in one or two plain sentences, directly answering the question.
- If the data is an empty list, say plainly that no matching records were found.
- Do NOT comment on your own reasoning process, do NOT say what you were or weren't told to do, and do NOT say a name is "not mentioned" if the data was clearly retrieved for that exact subject.
- Just answer the question directly, in plain language, using the data.

Answer:""",
)


def get_graph_qa_chain() -> GraphCypherQAChain:
    graph = Neo4jGraph(
        url=os.environ["NEO4J_URI"],
        username=os.environ["NEO4J_USERNAME"],
        password=os.environ["NEO4J_PASSWORD"],
    )
    graph.refresh_schema()

    cypher_llm = get_llm(max_tokens=2048, frequency_penalty=0.4)
    qa_llm = get_llm(max_tokens=2048, frequency_penalty=0.4)

    chain = GraphCypherQAChain.from_llm(
        cypher_llm=cypher_llm,
        qa_llm=qa_llm,
        graph=graph,
        qa_prompt=CUSTOM_QA_PROMPT,
        cypher_prompt=CUSTOM_CYPHER_PROMPT,
        verbose=True,
        allow_dangerous_requests=True,
        return_intermediate_steps=True,
        validate_cypher=True,
        top_k=10,
    )
    return chain

def _try_deterministic_match(question: str) -> str | None:
    q = question.lower()

    m = re.search(r"(?:blast radius|affected|impact).*?(?:if|change|changing)\s+([a-z0-9\-]+)", q)
    if not m:
        m = re.search(r"repos? (?:would be |are )?affected.*?(?:if|by)\s+([a-z0-9\-]+)", q)
    if m:
        module_name = m.group(1).strip()
        consumers = find_consumers_of(module_name)
        if not consumers:
            return f"No repos currently consume '{module_name}' (based on graph data)."
        # repos = ", ".join(f"{c['repo_id']} (v{c['version']})" for c in consumers)
        repos = ", ".join(f"{c['repo_id']} ({c['version']})" for c in consumers)
        return f"Changing '{module_name}' would affect: {repos}."

    if "unused" in q or "no consumer" in q or ("used" in q and "anywhere" in q) or "still in use" in q:
        unused = find_unused_modules()
        if not unused:
            return "All modules currently have at least one consumer."
        return f"The following module(s) have no consumers: {', '.join(u['module_name'] for u in unused)}."

    if "consisten" in q or "drift" in q or "behind" in q:
        drift = find_version_drift()
        if not drift:
            return "All modules are consumed at consistent versions across repos."
        lines = [f"{d['module_name']}: " + "; ".join(f"{u['repo']} on {u['version']}" for u in d["usages"]) for d in drift]
        return "Version inconsistencies found - " + " | ".join(lines)

    return None

def ask_graph(question: str, max_retries: int = 2) -> dict:
    deterministic_answer = _try_deterministic_match(question)
    if deterministic_answer:
        return {
            "question": question,
            "answer": deterministic_answer,
            "generated_cypher": "[deterministic - no LLM Cypher used]",
            "raw_context": None,
        }
    return _ask_graph_llm(question, max_retries=max_retries)

def _ask_graph_llm(question: str, max_retries: int = 2) -> dict:
    chain = get_graph_qa_chain()
    for attempt in range(1, max_retries + 1):
        result = chain.invoke({"query": question})
        answer = result["result"]
        if answer and answer.strip():
            return {
                "question": question,
                "answer": answer,
                "generated_cypher": result["intermediate_steps"][0].get("query") if result.get("intermediate_steps") else None,
                "raw_context": result["intermediate_steps"][1].get("context") if len(result.get("intermediate_steps", [])) > 1 else None,
            }
    return {
        "question": question,
        "answer": "[unable to generate an answer after retries]",
        "generated_cypher": None,
        "raw_context": None,
    }