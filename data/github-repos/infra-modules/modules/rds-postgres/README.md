# rds-postgres

Provisions a managed PostgreSQL RDS instance with a dedicated security group
and subnet group.

## Purpose
Standard module for any service that needs a relational Postgres database.
Handles subnet group, security group (port 5432 ingress only from allowed
CIDRs), and the RDS instance itself.

## Inputs
- `name`, `vpc_id`, `subnet_ids`, `allowed_cidr_blocks`
- `engine_version` (default 15.4), `instance_class` (default db.t3.micro)
- `allocated_storage` (default 20), `username`, `password` (sensitive)
- `skip_final_snapshot` (default false)

## Outputs
- `db_endpoint`

## Version history
- v1.0.0 — initial release
