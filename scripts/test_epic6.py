"""
Epic 6 validation: router correctly classifies and answers both question
types, and demonstrates fallback behavior.

Run: python -m scripts.test_epic6
"""
from src.router.langgraph_router import ask

QUESTIONS = [
    # structural - should route to graph
    ("Is vpc-base used consistently across all service repos?", "graph"),
    ("What's the blast radius if I change security-group-web?", "graph"),
    ("Is sqs-queue still in use anywhere?", "graph"),
    # semantic - should route to vector
    ("Is there a module for provisioning an S3 bucket?", "vector"),
    ("Do we have something for running containerized services?", "vector"),
]


def main():
    correct_routing = 0
    for question, expected_path in QUESTIONS:
        print(f"\n=== Q: {question} ===")
        result = ask(question)
        print(f"  Category: {result['category']}")
        print(f"  Path(s) attempted: {result['attempted_paths']}")
        print(f"  Final path used: {result['path_used']}")
        print(f"  Answer: {result['answer'][:300]}")

        if result["path_used"] == expected_path:
            correct_routing += 1
        else:
            print(f"  [NOTE] expected path={expected_path}, got={result['path_used']}")

    print(f"\n{correct_routing}/{len(QUESTIONS)} questions routed to expected path.")
    print("Manual review: check answer quality against GROUND_TRUTH.md.")


if __name__ == "__main__":
    main()