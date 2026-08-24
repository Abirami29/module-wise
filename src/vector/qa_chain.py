"""
Vector-only Q&A: retrieve top-k similar documents, synthesize an answer.
Mirrors ask_graph()'s interface so both paths can be compared fairly in Epic 7.
"""
from src.llm.nebius_client import get_llm, invoke_text
from src.vector.build_index import load_vector_store

VECTOR_QA_PROMPT = """Answer the question using ONLY the retrieved documentation below.
Always respond in English. If the retrieved documents don't actually answer the
question, say so plainly rather than guessing.

Retrieved documentation:
{context}

Question: {question}

Answer in one or two plain sentences:"""


def ask_vector(question: str, k: int = 3) -> dict:
    store = load_vector_store()
    results = store.similarity_search(question, k=k)

    if not results:
        return {
            "question": question,
            "answer": "No relevant documentation found.",
            "retrieved_sources": [],
        }

    context = "\n\n".join(
        f"[{r.metadata.get('module_name', r.metadata.get('source_path'))}]\n{r.page_content[:400]}"
        for r in results
    )

    llm = get_llm(max_tokens=1536, frequency_penalty=0.4)
    # response = llm.invoke(VECTOR_QA_PROMPT.format(context=context, question=question))

    answer = invoke_text(llm, VECTOR_QA_PROMPT.format(context=context, question=question))

    return {
        "question": question,
        "answer": answer,
        "retrieved_sources": [r.metadata.get("module_name", r.metadata.get("source_path")) for r in results],
    }