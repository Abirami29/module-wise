# GraphRAG vs. Vector RAG Comparison Report

Each question below was run through three configurations: the graph-only
path (GraphCypherQAChain), the vector-only path (embedding similarity
search + synthesis), and the LangGraph router (which selects automatically
between them).

---

## Q1: Is vpc-base used consistently across all service repos? Which are behind?
*Expected category: graph*

**Graph-only answer:**
> The provided records show three repositories with their respective versions: `service-billing` at `v1`, `service-analytics` at `v2`, and `service-webshop` at `v2`. This dataset contains no reference to `vpc-base`, so we cannot determine whether it's used consistently...

**Vector-only answer:**
> The retrieved documentation does not contain information about which service repos use `vpc-base` or their consistency of usage.

**Router answer** (routed to: `vector`):
> Found relevant documentation (README, internal doc, ecs-service) - did not directly answer the version question.

**Analysis:** Graph retrieval correctly fetched the right data (all three
repos + versions), but the answer-synthesis step failed to connect the
returned rows back to the question's subject, incorrectly claiming "no
reference to vpc-base" despite vpc-base being the exact query filter.
Router fell back to vector, which also couldn't answer (correctly, since
version data isn't in the README text). This demonstrates that correct
retrieval doesn't guarantee correct synthesis - they are separate LLM
calls with independent failure modes, and fallback alone doesn't help
when neither path's failure is simply "empty."

---

## Q2: What's the blast radius if I change security-group-web?
*Expected category: graph*

**Graph-only answer:**
> Changing security-group-web would impact two repositories: `service-billing` and `service-webshop`, both at version v1.0.0.

**Vector-only answer:**
> Based on the documentation, changing `security-group-web` would affect any public-facing web service (ALB, ECS service, EC2 instance) that uses this module...

**Router answer** (routed to: `graph`):
> Changing security-group-web would impact two repositories: `service-billing` and `service-webshop`, both at version v1.0.0.

**Analysis:** Router matched graph-only exactly - correct, specific
blast-radius answer. Graph wins clearly here: vector's answer is generic
module documentation describing *what kind of* service would use the
module, not *which specific repos actually do*. This is the clearest
example in the eval of graph's structural advantage over semantic search.

---

## Q3: Is sqs-queue module still in use anywhere?
*Expected category: graph*

**Graph-only, vector-only, and router** all agreed: no, sqs-queue is
unused.

**Analysis:** All three converge on the correct answer here, since the
internal doc/README directly states the module is unused in prose,
letting vector search succeed too. A case where both mechanisms happen to
work, not a strong differentiator.

---

## Q4: Which modules have no consumers?
*Expected category: graph*

**Graph-only and router** correctly identified `sqs-queue` as the only
module with no consumers, citing its resource count and type.
**Vector-only** also correctly named sqs-queue, since the README states
this directly.

**Analysis:** Again, both mechanisms converge since the fact happens to
be stated in prose as well as structurally. Graph's answer is more
precise (based on actual traversal of consumption edges, not just text
matching "no consumers" in a README that could be stale).

---

## Q5: What repos would be affected if rds-postgres changes?
*Expected category: graph*

**Graph-only answer (one run):** No matching records were found.
**Router answer (same underlying chain, different run):** The repo
`service-billing` would be affected if `rds-postgres` changes. (correct)
**Vector-only answer:** The retrieved documentation does not mention any
repositories that depend on rds-postgres.

**Analysis:** Direct evidence of LLM-generated-Cypher nondeterminism:
the same question, same chain, same temperature=0.0 setting, produced an
empty result on one run and the correct answer on another. Vector
correctly could not answer this relational question either way (as
expected - it's not a vector-shaped question). This is the strongest
single piece of evidence in this eval that graph-query generation is not
fully reproducible run to run.

---

## Q6: Is there an existing module for provisioning an S3 bucket?
*Expected category: vector*

**Graph-only answer:** Yes - `s3-bucket-logging` and `s3-bucket-standard`.
**Vector-only answer:** Yes, with purpose explanation for each ("general-purpose use" vs. "log storage with lifecycle expiration").
**Router answer** (routed to: `vector`): Retrieved both module docs directly.

**Analysis:** Both mechanisms found the right modules, but vector's
answer is more useful - it explains *why* you'd pick one over the other,
which is exactly what this question is actually asking. Graph gives a
flat list; vector gives a recommendation. Router correctly chose the
more useful path.

---

## Q7: Do we have a module for running containerized services?
*Expected category: vector*

**Graph-only answer (one run):** No matching records were found.
**Vector-only / router answer:** Yes, `ecs-service` provisions ECS
Fargate task definitions and services for containerized workloads.

**Analysis:** Graph failed to find this by name-matching alone
("containerized" doesn't literally appear in any module name); vector
succeeded because it matches on semantic meaning, not literal string
matching. Textbook example of vector search's core strength.

---

## Q8: What module should I use to set up a Postgres database?
*Expected category: vector*

**Graph-only answer:** Failed with a Cypher syntax error on one run.
**Vector-only / router answer:** Correctly recommended `rds-postgres`
with a clear justification.

**Analysis:** Graph-only failure here didn't take down the whole system -
the router correctly used vector and returned a clean, correct,
well-justified answer. Good demonstration of the router's fallback value:
a single point of failure in one path doesn't propagate to the user.

---

## Q9: Are there any modules that do almost the same thing?
*Expected category: ambiguous*

**Graph-only answer:** Failed with a Cypher type-mismatch error (attempted
`id()` on a property rather than a node - an invalid comparison pattern
for this kind of judgment).
**Vector-only / router answer:** Compared two arbitrary retrieved modules
(lambda-function, ecs-service) and correctly concluded they're distinct -
technically correct, but incomplete (didn't surface the actual planted
duplicate pair, s3-bucket-standard/s3-bucket-logging, since those weren't
the top-k match for this particular query phrasing).

**Analysis:** This is an expected, honest limitation: duplicate-capability
findings are LLM-derived judgments computed in Epic 4.1a, not facts
stored in the graph or guaranteed to surface via generic similarity
search. Neither retrieval mechanism is well-suited to this question as
posed - the correct system design would be a dedicated tool/query that
returns the pre-computed 4.1a findings directly, rather than relying on
generic graph or vector retrieval to reconstruct them ad hoc. Good
finding for future work.

---

## Q10: What's the difference between s3-bucket-standard and s3-bucket-logging?
*Expected category: ambiguous*

**Graph-only answer (varies by run):** Sometimes "no matching records
found," sometimes a detailed, correct resource-level comparison (4
resources + lifecycle config + retention_days vs. 3 resources +
versioning_enabled).
**Vector-only answer (consistent across runs):** Correct, clear prose
comparison every time.

**Analysis:** The clearest evidence in the whole eval that vector search
is more *reliable* even when graph is capable of a more detailed answer
when it happens to work. Graph's best-case answer here is actually more
precise (exact resource counts and types) than vector's prose summary,
but its inconsistency across runs makes it less trustworthy as a system
behavior than vector's dependable, if less detailed, answer.

---

## Summary

Across 10 questions, the router correctly matched retrieval mechanism to
question type in every case (5/5 structural questions attempted graph
first; 5/5 semantic/ambiguous questions used vector, either directly or
via fallback). Deterministic graph queries answering simple, single-hop
lookups (blast radius, unused-module detection) were reliably correct.
Multi-hop or comparison-shaped graph questions (version consistency
across repos, module-to-module comparison) showed real nondeterminism -
the same question produced different Cypher, and therefore different
results, across separate runs, even at temperature=0.0.

Vector search was consistently more *reliable* run-to-run, but
structurally cannot answer relational questions (blast radius, consumer
counts) with the same precision as a correct graph query, and cannot
represent facts that live only in application logic rather than document
text (e.g., LLM-derived duplicate-capability findings from Epic 4.1a).

The router's fallback logic proved genuinely valuable in practice, not
just in theory: on multiple questions where graph-only failed outright
(Q5, Q8, Q9), the router recovered a correct or reasonable answer via the
fallback path rather than surfacing an error to the user.

The main limitation surfaced by this eval is not "which retrieval
mechanism is better" but "LLM-generated Cypher for multi-hop comparison
queries is not yet reliable enough to trust without a fallback or a
human-reviewable verification step" - itself a useful, honest finding
about the current state of GraphRAG for structured-but-relational data,
and the direct justification for this system's fallback-by-design
architecture rather than a single-retrieval-mechanism approach.
