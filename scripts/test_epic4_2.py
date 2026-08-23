"""
Epic 4.2 validation: GraphCypherQAChain answers grounded in the graph.

Run: python -m scripts.test_epic4_2
"""
from src.graph.qa_chain import ask_graph


QUESTIONS = [
    "Is vpc-base used consistently across all service repos, or are any behind?",
    "What's the blast radius if I change security-group-web?",
    "Is the sqs-queue module still in use anywhere?",
    "Which modules have no consumers?",
]


def main():
    for q in QUESTIONS:
        print(f"\n=== Q: {q} ===")
        result = ask_graph(q)
        print(f"Generated Cypher: {result['generated_cypher']}")
        print(f"Answer: {result['answer']}")

    print("\nManual review: check each answer against GROUND_TRUTH.md for correctness.")


if __name__ == "__main__":
    main()