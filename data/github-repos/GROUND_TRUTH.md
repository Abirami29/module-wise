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
