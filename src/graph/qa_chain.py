"""
Natural-language Q&A over the Neo4j graph via GraphCypherQAChain.
LLM translates a question into Cypher, runs it, and generates an answer
grounded in the actual query result - not free-form generation.
"""
import os

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


def ask_graph(question: str, max_retries: int = 2) -> dict:
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