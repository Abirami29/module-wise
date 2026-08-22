# s3-bucket-standard

Provisions a general-purpose S3 bucket with versioning and default
server-side encryption enabled.

## Purpose
Use this module whenever a service needs a general-purpose S3 bucket for
storing application data, assets, or backups, with sane security defaults
(encryption at rest, optional versioning).

## Inputs
- `bucket_name`
- `environment`
- `versioning_enabled` (default: true)

## Outputs
- `bucket_id`
- `bucket_arn`

## Version history
- v1.0.0 — initial release: bucket, versioning, SSE-S3 encryption
