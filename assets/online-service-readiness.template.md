# Persistent Online Service Readiness

## Honest scope

- Product / build / protocol / content versions:
- Scope: `offline MMO-like prototype / network prototype / production slice / launch candidate`
- Declared capacity, region, availability, RPO and RTO:
- Real services versus mocks:
- Independent reviewer context:

## Ownership and trust boundaries

| Domain | Authoritative component | Durable store | Client-visible contract | Identity/authorization | Failure boundary |
|---|---|---|---|---|---|
| Session/auth |  |  |  |  |  |
| Zone/world |  |  |  |  |  |
| Character/inventory/currency |  |  |  |  |  |
| Progression/quest/reward |  |  |  |  |  |
| Social/chat/moderation |  |  |  |  |  |

## Durable transaction contract

| Mutation | Idempotency key | Preconditions/version | Atomic/compensation boundary | Retry/duplicate result | Audit evidence |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Zone, shard, and interest contract

- Stable account/character/entity/zone IDs:
- Routing and ownership model:
- Zone handoff steps and compensation:
- Interest filter and private-field policy:
- Maximum world/visible/replicated entities:
- Reconnect target and split-ownership prevention:

## Capacity and failure evidence

| State | Workload/build/config | Duration | Budgets | Observed | Artifact | Verdict |
|---|---|---:|---|---|---|---|
| Declared load |  |  |  |  |  |  |
| Soak |  |  |  |  |  |  |
| Dependency latency/outage |  |  |  |  |  |  |
| Process crash/restart |  |  |  |  |  |  |
| Duplicate/partial transaction |  |  |  |  |  |  |
| Backup restore |  |  |  |  |  |  |
| Deployment rollback/forward fix |  |  |  |  |  |  |

## Operations and abuse

- Health/readiness/drain/shutdown:
- Logs/metrics/traces/correlation and alert ownership:
- Secret/config/environment separation:
- Rate limits, bans, moderation/report/support path:
- Data retention/privacy/child-safety/legal review boundary:
- Runbook and incident escalation:

## Verdict

- `online_service_readiness_evidence`: `PASS / FAIL / NOT TESTED`
- `online_service_architecture_review`: `PASS / FAIL / NOT TESTED`
- Evidence-backed scope label:
- Blocking defects:
- Mocked or untested systems that forbid a broader MMO claim:
