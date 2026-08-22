# lambda-function

Provisions a Lambda function with a basic execution IAM role attached.

## Purpose
Standard module for any service that needs to deploy a Lambda function
without hand-writing the IAM role/policy boilerplate each time.

## Inputs
- `function_name`, `package_path`
- `handler` (default index.handler), `runtime` (default python3.12)
- `memory_size` (default 128), `timeout` (default 30)

## Outputs
- `function_arn`

## Version history
- v1.0.0 — initial release
