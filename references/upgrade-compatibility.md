# Upgrade compatibility

Use this guide for Godot version upgrades, renderer/language/addon replacement, protocol/schema changes, or release updates that must preserve old saves, replays, mods, or online compatibility.

## Freeze the before-state

Before migration, record source/target engine builds and revisions, dependency locks, export templates, immutable hashes for representative old saves/replays/mods, supported client/server skew, rollback point, and acceptance budgets. Work on version control or a copy; never destructively import the only copy of a project or player fixture. Instantiate `assets/upgrade-compatibility-contract.template.json`.

Read every applicable Godot migration page between versions and inspect release notes for project-specific behavioral changes. Upgrade one boundary at a time. Make data migrations versioned and idempotent; preserve stable IDs; reject unsupported downgrade or network skew truthfully instead of partially loading corrupt state.

## Required matrix

Prove clean import/build, old save, old replay, old mod/addon data when supported, removed/replaced dependency, declared mixed client/server window, rollback, and explicit downgrade rejection. Compare source-fixture hashes before every run. Re-run core deterministic, target-build, performance, rendering, input, and store/service checks; an editor that opens cleanly is not a compatibility verdict.

Run `scripts/upgrade_compatibility_probe.py`, then use `assets/upgrade-compatibility-review.template.md` for an independent release review.

## Primary references

- [Godot upgrade guides](https://docs.godotengine.org/en/4.4/tutorials/migrating/index.html)
- [Example: upgrading to Godot 4.7](https://docs.godotengine.org/en/stable/tutorials/migrating/upgrading_to_godot_4.7.html)
- [Godot release policy](https://docs.godotengine.org/en/stable/about/release_policy.html)
