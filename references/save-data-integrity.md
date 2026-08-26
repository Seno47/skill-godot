# Save Data Integrity and Migration

Read this when progress, settings, unlocks, worlds, inventories, replays, procedural state, or platform/cloud data must survive a restart or build update. A successful `FileAccess.open()` call is wiring, not a persistence contract.

## Define ownership and the envelope

Start from `assets/save-data-contract.template.json`. Record the authoritative owner, slot/profile/account identity, current schema/content/build version, supported source versions, critical fields, storage paths, size and latency budgets, backup/restore policy, and platform/cloud boundary.

Use a versioned envelope around payload data: schema version, content/build compatibility, stable profile/slot ID, timestamp or monotonic revision, payload checksum, and commit/transaction ID where retries are possible. Keep settings separate from gameplay progress when they have different reset/sync policies.

Persist stable IDs and value data, not live node references, instance IDs, RIDs, transient scene paths, or arbitrary executable resources. Godot JSON needs explicit conversion for engine types; binary `store_var` is not a substitute for a version/migration policy.

## Make local writes recoverable

For material progress, use a project-owned atomic commit sequence appropriate to the target filesystem:

1. serialize and validate a complete candidate;
2. write to a temporary file and flush/close;
3. read back or verify length/checksum when corruption risk matters;
4. preserve the previous known-good generation;
5. replace/promote the candidate;
6. remove stale temporary state only after success.

Test interruption before write, mid-write, after candidate close, during promote, and after promote. Loading must distinguish missing, corrupt, unsupported-newer, migratable-older, and valid data. Never silently overwrite the only recoverable copy after a parse or migration failure.

## Keep migrations explicit and testable

Migrations form a monotonic chain from every supported source version to current. Each step should be deterministic, side-effect-free until final commit, preserve unknown fields when forward-compatible policy requires it, and either produce a valid current payload or fail without destroying the source.

Maintain golden fixtures for the oldest supported, each released intermediate, current, corrupt/truncated, semantically invalid, and future-version save. Prove:

- exact critical state after migration and target-build load;
- a second load does not duplicate rewards, actors, quests, mail, or transactions;
- removed content maps to a declared fallback/refund rather than a soft lock;
- new-game/reset affects only the intended slot/domain;
- save during pause, scene transition, death/result, focus loss, or shutdown respects the declared boundary.

Run:

```bash
python <skill-dir>/scripts/save_data_probe.py --model reports/save-data-contract.json --summary --json-output reports/save-data-audit.json
```

The probe checks scenario/version coverage, round-trip digests, critical-field loss, interruption/corruption recovery, atomic cleanup, migration, duplicate-load idempotence, cloud-conflict policy, and size/time budgets. Its traces must come from the target build or the same serializer/migrator used by it.

## Cloud and multi-device state

Local save and cloud synchronization are separate systems. Record whether the platform syncs files after process exit or through an API, which paths are included, offline behavior, conflict identity/revision policy, clock trust, quota/error handling, and how deletion propagates. Test two-device divergence, offline advancement, stale upload, same-revision conflict, failed upload/download, and retry without duplicate progression.

Do not merge inventories or currencies by adding both payloads unless the economy explicitly defines that operation. Prefer server authority for valuable online state. Preserve the losing copy or a conflict record when automatic resolution could destroy player progress.

## Acceptance

Builder-owned acceptance requires target-build traces for clean create, round trip, interrupted commit, corrupt primary, every supported migration origin, repeated load, reset, and applicable cloud conflict. Complete `assets/save-data-integrity-review.template.md`. Missing platform storage access may remain `NOT TESTED`; it cannot be inferred from a local JSON unit test.

Primary Godot references:

- [Saving games](https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html)
- [FileAccess](https://docs.godotengine.org/en/stable/classes/class_fileaccess.html)

