"""
Epic 2 validation: parses all repos under data/github-repos and checks
output against eval/ground_truth.md expectations.

Run: python scripts/test_epic2.py
"""
from pathlib import Path

from src.parsing.terraform.hcl_parser import parse_repo
from src.parsing.terraform.git_metadata import get_repo_summary

DATA_DIR = Path("data/github-repos")  # adjust if you renamed this folder


def main():
    all_parsed = {}
    for repo_path in sorted(p for p in DATA_DIR.iterdir() if p.is_dir()):
        print(f"\n=== Parsing {repo_path.name} ===")
        parsed = parse_repo(repo_path)
        all_parsed[repo_path.name] = parsed

        print(f"  entities: {len(parsed.entities)}, edges: {len(parsed.edges)}")
        for e in parsed.entities:
            print(f"    [{e.type}] {e.name}  {e.properties}")
        for edge in parsed.edges:
            print(f"    ({edge.source_id}) -{edge.type}-> ({edge.target_id})  {edge.properties}")

        try:
            summary = get_repo_summary(repo_path)
            print(f"  git: {summary['total_commits']} commits, tags={summary['tags']}")
        except Exception as e:
            print(f"  [warn] git metadata failed: {e}")

    # --- checks against GROUND_TRUTH.md ---
    print("\n=== Ground truth checks ===")
    modules = [e for e in all_parsed["infra-modules"].entities if e.type == "module_def"]
    assert len(modules) == 8, f"expected 8 modules, got {len(modules)}"
    print(f"  [PASS] module count == 8")

    consumer_repos = [r for r in all_parsed if r != "infra-modules"]
    assert len(consumer_repos) == 3, f"expected 3 consumer repos, got {len(consumer_repos)}"
    print(f"  [PASS] consumer repo count == 3")

    total_consumes_edges = sum(
        len([ed for ed in p.edges if ed.type == "consumes"])
        for name, p in all_parsed.items() if name != "infra-modules"
    )
    assert total_consumes_edges == 10, f"expected 10 consumes edges, got {total_consumes_edges}"
    print(f"  [PASS] total consumes edges == 10")

    billing_vpc = next(
        ed for ed in all_parsed["service-billing"].edges
        if ed.properties.get("call_name") == '"vpc"'
    )
    assert billing_vpc.properties["version"] == "v1.0.0", "expected billing on vpc-base v1.0.0"
    print(f"  [PASS] service-billing pinned to vpc-base v1.0.0 (drift confirmed)")

    print("\nAll Epic 2 checks passed.")


if __name__ == "__main__":
    main()