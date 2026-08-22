# security-group-web

Provisions a security group allowing inbound HTTP/HTTPS traffic from
anywhere, and unrestricted egress.

## Purpose
Standard security group for any public-facing web service (ALB, ECS service,
EC2 instance) that needs to accept inbound traffic on ports 80/443.

## Inputs
- `name`, `vpc_id`

## Outputs
- `security_group_id`

## Version history
- v1.0.0 — initial release
