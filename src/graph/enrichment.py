"""
LLM-enriched graph analysis:
  4.1a - duplicate capability detection (module vs module)
  4.1b - documentation drift detection:
           structural sub-check: comment claim vs parsed HCL facts (code-grounded)
           narrative sub-check: README vs internal doc vs comment (surfaced, no verdict)
"""
import json
from pathlib import Path

from src.llm.nebius_client import get_llm
from src.parsing.terraform.comment_extractor import extract_comments_for_module

MODULES_DIR = Path("data/github-repos/infra-modules/modules")
INTERNAL_DOCS_DIR = Path("data/internal-docs")

# --- 4.1a: Duplicate capability detection ---

DUPLICATE_PROMPT = """You are comparing two Terraform modules to judge if they serve a similar purpose.

Module A: {name_a}
Description: {desc_a}
Resource types: {resources_a}

Module B: {name_b}
Description: {desc_b}
Resource types: {resources_b}

Do these modules serve a substantially similar purpose (i.e. a team building
a new service might reasonably use either one, or might not know both exist)?

Respond ONLY with valid JSON, no other text. The "reasoning" field must be
ONE sentence, maximum 20 words:
{{"similar": true/false, "confidence": "low/medium/high", "reasoning": "one short sentence, max 20 words"}}
"""


def read_readme(module_name: str) -> str:
    readme_path = MODULES_DIR / module_name / "README.md"
    return readme_path.read_text() if readme_path.exists() else ""


def check_duplicate_capability(module_a: str, module_b: str, resources_a: list[str], resources_b: list[str]) -> dict:
    llm = get_llm(max_tokens=1024, frequency_penalty=0.4)
    prompt = DUPLICATE_PROMPT.format(
        name_a=module_a, desc_a=read_readme(module_a)[:500], resources_a=resources_a,
        name_b=module_b, desc_b=read_readme(module_b)[:500], resources_b=resources_b,
    )
    response = llm.invoke(prompt)


    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {"similar": None, "confidence": "low", "reasoning": f"parse error: {response.content[:200]}"}

# --- 4.1b: Documentation drift detection ---

STRUCTURAL_CLAIM_PROMPT = """Extract any factual claims about infrastructure configuration from this comment.
Focus on claims that could be checked against code (e.g. "encryption disabled",
"versioning enabled", "publicly accessible").

Comment: {comment}

Respond ONLY with valid JSON, no other text:
{{"claims": [{{"topic": "short topic name", "claim": "what it asserts"}}]}}
If no checkable claims, return {{"claims": []}}.
"""


def extract_structural_claims(comment: str) -> list[dict]:
    llm = get_llm()
    response = llm.invoke(STRUCTURAL_CLAIM_PROMPT.format(comment=comment))
    try:
        return json.loads(response.content).get("claims", [])
    except json.JSONDecodeError:
        return []


def check_structural_drift(module_name: str, resource_types: list[str]) -> list[dict]:
    """
    Code-grounded check: extract claims from comments via LLM, then verify
    each claim against parsed HCL facts (resource_types) using plain code -
    the LLM never decides right/wrong, only extracts the claim.
    """
    comments = extract_comments_for_module(MODULES_DIR / module_name)
    findings = []

    for comment in comments:
        claims = extract_structural_claims(comment)
        for claim in claims:
            topic = claim["topic"].lower()
            claim_text = claim["claim"].lower()

            # Grounded check: encryption claims vs actual SSE resource presence
            if "encrypt" in topic or "encrypt" in claim_text:
                has_sse_resource = any(
                    "server_side_encryption" in rt for rt in resource_types
                )
                claims_disabled = "disable" in claim_text or "not enable" in claim_text or "no encrypt" in claim_text

                if claims_disabled and has_sse_resource:
                    findings.append({
                        "module": module_name,
                        "type": "structural_drift",
                        "comment": comment,
                        "claim": claim["claim"],
                        "fact": f"module currently provisions {[rt for rt in resource_types if 'server_side_encryption' in rt]}",
                        "confidence": "moderate",
                        "note": "Comment claims encryption is disabled, but a server-side encryption "
                                 "resource is present in the current module. Comment may be stale.",
                    })

    return findings


NARRATIVE_COMPARE_PROMPT = """Compare these descriptions of the same infrastructure module from
different documentation sources. Do NOT judge which is correct - only note
whether they are consistent or whether they emphasize/claim different things.

README: {readme}

Internal doc: {internal_doc}

Inline comment: {comment}

Respond ONLY with valid JSON, no other text:
{{"consistent": true/false, "summary": "one sentence describing alignment or divergence"}}
"""


# def check_narrative_alignment(module_name: str, internal_doc_text: str = "") -> dict:
#     readme = read_readme(module_name)
#     comments = extract_comments_for_module(MODULES_DIR / module_name)
#     comment_text = " ".join(comments) if comments else "(none)"
#
#     if not readme and not internal_doc_text and not comments:
#         return {"consistent": None, "summary": "no sources available to compare"}
#
#     llm = get_llm()
#     prompt = NARRATIVE_COMPARE_PROMPT.format(
#         readme=readme[:800] or "(none)",
#         internal_doc=internal_doc_text[:800] or "(none)",
#         comment=comment_text[:500],
#     )
#     response = llm.invoke(prompt)
#     try:
#         return json.loads(response.content)
#     except json.JSONDecodeError:
#         return {"consistent": None, "summary": f"parse error: {response.content[:200]}"}

def check_narrative_alignment(module_name: str, internal_doc_text: str = "") -> dict:
    readme = read_readme(module_name)
    comments = extract_comments_for_module(MODULES_DIR / module_name)
    comment_text = " ".join(comments) if comments else "(none)"

    if not readme and not internal_doc_text and not comments:
        return {"consistent": None, "summary": "no sources available to compare"}

    llm = get_llm()
    prompt = NARRATIVE_COMPARE_PROMPT.format(
        readme=readme[:800] or "(none)",
        internal_doc=internal_doc_text[:800] or "(none)",
        comment=comment_text[:500],
    )
    response = llm.invoke(prompt)

    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {"consistent": None, "summary": f"parse error: {response.content[:200]}"}