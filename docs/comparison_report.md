# GraphRAG vs. Vector RAG Comparison Report

Generated: 2026-08-24 03:23

Each question below was run through three configurations: the graph-only 
path (GraphCypherQAChain), the vector-only path (embedding similarity search 
+ synthesis), and the LangGraph router (which selects automatically between them).

---

## Q1: Is vpc-base used consistently across all service repos? Which are behind?
*Expected category: graph*

**Graph-only answer:**
> No matching records were found regarding the consistency of vpc-base usage across service repos or which repos might be behind.

**Vector-only answer:**
> The retrieved documentation does not contain information about which service repos use `vpc-base` or their consistency of usage.

**Router answer** (routed to: `graph`):
> No matching records were found regarding the consistency of vpc-base usage across service repos or which repos might be behind.

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q2: What's the blast radius if I change security-group-web?
*Expected category: graph*

**Graph-only answer:**
> The blast radius includes the services `service-billing` and `service-webshop`.

**Vector-only answer:**
> Based on the documentation, changing `security-group-web` would affect any public-facing web service (ALB, ECS service, EC2 instance) that uses this module to accept inbound HTTP/HTTPS traffic on ports 80/443.

**Router answer** (routed to: `graph`):
> The blast radius includes the services `service-billing` and `service-webshop`.

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q3: Is sqs-queue module still in use anywhere?
*Expected category: graph*

**Graph-only answer:**
> No matching records were found, so the data does not show that the sqs-queue module is in use anywhere.

**Vector-only answer:**
> No, the sqs-queue module is not in use; it was built for a prototype that was later shelved, and no consumers are currently wired to it.

**Router answer** (routed to: `graph`):
> No matching records were found, so the data does not show that the sqs-queue module is in use anywhere.

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q4: Which modules have no consumers?
*Expected category: graph*

**Graph-only answer:**
> The provided data shows a single module named **`sqs-queue`** (id: `infra-modules:sqs-queue`) containing 2 AWS SQS queue resources. No consumer modules are listed for it in this data, so it has no consumers according to the query results.

**Vector-only answer:**
> The `sqs-queue` module has no consumers currently wired to it.

**Router answer** (routed to: `graph`):
> The provided data lists one module named `sqs-queue` (id: `infra-modules:sqs-queue`) containing 2 AWS SQS queue resources. This is the only module shown, and it has no consumer relationships recorded in the retrieved data—so it has no consumers according to this query result.

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q5: What repos would be affected if rds-postgres changes?
*Expected category: graph*

**Graph-only answer:**
> The affected repository would be **service-billing**.

**Vector-only answer:**
> The retrieved documentation does not mention any repositories that depend on or would be affected by changes to `rds-postgres`.

**Router answer** (routed to: `graph`):
> The repo `service-billing` would be affected if `rds-postgres` changes.

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q6: Is there an existing module for provisioning an S3 bucket?
*Expected category: vector*

**Graph-only answer:**
> Yes, there is an existing module for provisioning an S3 bucket.

**Vector-only answer:**
> Yes, there are existing modules for provisioning an S3 bucket: `s3-bucket-standard` for general-purpose use and `s3-bucket-logging` for log storage with lifecycle expiration.

**Router answer** (routed to: `vector`):
> Found relevant documentation:

[s3-bucket-standard]
# s3-bucket-standard

Provisions a general-purpose S3 bucket with versioning and default
server-side encryption enabled.

## Purpose
Use this module whenever a service needs a general-purpose S3 bucket for
storing application data, assets, or backups, with sane security defaults
(encryption at rest,

[s3-bucket-logging]
# s3-bucket-logging

Provisions an S3 bucket intended for log storage, with versioning,
encryption, and a lifecycle rule to expire old logs.

## Purpose
Originally created for a service that needed log retention with automatic
expiry. Functionally very similar to s3-bucket-standard (bucket + version

[lambda-function]
# lambda-function

Provisions a Lambda function with a basic execution IAM role attached.

## Purpose
Standard module for any service that needs to deploy a Lambda function
without hand-writing the IAM role/policy boilerplate each time.

## Inputs
- `function_name`, `package_path`
- `handler` (defau

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q7: Do we have a module for running containerized services?
*Expected category: vector*

**Graph-only answer:**
> No matching records were found.

**Vector-only answer:**
> Yes, the `ecs-service` module provisions an ECS Fargate task definition and service for deploying containerized services.

**Router answer** (routed to: `vector`):
> Found relevant documentation:

[ecs-service]
# ecs-service

Provisions an ECS Fargate task definition and service.

## Purpose
Standard module for deploying a containerized service on ECS Fargate.
Wraps task definition + service creation with sensible defaults.

## Inputs
- `service_name`, `cluster_id`, `container_image`
- `container_port` (de

[data/internal-docs/vpc-flow-logs-decision.md]
# Decision: VPC Flow Logs Required for All Services

**Date:** 2026-06-02
**Status:** Approved
**Related module:** vpc-base (v2.0.0+)

## Context
Following the Q2 2026 SOC2 audit, VPC flow logs are now required for all
production network infrastructure for audit visibility.

## Decision
The `vpc-bas

[lambda-function]
# lambda-function

Provisions a Lambda function with a basic execution IAM role attached.

## Purpose
Standard module for any service that needs to deploy a Lambda function
without hand-writing the IAM role/policy boilerplate each time.

## Inputs
- `function_name`, `package_path`
- `handler` (defau

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q8: What module should I use to set up a Postgres database?
*Expected category: vector*

**Graph-only answer:**
> 

**Vector-only answer:**
> You should use the `rds-postgres` module, as it provisions a managed PostgreSQL RDS instance with a dedicated security group and subnet group.

**Router answer** (routed to: `vector`):
> Found relevant documentation:

[rds-postgres]
# rds-postgres

Provisions a managed PostgreSQL RDS instance with a dedicated security group
and subnet group.

## Purpose
Standard module for any service that needs a relational Postgres database.
Handles subnet group, security group (port 5432 ingress only from allowed
CIDRs), and the RDS instance

[ecs-service]
# ecs-service

Provisions an ECS Fargate task definition and service.

## Purpose
Standard module for deploying a containerized service on ECS Fargate.
Wraps task definition + service creation with sensible defaults.

## Inputs
- `service_name`, `cluster_id`, `container_image`
- `container_port` (de

[lambda-function]
# lambda-function

Provisions a Lambda function with a basic execution IAM role attached.

## Purpose
Standard module for any service that needs to deploy a Lambda function
without hand-writing the IAM role/policy boilerplate each time.

## Inputs
- `function_name`, `package_path`
- `handler` (defau

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q9: Are there any modules that do almost the same thing?
*Expected category: ambiguous*

**Graph-only answer:**
> No matching records were found.

**Vector-only answer:**
> No, the retrieved documentation describes two distinct modules: `lambda-function` for Lambda functions and `ecs-service` for ECS Fargate services, which do not do almost the same thing.

**Router answer** (routed to: `vector`):
> Found relevant documentation:

[lambda-function]
# lambda-function

Provisions a Lambda function with a basic execution IAM role attached.

## Purpose
Standard module for any service that needs to deploy a Lambda function
without hand-writing the IAM role/policy boilerplate each time.

## Inputs
- `function_name`, `package_path`
- `handler` (defau

[ecs-service]
# ecs-service

Provisions an ECS Fargate task definition and service.

## Purpose
Standard module for deploying a containerized service on ECS Fargate.
Wraps task definition + service creation with sensible defaults.

## Inputs
- `service_name`, `cluster_id`, `container_image`
- `container_port` (de

[data/internal-docs/vpc-flow-logs-decision.md]
# Decision: VPC Flow Logs Required for All Services

**Date:** 2026-06-02
**Status:** Approved
**Related module:** vpc-base (v2.0.0+)

## Context
Following the Q2 2026 SOC2 audit, VPC flow logs are now required for all
production network infrastructure for audit visibility.

## Decision
The `vpc-bas

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Q10: What's the difference between s3-bucket-standard and s3-bucket-logging?
*Expected category: ambiguous*

**Graph-only answer:**
> No matching records were found.

**Vector-only answer:**
> The main difference is that s3-bucket-logging includes a lifecycle rule to expire old logs, while s3-bucket-standard does not; otherwise they are functionally very similar.

**Router answer** (routed to: `vector`):
> Found relevant documentation:

[s3-bucket-logging]
# s3-bucket-logging

Provisions an S3 bucket intended for log storage, with versioning,
encryption, and a lifecycle rule to expire old logs.

## Purpose
Originally created for a service that needed log retention with automatic
expiry. Functionally very similar to s3-bucket-standard (bucket + version

[s3-bucket-standard]
# s3-bucket-standard

Provisions a general-purpose S3 bucket with versioning and default
server-side encryption enabled.

## Purpose
Use this module whenever a service needs a general-purpose S3 bucket for
storing application data, assets, or backups, with sane security defaults
(encryption at rest,

[vpc-base]
# vpc-base

Provisions a base VPC with public subnets and an internet gateway.

## Purpose
Standard starting point for any service that needs its own network boundary.
Creates a VPC, one public subnet per availability zone provided, and an
internet gateway attached to the VPC.

## Inputs
- `name` — 

**Analysis:** _[fill in: which answer was most correct/useful, and why]_

---

## Summary

_[fill in after reviewing all 10: overall pattern of when graph wins vs. 
vector wins vs. they tie; how often the router matched the better path]_
