# LiveOps, Telemetry, and Privacy

Read this when remote configuration, analytics, experiments, crash reporting, inbox/events, downloadable catalogs, seasons or operational dashboards affect the game.

Treat every remote response as untrusted versioned data. Record schema, defaults, signature/authenticity where needed, timeout/retry/backoff, cache expiry, kill switch, rollout/rollback, environment separation and the exact systems remote data may change. Core play and purchased/durable state need a safe offline/default path; remote config must not become arbitrary remote code.

Telemetry uses an explicit event dictionary with purpose, fields, units, sampling, consent/legal basis, retention, deletion/export route and forbidden sensitive fields. Queue offline events with bounds and idempotent IDs; do not block gameplay, duplicate rewards, embed service secrets, or log authentication/payment/user content casually. Experiments require stable assignment, exposure events, guardrail metrics and an end condition.

Use `assets/liveops-contract.template.json`, run `scripts/liveops_probe.py`, and complete `assets/liveops-review.template.md`. Prove timeout, malformed/stale response, offline queue overflow, duplicate retry, opt-out, deletion, environment mismatch, rollback and target-build observability.

Primary Godot reference: [Making HTTP requests](https://docs.godotengine.org/en/stable/tutorials/networking/http_request_class.html).
