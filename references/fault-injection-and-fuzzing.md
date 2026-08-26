# Fault injection and fuzzing

Use this guide when a system crosses durable, network, service, streaming, asynchronous, or shutdown boundaries. This is builder-owned routine resilience QA, not destructive testing of production users or services.

## Declare boundaries and invariants

List injection points, expected safe state, deterministic seeds, maximum runtime/input size, durable invariants, retry/rollback policy, and test environment. Typical targets are save writes, network responses, remote config, purchase callbacks, cloud sync, streamed assets, scene transitions, and shutdown. Instantiate `assets/fault-injection-contract.template.json`.

Exercise control plus interruption, timeout, duplicate, reordering, malformed, truncated, oversized, disk-full, and permission-denied conditions wherever applicable. Assert no unhandled exception/hang, duplicate durable effect, orphan task, stale lock, cross-user write, or unbounded allocation. Shrink and retain the smallest failing input/seed as a regression fixture.

Use project-owned injection adapters at real boundaries rather than peppering production logic with random failures. Fuzz parsers and message boundaries under explicit byte/time budgets. Never point load/fuzz traffic at a live third-party or production backend without authorization.

Run `scripts/fault_injection_probe.py`. Use `assets/fault-injection-review.template.md` to record the threat surface, corpus, minimized failures, and remaining untested boundaries. Passing the probe means the declared matrix is internally consistent; it does not prove undisclosed targets safe.
