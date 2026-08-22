# ecs-service

Provisions an ECS Fargate task definition and service.

## Purpose
Standard module for deploying a containerized service on ECS Fargate.
Wraps task definition + service creation with sensible defaults.

## Inputs
- `service_name`, `cluster_id`, `container_image`
- `container_port` (default 8080), `cpu` (default 256), `memory` (default 512)
- `desired_count` (default 2), `subnet_ids`, `security_group_ids`

## Outputs
- `service_name`

## Version history
- v1.2.0 — added configurable cpu/memory (previously hardcoded)
- v1.1.0 — added desired_count variable
- v1.0.0 — initial release
