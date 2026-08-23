"""
Epic 5 validation: builds the vector store, checks retrieval quality on
semantic-shaped questions.

Run: python -m scripts.test_epic5
"""
from src.vector.build_index import build_vector_store


def main():
    print("=== Building vector store ===")
    store = build_vector_store(clear_first=True)

    print("\n=== Query: 'Is there a module for provisioning an S3 bucket?' ===")
    results = store.similarity_search("provisioning an S3 bucket for storage", k=3)
    for r in results:
        print(f"  [{r.metadata.get('source_type')}] {r.metadata.get('module_name', r.metadata.get('source_path'))}")
        print(f"    {r.page_content[:100]}...")
    module_names = [r.metadata.get("module_name") for r in results]
    assert "s3-bucket-standard" in module_names or "s3-bucket-logging" in module_names, \
        f"expected an S3 module in top results, got {module_names}"
    print("  [PASS] S3 bucket query surfaced a relevant module")

    print("\n=== Query: 'Do we have a module for running containerized services?' ===")
    results = store.similarity_search("running containerized services on Fargate", k=3)
    for r in results:
        print(f"  [{r.metadata.get('source_type')}] {r.metadata.get('module_name', r.metadata.get('source_path'))}")
    module_names = [r.metadata.get("module_name") for r in results]
    assert "ecs-service" in module_names, f"expected ecs-service in top results, got {module_names}"
    print("  [PASS] container/Fargate query surfaced ecs-service")

    print("\n=== Query: 'What module should I use for a Postgres database?' ===")
    results = store.similarity_search("Postgres database module", k=3)
    for r in results:
        print(f"  [{r.metadata.get('source_type')}] {r.metadata.get('module_name', r.metadata.get('source_path'))}")
    module_names = [r.metadata.get("module_name") for r in results]
    assert "rds-postgres" in module_names, f"expected rds-postgres in top results, got {module_names}"
    print("  [PASS] Postgres query surfaced rds-postgres")

    print("\nAll Epic 5 checks passed.")


if __name__ == "__main__":
    main()