# vpc-base

Provisions a base VPC with public subnets and an internet gateway.

## Purpose
Standard starting point for any service that needs its own network boundary.
Creates a VPC, one public subnet per availability zone provided, and an
internet gateway attached to the VPC.

## Inputs
- `name` — name prefix for tagging
- `cidr_block` — VPC CIDR block (default 10.0.0.0/16)
- `public_subnet_cidrs` — list of subnet CIDRs
- `availability_zones` — list of AZs to spread subnets across

## Outputs
- `vpc_id`
- `public_subnet_ids`

## Version history
- v2.0.0 — added VPC flow logs support (enable_flow_logs, flow_log_destination_arn)
- v1.0.0 — initial release: VPC, public subnets, internet gateway

## Security note
As of v2.0.0, flow logs are enabled by default for audit/compliance visibility.
Consumers still pinned to v1.0.0 do not have flow logs and should upgrade.
