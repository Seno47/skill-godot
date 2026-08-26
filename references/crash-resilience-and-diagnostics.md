# Crash resilience and diagnostics

Use this guide when the brief promises production reliability, crash reporting, recovery, safe mode, or supportable native builds. It complements save-data and performance guidance; it does not turn intentional force-quit noise into a crash.

## Contract before instrumentation

Record the exact build identity, supported platforms, recovery-point/data-loss budget, log retention and redaction rules, watchdog boundary, crash artifact location, native symbol identity, and which failures should degrade, restart, enter safe mode, or exit truthfully. Instantiate `assets/crash-resilience-contract.template.json`.

Godot normally writes project logs under `user://logs`; preserve a bounded previous-run log, but never write tokens, purchase payloads, personal chat, account identifiers, or full user paths without a justified policy. A useful native backtrace requires debug symbols matching the exact executable. Record both identities rather than claiming symbolication from an unrelated build.

## Builder-owned matrix

Run the exact candidate through clean exit, controlled error, crash and relaunch, hang/watchdog, memory pressure, renderer failure, corrupted settings, interrupted durable write, and redaction. Prove detection of the previous abnormal exit, bounded data loss, no duplicate settlement, a usable safe-mode/reset route, and a clear message that does not promise recovered data that was not recovered. Reproduce first; classify editor/test-driver forced termination separately from an organic target-build failure.

`scripts/crash_resilience_probe.py` checks coverage and invariants. It cannot judge whether recovery copy is understandable or whether support can use the artifacts; obtain the independent review in `assets/crash-resilience-review.template.md`.

## Boundaries

- Do not deliberately crash a user's unsaved editor session or unrelated process.
- Do not upload diagnostics without the brief's consent/privacy decision.
- A caught exception, clean `quit()`, or forced timeout is not evidence of native crash recovery.
- A crash reporter SDK being present is not evidence that reports arrive, match symbols, redact secrets, or lead to a usable recovery path.

## Primary references

- [Godot logging](https://docs.godotengine.org/en/stable/tutorials/scripting/logging.html)
- [Godot OS class, including crash-test behavior](https://docs.godotengine.org/en/stable/classes/class_os.html)
