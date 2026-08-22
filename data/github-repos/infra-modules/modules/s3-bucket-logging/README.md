# s3-bucket-logging

Provisions an S3 bucket intended for log storage, with versioning,
encryption, and a lifecycle rule to expire old logs.

## Purpose
Originally created for a service that needed log retention with automatic
expiry. Functionally very similar to s3-bucket-standard (bucket + versioning
+ SSE-S3) with an added lifecycle expiration rule bolted on.

## Inputs
- `bucket_name`
- `environment`
- `retention_days` (default: 90)

## Outputs
- `bucket_id`
- `bucket_arn`

## Version history
- v1.0.0 — initial release: bucket, versioning, SSE-S3 encryption, lifecycle expiry
