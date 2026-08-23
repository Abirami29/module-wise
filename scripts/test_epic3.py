"""
Epic 3 validation: builds the graph, then checks deterministic queries
against eval/ground_truth.md expectations.

Run: python -m scripts.test_epic3
"""
from src.graph.build_graph import build_full_graph
from src.graph.queries import find_unused_modules, find_version_drift, find_consumers_of


def main():
    print("=== Building graph ===")
    build_full_graph(clear_first=True)

    print("\n=== Unused modules ===")
    unused = find_unused_modules()
    for u in unused:
        print(f"  {u['module_name']}")
    assert len(unused) == 1, f"expected 1 unused module, got {len(unused)}: {unused}"
    assert unused[0]["module_name"] == "sqs-queue", f"expected sqs-queue, got {unused[0]['module_name']}"
    print("  [PASS] sqs-queue correctly flagged as unused")

    print("\n=== Version drift ===")
    drift = find_version_drift()
    for d in drift:
        print(f"  {d['module_name']}: versions={d['versions']}")
        for u in d["usages"]:
            print(f"    {u['repo']} -> {u['version']}")
    assert len(drift) == 1, f"expected 1 drifted module, got {len(drift)}: {drift}"
    assert drift[0]["module_name"] == "vpc-base", f"expected vpc-base, got {drift[0]['module_name']}"
    assert set(drift[0]["versions"]) == {"v1.0.0", "v2.0.0"}
    print("  [PASS] vpc-base correctly flagged as drifted (v1.0.0 vs v2.0.0)")

    print("\n=== Blast radius: security-group-web ===")
    consumers = find_consumers_of("security-group-web")
    for c in consumers:
        print(f"  {c['repo_id']} @ {c['version']}")
    assert len(consumers) == 2, f"expected 2 consumers, got {len(consumers)}"
    print("  [PASS] security-group-web consumed by 2 repos (webshop, billing)")

    print("\nAll Epic 3 checks passed.")


if __name__ == "__main__":
    main()