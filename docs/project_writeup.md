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
shape: a Neo4j knowledge graph (via GraphCypherQAChain, LangChain +
LangGraph) for structural/relational questions, and a vector store (Qdrant +
Nebius embeddings) for semantic "is there a module for X" questions. A
LangGraph router classifies each incoming question and picks the right path
automatically, with fallback to the other path if the first attempt returns
a weak or empty result.

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
and stronger faithfulness (the graph query returns a fact, not an
LLM-synthesized guess). Semantic questions ("is there a module for X")
remain better served by vector search, which is why this system routes
between graph and vector retrieval per question rather than treating one as
universally superior.

## Datasets Used
Synthetic but structurally realistic data, self-authored - no real company
data used. The project intentionally avoids any details specific to a real
employer's architecture; the "central modules repo consumed by service
repos" pattern is a widely-documented, industry-standard Terraform practice
(recommended in HashiCorp's own docs), not a proprietary structure.

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
  - A stale inline comment contradicting the actual code (claims encryption
    is disabled; the module provisions SSE encryption)
  - A narrative-alignment control case (vpc-base's README, internal doc,
    and inline comment all consistently describe the same SOC2 compliance
    driver - used to confirm the system doesn't flag agreement as drift)

## Architecture / Tooling

| Layer | Choice | Why |
|---|---|---|
| Parsing | python-hcl2 + GitPython | Extracts structured Entity/Edge data via a generic intermediate representation, kept parser-agnostic so future sources (dbt, Helm, etc.) can plug into the same downstream graph/query code |
| Graph store | Neo4j AuraDB (free tier) | Hosted, persists independent of app runtime, standard property-graph model |
| Vector store | Qdrant Cloud (free tier) | Chosen over Pinecone despite Pinecone's broader name recognition: Qdrant is open-source and self-hostable, matching the project's goals of production flexibility and open-source distributability. Pinecone is managed-only and would force a vendor account on anyone running this project. LangChain's VectorStore abstraction keeps this swappable if a future deployment favors managed convenience. |
| LLM (chat) | Nebius Token Factory - deepseek-ai/DeepSeek-V4-Flash | OpenAI-compatible endpoint, general-purpose text model suited to structured JSON extraction and comparison tasks; selected over a specialized multimodal model (Nemotron-3-Nano-Omni) which is optimized for image/audio perception, not text reasoning |
| Embeddings | Nebius Token Factory - Qwen/Qwen3-Embedding-8B | Available embedding model on the account's plan; corpus is small enough that embedding model choice has limited practical impact |
| Orchestration | LangChain + LangGraph | Matches the course's named Track 2; LangGraph's state-machine model is used deliberately for the routing logic (classify -> retrieve -> fallback), not just included nominally |
| UI | Streamlit | Chat-native components (st.chat_message, st.chat_input) for a conversational interface per the project's "vibe-coded chatbot" bonus criteria |
| Chunking strategy | Whole-document (one chunk per README/doc) | Module documentation is short (150-300 tokens) and self-contained by convention; splitting would fragment rather than improve retrieval. Chunk size was matched to actual document size rather than applying a default splitter. |

## Prompts / Agent Instructions
Key prompt templates used (full text in `src/graph/enrichment.py`,
`src/graph/qa_chain.py`, `src/vector/qa_chain.py`,
`src/router/langgraph_router.py`):

- **DUPLICATE_PROMPT** - compares two module READMEs + resource types,
  judges shared purpose, returns structured JSON with confidence and a
  one-sentence (20-word max) reasoning string
- **STRUCTURAL_CLAIM_PROMPT** - extracts checkable factual claims from an
  inline code comment (e.g. "encryption disabled"), for code-grounded
  verification against parsed HCL facts
- **NARRATIVE_COMPARE_PROMPT** - compares README, internal doc, and inline
  comment for a module, explicitly instructed to surface disagreement
  without adjudicating which source is "correct" (no ground truth exists
  for narrative claims, only for structural ones)
- **CUSTOM_CYPHER_PROMPT** - translates English questions into Cypher,
  constrained to the actual graph schema, with an explicit fallback
  instruction for genuinely unanswerable questions and a worked example
  for multi-repo comparison queries
- **CUSTOM_QA_PROMPT** - synthesizes a final answer from Cypher query
  results, explicitly instructed to trust retrieved data and never claim
  inability to answer when data is present
- **CLASSIFY_PROMPT** (router) - classifies a question as "structural"
  (routes to graph) or "semantic" (routes to vector)

All prompts include explicit "always respond in English" instructions
after an early bug where vague questions occasionally produced non-English
output.

## Design Decision: Where LLM Judgment Is Trusted vs. Only Surfaced
A deliberate distinction runs through the enrichment layer:
- **Deterministic facts** (orphaned modules, version drift) are answered by
  direct Cypher queries with zero LLM involvement - the LLM never decides
  these, only narrates results already computed by code.
- **Structural drift claims** (e.g. a comment claiming encryption is
  disabled) are LLM-extracted but code-verified against parsed HCL facts -
  the LLM extracts a claim, code checks it against ground truth.
- **Narrative differences** across documentation sources are surfaced for
  human review without an automated verdict, since no ground truth exists
  to adjudicate prose framing differences.

This tiered-trust model is applied consistently and is the intended answer
to "why not just use Copilot/an IDE assistant for this" - a per-file coding
assistant has no persistent, cross-repo structure to reason over and no
standing distinction between grounded fact and surfaced-but-unverified
claim; it only answers what a user happens to think to ask, in the file
they happen to have open.

## Iterations & Debugging
- **Empty LLM responses**: initial calls returned empty content with
  finish_reason="length" - the model was exhausting its output token
  budget on internal reasoning before writing the answer. Fixed by
  increasing max_tokens and setting reasoning_effort="low" via extra_body
  for tasks that don't need deep reasoning.
- **Repetition loops**: at temperature=0.0, the model occasionally entered
  degenerate repetition loops rather than completing a coherent answer.
  Fixed via frequency_penalty=0.4 plus explicit word-limit constraints in
  prompts.
- **Answer-synthesis hedging**: GraphCypherQAChain's default QA prompt led
  the model to say "I cannot determine" even when correct data was present
  in context. Fixed with a custom qa_prompt explicitly instructing the
  model to trust retrieved data.
- **Cypher hallucination**: on questions outside the graph's actual schema,
  the model invented plausible-but-fake boolean properties rather than
  admitting the schema couldn't answer the question. Fixed with a custom
  cypher_prompt giving explicit schema-grounding instructions and a defined
  fallback query for genuinely unanswerable questions.
- **Over-correction**: the schema-grounding fix initially made the model
  too conservative, bailing out on questions it could actually answer.
  Fixed by adding a worked Cypher example for the multi-repo comparison
  pattern directly in the prompt.
- **Non-English output**: on vague/open-ended questions, the model
  occasionally responded in Chinese. Fixed by adding explicit
  "always respond in English" instructions to all prompts.
- **Comment-extraction regex bug**: an overly greedy regex (re.DOTALL
  applied too broadly) caused inline comment extraction to swallow the
  entire resource block below the comment, not just the comment text.
  Fixed by scoping DOTALL only to the block-comment branch.
- **Nested git repository handling**: sample repos were given their own
  git histories (for realistic commit metadata) nested inside the main
  project repo, which caused git to silently treat them as embedded
  repos/gitlinks rather than tracking their file contents. Fixed via a
  .gitignore rule excluding only the nested .git directories while
  tracking the actual file content normally.

## Known Limitations & Findings (Epic 7 Evaluation)
During the 10-question comparison eval, several real limitations surfaced.
Rather than chase every one to a fully clean result (a diminishing-returns
exercise given inherent LLM nondeterminism), these are documented as honest
findings about the current state of LLM-generated Cypher for relational RAG.

**Finding 1: Retrieval can succeed while synthesis fails.** On the
version-consistency question, Cypher generation correctly retrieved all
three repos and their versions - but answer-synthesis failed to connect the
returned data back to the question's subject, incorrectly claiming "no
reference to vpc-base." This shows correctness at the retrieval layer
doesn't guarantee correctness at the synthesis layer; they are separate LLM
calls with independent failure modes.

**Finding 2: LLM-generated Cypher is not fully reproducible.** Identical
questions, run moments apart at temperature=0.0, produced different
generated Cypher and different results on at least two questions. This is a
known characteristic of MoE/batched LLM inference, not a codebase bug - but
it is a material limitation for any system generating database queries via
LLM.

**Finding 3: Not all questions about graph data are graph-shaped.** Asking
the graph "are there modules that do almost the same thing" failed, because
duplicate-capability judgments are LLM-derived findings (Epic 4.1a), not
facts stored in the graph itself. This reinforces the project's core
thesis: retrieval mechanism must match not just question topic but where
the relevant fact actually lives (structured graph vs. LLM-derived insight
vs. document prose).

**Finding 4: Router fallback provided real, measurable value.** On multiple
questions where the graph-only path failed outright (a Cypher syntax
error, a malformed multi-line query), the router successfully recovered a
correct answer via the vector fallback path - direct evidence the fallback
logic measurably improved answer availability during actual testing, not
just in theory.

**Conclusion**: further prompt iteration showed diminishing returns - each
fix for one question's failure mode either didn't generalize or introduced
a new failure mode elsewhere. This is treated as a legitimate finding about
current LLM-generated-Cypher reliability rather than an unfinished feature:
the system's fallback design (route to vector when graph fails or returns a
weak result) is the correct mitigation, not further prompt engineering,
which appears to have reached diminishing returns for this model/task
combination within this project's scope.

## Learnings / Observations
- Deterministic graph queries (orphan detection, version drift lookups) are
  100% reliable and faithful by construction - the LLM's only role is
  translating English to Cypher and narrating results, never inventing
  facts. This is meaningfully more trustworthy than any purely
  LLM-generated content.
- Forcing the wrong retrieval mechanism onto a question doesn't just
  produce a worse answer - it can produce confidently wrong output (the
  Cypher hallucination bug, where the model invented a nonexistent
  boolean property, is the clearest example).
- GraphRAG and vector RAG are not "one is better than the other" - they
  solve genuinely different question shapes. Structural/relational
  questions need graph traversal; "does something like X exist" questions
  need semantic similarity. The router's job is matching mechanism to
  question shape, not picking an overall winner.
- Vector search proved more *consistent* run-to-run than LLM-generated
  Cypher, even in cases where a correct graph query would have given a
  more precise answer when it worked. Reliability and precision are
  different axes, and this project's fallback design treats reliability as
  the more important guarantee for a production-facing tool.

## Future Work
- Extend the parsing layer (already format-agnostic via a shared
  Entity/Edge intermediate representation) to non-Terraform sources, e.g.
  dbt model lineage - applying the same graph pattern to data contracts
  and ingestion-as-a-service questions. Infra provisioning (Terraform
  modules) and data contracts/lineage are typically tracked in separate
  tooling; a unified graph spanning both is a genuine, underbuilt gap.
- Naming-convention consistency checking: deterministic style linting via
  structured queries (already-parsed data, no LLM needed), plus
  LLM-based detection of misleading/confusing names across modules using
  the same grounded-flagging pattern as documentation drift detection.
- Production ingestion: webhook-triggered pipeline (vs. the current
  on-demand "Rebuild Graph" button) so the graph stays current
  automatically as repos change. The ingestion logic itself is already
  production-shaped; only the trigger mechanism would change.
- Real Confluence/Wiki integration via REST API or native per-page
  Markdown export, feeding into the same chunking/embedding pipeline
  already used for READMEs - the ingestion layer is source-agnostic past
  an initial text-normalization step.
- A fully self-hosted deployment path (local embedding model via
  sentence-transformers instead of a hosted API, self-hosted Qdrant and
  Neo4j) for a zero-external-dependency, clone-and-run open-source version.
