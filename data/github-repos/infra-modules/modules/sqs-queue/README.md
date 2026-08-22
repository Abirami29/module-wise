# sqs-queue

Provisions an SQS queue with an optional dead-letter queue.

## Purpose
Built for an early async-processing prototype that was later shelved.
Standard queue + optional DLQ, no consumers currently wired to this module.

## Inputs
- `queue_name`
- `visibility_timeout` (default 30), `message_retention_seconds` (default 345600)
- `enable_dlq` (default true)

## Outputs
- `queue_url`

## Version history
- v1.0.0 — initial release
