# Decision: VPC Flow Logs Required for All Services

**Date:** 2026-06-02
**Status:** Approved
**Related module:** vpc-base (v2.0.0+)

## Context
Following the Q2 2026 SOC2 audit, VPC flow logs are now required for all
production network infrastructure for audit visibility.

## Decision
The `vpc-base` module was updated to `v2.0.0`, adding flow log support
enabled by default. All services must migrate off `v1.0.0` by end of
Q3 2026 to remain compliant.

## Impact
Services still pinned to `vpc-base v1.0.0` do not have flow logs and will
be flagged in the next audit cycle. `service-billing` is currently on
v1.0.0 and needs to upgrade.