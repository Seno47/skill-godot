# Upgrade Compatibility Review

- Source/target engine and revisions:
- Contract/probe report:
- Independent release reviewer:
- Verdict: NOT TESTED

## Evidence

- Immutable fixture hashes and migration matrix:
- Clean import/build/test diffs:
- Old save/replay/mod and protocol-skew traces:
- Rollback/downgrade and dependency replacement proof:

## Review

- Is every destructive step backed up and every migration idempotent?
- Are stable IDs, behavior, rendering, performance and online compatibility preserved?
- Are unsupported versions rejected explicitly rather than partially loaded?

## Blocking defects / limitations

-
