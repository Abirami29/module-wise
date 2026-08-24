"""
Epic 4 validation: duplicate detection, structural drift, narrative alignment.

Run: python -m scripts.test_epic4
"""
from pathlib import Path

from src.graph.enrichment import (
    check_duplicate_capability,
    check_structural_drift,
    check_narrative_alignment,
)

INTERNAL_DOCS_DIR = Path("data/internal-docs")


def main():
    print("=== 4.1a: Duplicate capability detection ===")
    result = check_duplicate_capability(
        "s3-bucket-standard", "s3-bucket-logging",
        resources_a=["aws_s3_bucket", "aws_s3_bucket_versioning", "aws_s3_bucket_server_side_encryption_configuration"],
        resources_b=["aws_s3_bucket", "aws_s3_bucket_versioning", "aws_s3_bucket_server_side_encryption_configuration", "aws_s3_bucket_lifecycle_configuration"],
    )
    print(f"  {result}")
    assert result["similar"] is True, f"expected duplicate flagged as similar, got {result}"
    print("  [PASS] s3-bucket-standard <-> s3-bucket-logging flagged as similar")

    print("\n=== 4.1b (structural): Stale comment detection ===")
    findings = check_structural_drift(
        "s3-bucket-standard",
        resource_types=["aws_s3_bucket", "aws_s3_bucket_versioning", "aws_s3_bucket_server_side_encryption_configuration"],
    )
    print(f"  {findings}")
    assert len(findings) >= 1, "expected at least one structural drift finding"
    print("  [PASS] stale encryption comment flagged")

    print("\n=== 4.1b (narrative): vpc-base alignment check (should be CONSISTENT) ===")
    internal_doc_text = (INTERNAL_DOCS_DIR / "vpc-flow-logs-decision.md").read_text()
    result = check_narrative_alignment("vpc-base", internal_doc_text=internal_doc_text)
    print(f"  {result}")
    assert result["consistent"] is True, f"expected vpc-base sources to be consistent, got {result}"
    print("  [PASS] vpc-base README/doc/comment correctly found consistent (negative test case)")

    print("\nAll Epic 4 checks passed.")


if __name__ == "__main__":
    main()