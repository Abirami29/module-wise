# Ground Truth — Synthetic Repo Set

Use this to validate parser output (Epic 2) and graph query output (Epic 3) against
expected answers. Do not use this file in the actual RAG pipeline — it's for your
own testing/grading only.

## Modules defined in infra-modules (8 total)
1. vpc-base            — versions: v1.0.0, v2.0.0 (current)
2. s3-bucket-standard   — version: v1.0.0
3. s3-bucket-logging    — version: v1.0.0  [DUPLICATE CAPABILITY of s3-bucket-standard]
4. rds-postgres         — version: v1.0.0
5. security-group-web   — version: v1.0.0
6. ecs-service          — version: v1.2.0
7. lambda-function      — version: v1.0.0
8. sqs-queue            — version: v1.0.0  [ORPHAN — zero consumers]

## Consumer repos
- service-webshop:
    - vpc-base @ v2.0.0
    - s3-bucket-standard @ v1.0.0
    - ecs-service @ v1.2.0
    - security-group-web @ v1.0.0
- service-billing:
    - vpc-base @ v1.0.0   <-- STALE, drift vs webshop/analytics (both on v2.0.0)
    - rds-postgres @ v1.0.0
    - security-group-web @ v1.0.0
- service-analytics:
    - vpc-base @ v2.0.0
    - s3-bucket-logging @ v1.0.0
    - lambda-function @ v1.0.0

## Expected test outcomes
| Test | Expected result |
|---|---|
| Unused module query | sqs-queue (only one with 0 consumers) |
| Version drift query | vpc-base: service-billing on v1.0.0 while webshop/analytics on v2.0.0 |
| Duplicate capability detection | s3-bucket-standard <-> s3-bucket-logging flagged as similar |
| Module count | 8 |
| Consumer repo count | 3 |
| Total module-call edges | 10 (4 + 3 + 3) |

## Sample eval questions (for Epic 4/6/7)
Graph-shaped (should be answered well by graph path):
1. Is vpc-base used consistently across all service repos? Which are behind?
2. What's the blast radius if I change security-group-web?
3. Is sqs-queue module still in use anywhere?
4. Which modules have no consumers?
5. What repos would be affected if rds-postgres changes?

Vector-shaped (should be answered well by vector path):
6. Is there an existing module for provisioning an S3 bucket?
7. Do we have a module for running containerized services?
8. What module should I use to set up a Postgres database?

Ambiguous / router test:
9. Are there any modules that do almost the same thing?
10. What's the difference between s3-bucket-standard and s3-bucket-logging?


## Epic 4 — LLM-enriched findings (expected outcomes)

### 4.1a — Duplicate capability detection
| Module A | Module B | Expected result |
|---|---|---|
| s3-bucket-standard | s3-bucket-logging | similar: true, high confidence — both provision S3 buckets with versioning + SSE; logging adds a lifecycle rule on top |

### 4.1b — Structural drift (code-grounded)
| Module | Comment | Expected result |
|---|---|---|
| s3-bucket-standard | "Encryption disabled for this bucket per legacy compliance exemption..." | Flagged as structural_drift — module currently provisions `aws_s3_bucket_server_side_encryption_configuration`, contradicting the comment's claim |

### 4.1b — Narrative alignment (surfaced, not adjudicated)
| Module | Sources compared | Expected result |
|---|---|---|
| vpc-base | README + internal doc (vpc-flow-logs-decision.md) + inline comment | consistent: true — all three agree flow logs were added in v2.0.0 for SOC2 compliance; this is the negative test case proving the system doesn't cry wolf on aligned sources |

### 4.2 — GraphCypherQAChain (natural language Q&A)
| Question | Expected answer content |
|---|---|
| Is vpc-base used consistently across all service repos? | No — service-billing is on v1.0.0 (stale); service-analytics and service-webshop are on v2.0.0 |
| What's the blast radius if I change security-group-web? | Two consumers: service-billing and service-webshop |
| Is sqs-queue module still in use anywhere? | No — zero consumers found |
| Which modules have no consumers? | sqs-queue (the only orphaned module) |

## Notes on LLM-based checks (4.1, 4.2)
Unlike Epic 3's deterministic Cypher queries, these results depend on LLM output and
are not guaranteed to be word-for-word identical between runs. Validate against the
*substance* of the expected result (correct module names, correct true/false verdicts,
correct version numbers), not exact phrasing. Known failure modes encountered and
fixed during development, in case they resurface:
- Empty response / finish_reason=length -> model exhausted output budget on internal
  reasoning before writing the answer. Fixed via reasoning_effort="low" + adequate max_tokens.
- Repetition loops at temperature=0.0 -> fixed via frequency_penalty=0.4 + explicit
  word-limit constraints in prompts.
- Answer-synthesis hedging in GraphCypherQAChain (model says "cannot determine" despite
  correct data in context) -> fixed via a custom qa_prompt that explicitly instructs the
  model to trust retrieved data and never claim it lacks information when data is present.
- All LLM calls wrapped in retry logic (invoke_json, up to 3 attempts) since occasional
  malformed/looping output is a known nondeterministic risk even with the above fixes.