# Module-Wise: GraphRAG for Terraform Module Dependencies

## Project Overview
Module-Wise is a GraphRAG application that answers infrastructure-relationship
questions about a shared Terraform modules repo consumed by multiple service
repos - questions like "what's the blast radius if I change this module,"
"is this module still used anywhere," and "are any repos behind on version."
These are relational/structural questions that plain vector search (or
existing Terraform tooling like `terraform graph`) can't answer well, since
the answer depends on multi-hop relationships across repos, not semantic
similarity to a query.

The system routes between two retrieval mechanisms depending on question
shape: a Neo4j knowledge graph for structural/relational questions, and a
vector store (Qdrant + Nebius embeddings) for semantic "is there a module
for X" questions. A LangGraph router classifies each incoming question and
picks the right path automatically, with fallback to the other path if the
first attempt returns a weak or empty result.

## One-liner
My RAG app helps platform/infra engineers answer module usage, staleness,
duplication, and blast-radius questions from a shared Terraform modules repo
consumed by multiple service repos, in a Streamlit chat, with high
faithfulness and a clear "no existing module covers this" fallback.

## Why GraphRAG (justification)
This project's core use case - module usage, staleness, blast radius, and
duplication across a shared Terraform modules repo - is fundamentally
relational: the answers depend on structural facts (consumption edges,
version pins, orphan status) and multi-hop connections between modules and
consumers, not on semantic similarity to a query. Vector retrieval can find
text that *resembles* a question, but has no mechanism for traversing
relationships, so it cannot answer "what's the blast radius of X" or "who's
behind on which version." GraphRAG represents these facts natively as nodes
and edges, enabling direct, deterministic traversal for structural questions
and stronger faithfulness. Semantic questions ("is there a module for X")
remain better served by vector search, which is why this system routes
between graph and vector retrieval per question rather than treating one as
universally superior.

## Datasets Used
Synthetic but structurally realistic data, self-authored - no real company
data used. The "central modules repo consumed by service repos" pattern is
a widely-documented, industry-standard Terraform practice (recommended in
HashiCorp's own docs), not a proprietary structure.

- 1 shared `infra-modules` repo: 8 Terraform modules (vpc-base,
  s3-bucket-standard, s3-bucket-logging, rds-postgres, security-group-web,
  ecs-service, lambda-function, sqs-queue), each with real .tf files,
  README, and git history (11 commits, 2 version tags)
- 3 consumer repos (service-webshop, service-billing, service-analytics)
  referencing modules via versioned git source URLs
- 2 synthetic "internal docs" simulating Confluence-style decision records
- Deliberately planted inconsistencies for testing:
  - An orphaned module (sqs-queue, zero consumers)
  - Version drift (vpc-base v1.0.0 on service-billing vs. v2.0.0 on
    service-webshop/service-analytics)
  - A near-duplicate module pair (s3-bucket-standard vs. s3-bucket-logging)
  - A stale inline comment contradicting the actual code
  - A narrative-alignment control case (vpc-base's README, internal doc,
    and inline comment all consistently describe the same SOC2 driver)

## Architecture / Tooling

| Layer | Choice | Why |
|---|---|---|
| Parsing | python-hcl2 + GitPython | Extracts structured Entity/Edge data via a generic intermediate representation, kept parser-agnostic for future non-Terraform sources |
| Graph store | Neo4j AuraDB (free tier) | Hosted, persists independent of app runtime |
| Vector store | Qdrant Cloud (free tier) | Chosen over Pinecone: open-source and self-hostable, matching the project's goals of production flexibility and open-source distributability. Pinecone is managed-only and would force a vendor account on anyone running this project. |
| LLM (chat) | Nebius Token Factory - deepseek-ai/DeepSeek-V4-Flash | OpenAI-compatible endpoint |
| Embeddings | Nebius Token Factory - Qwen/Qwen3-Embedding-8B | Available embedding model on the account's plan |
| Orchestration | LangChain + LangGraph | Matches the course's named Track 2; LangGraph's state-machine model handles routing (classify -> retrieve -> fallback) |
| UI | Streamlit | Chat-native components, plus a collapsible repo browser panel |
| Chunking strategy | Whole-document (one chunk per README/doc) | Module documentation is short (150-300 tokens) and self-contained; splitting would fragment rather than improve retrieval |

## Design Decision: Deterministic-First Query Answering
A key architectural decision made late in development, after direct
evidence of LLM-generated-Cypher unreliability (see "Iterations &
Debugging" below): **the graph query path tries a deterministic
pattern-match first, before ever invoking an LLM to generate Cypher.**

Concretely, `ask_graph()` checks the incoming question against a small set
of known question shapes (blast radius / affected repos, unused modules,
version drift/consistency) using simple regex matching. If matched, the
answer is computed via Epic 3's proven, 100%-reliable Cypher queries
(`find_consumers_of`, `find_unused_modules`, `find_version_drift`) with
zero LLM involvement in either the query or the answer. Only questions that
don't match a known pattern fall through to the LLM-generated-Cypher path
(`GraphCypherQAChain`), which remains available for open-ended questions
but is no longer relied on for the system's most common, most important
question types.

This mirrors the same tiered-trust philosophy already used in the Epic 4
enrichment layer (deterministic facts trusted outright; LLM judgments
flagged, never asserted as ground truth) - applied here to retrieval
itself, not just to duplicate/drift detection. It is also a direct,
practical response to Finding 2 below: rather than trying to make
LLM-generated Cypher more reliable through further prompting (which showed
diminishing returns), the system routes around the unreliable component
entirely for the question shapes that matter most, and keeps it only as a
fallback for novelty.

## Design Decision: Where LLM Judgment Is Trusted vs. Only Surfaced
- **Deterministic facts** (orphaned modules, version drift, blast radius)
  are answered by direct Cypher queries with zero LLM involvement in the
  common path - the LLM is only invoked for questions outside the known
  patterns, and even then never invents facts, only translates/narrates.
- **Structural drift claims** (e.g. a comment claiming encryption is
  disabled) are LLM-extracted but code-verified against parsed HCL facts.
- **Narrative differences** across documentation sources are surfaced for
  human review without an automated verdict, since no ground truth exists
  to adjudicate prose framing differences.
- **Vector-retrieved documentation** is passed through an LLM synthesis
  step (not shown to the user as raw retrieved snippets) so answers are
  focused on the question asked rather than requiring the user to parse
  multiple loosely-related retrieved chunks themselves.

This tiered-trust model is the intended answer to "why not just use
Copilot/an IDE assistant for this" - a per-file coding assistant has no
persistent, cross-repo structure to reason over and no standing
distinction between grounded fact and surfaced-but-unverified claim.

## Prompts / Agent Instructions
Key prompt templates (full text in `src/graph/enrichment.py`,
`src/graph/qa_chain.py`, `src/vector/qa_chain.py`,
`src/router/langgraph_router.py`): DUPLICATE_PROMPT, STRUCTURAL_CLAIM_PROMPT,
NARRATIVE_COMPARE_PROMPT (4.1 enrichment), CUSTOM_CYPHER_PROMPT,
CUSTOM_QA_PROMPT (LLM-fallback graph path), VECTOR_QA_PROMPT (vector
synthesis), CLASSIFY_PROMPT (router). All include explicit "always respond
in English" instructions after an early bug where vague questions
occasionally produced non-English output.

## Iterations & Debugging
- **Empty LLM responses**: initial calls returned empty content with
  finish_reason="length" - the model was exhausting its output token
  budget on internal reasoning before writing the answer. Fixed by
  increasing max_tokens and setting reasoning_effort="low".
- **Repetition loops**: at temperature=0.0, the model occasionally entered
  degenerate repetition loops. Fixed via frequency_penalty=0.4 plus
  explicit word-limit constraints in prompts.
- **Answer-synthesis hedging**: the default QA prompt led the model to say
  "I cannot determine" even when correct data was present in context.
  Fixed with a custom qa_prompt explicitly instructing the model to trust
  retrieved data.
- **Cypher hallucination**: on questions outside the graph's actual schema,
  the model invented plausible-but-fake boolean properties rather than
  admitting the schema couldn't answer the question. Fixed with a custom
  cypher_prompt giving explicit schema-grounding instructions.
- **Over-correction**: the schema-grounding fix initially made the model
  too conservative, bailing out on questions it could actually answer.
  Fixed by adding a worked Cypher example to the prompt.
- **Non-English output**: on vague/open-ended questions, the model
  occasionally responded in Chinese. Fixed by adding explicit
  "always respond in English" instructions to all prompts.
- **Comment-extraction regex bug**: an overly greedy regex (re.DOTALL
  applied too broadly) caused inline comment extraction to swallow the
  entire resource block below the comment. Fixed by scoping DOTALL only
  to the block-comment branch.
- **Nested git repository handling**: sample repos were given their own
  git histories nested inside the main project repo, which caused git to
  silently treat them as embedded repos/gitlinks. Fixed via a .gitignore
  rule excluding only the nested .git directories.
- **Vector path bypassing LLM synthesis**: the router's vector-search path
  was initially displaying raw retrieved document snippets directly to the
  user rather than passing them through an LLM synthesis step, causing
  loosely-relevant results (e.g. an ECS module showing up alongside a
  Lambda-specific question) to appear verbatim in the chat. Fixed by
  routing the vector path through the same LLM-synthesis function
  (`ask_vector`) already built and validated for the Epic 7 comparison
  eval, rather than formatting raw snippets directly.
- **LLM-generated-Cypher reliability, resolved architecturally rather than
  through further prompting**: after repeated observation that the same
  question could produce correct, incorrect, or stalled results across
  separate runs at temperature=0.0 (see Finding 2), further prompt
  iteration showed diminishing and sometimes counter-productive returns
  (a fix for one failure mode occasionally introduced a different one
  elsewhere). The system was changed to try a deterministic, LLM-free
  pattern-match against known question shapes first, falling back to
  LLM-generated Cypher only for questions outside that known set. This
  eliminated the reliability problem entirely for the system's core,
  most-used question types, rather than continuing to chase reliability
  through prompt engineering alone.

## Known Limitations & Findings (Epic 7 Evaluation)
During the 10-question comparison eval (before the deterministic-first
fix described above), several real limitations surfaced:

**Finding 1: Retrieval can succeed while synthesis fails.** Cypher
generation correctly retrieved data, but answer-synthesis sometimes failed
to connect the returned data back to the question's subject.

**Finding 2: LLM-generated Cypher is not fully reproducible.** Identical
questions, run moments apart at temperature=0.0, produced different
generated Cypher and different results across separate runs - a known
characteristic of MoE/batched LLM inference, not a codebase bug. This
finding directly motivated the deterministic-first architecture described
above.

**Finding 3: Not all questions about graph data are graph-shaped.** Asking
the graph "are there modules that do almost the same thing" failed, because
duplicate-capability judgments are LLM-derived findings (Epic 4.1a), not
facts stored in the graph itself.

**Finding 4: Router fallback provided real, measurable value.** On multiple
questions where the graph-only LLM path failed outright, the router
successfully recovered a correct answer via the vector fallback path.

Full question-by-question analysis: see `docs/comparison_report.md`.

## Learnings / Observations
- Deterministic graph queries are 100% reliable and faithful by
  construction. This project's most important architectural lesson was
  learning *when* to rely on this guarantee versus LLM generation: rather
  than treating "ask an LLM to write a database query" as the default for
  all structured questions, the strongest design uses deterministic code
  wherever the question shape is known in advance, and reserves LLM
  generation for genuine novelty.
- Forcing the wrong retrieval mechanism onto a question doesn't just
  produce a worse answer - it can produce confidently wrong output.
- GraphRAG and vector RAG solve genuinely different question shapes. The
  router's job is matching mechanism to question shape, not picking an
  overall winner.
- Displaying raw retrieved content is not the same as answering a
  question - even in a system explicitly built around retrieval, a
  synthesis step matters for actually answering what was asked rather
  than showing everything that was found.

## Future Work
- Extend the deterministic pattern-matching approach with more known
  question shapes (e.g. duplicate-capability lookups reading directly from
  pre-computed Epic 4.1a findings, rather than attempting this via generic
  Cypher or vector retrieval, which Finding 3 showed neither handles well)
- Extend the parsing layer (already format-agnostic) to non-Terraform
  sources, e.g. dbt model lineage
- Naming-convention consistency checking: deterministic style linting plus
  LLM-based detection of misleading/confusing names
- Production ingestion: webhook-triggered pipeline instead of the current
  on-demand "Rebuild Graph" button
- Real Confluence/Wiki integration via REST API or native Markdown export
- Similarity-score-threshold filtering for vector retrieval, rather than a
  fixed top-k, to improve precision as the corpus grows
- A fully self-hosted deployment path (local embedding model, self-hosted
  Qdrant and Neo4j) for a zero-external-dependency, clone-and-run
  open-source version
