# Procedural Generation and Roguelike Content

Read this when rooms, maps, encounters, loot, quests, terrain, waves, or runs are generated. Runtime generation is valid scene architecture only when the seed/data contract remains reproducible, inspectable, playable, and visually authored.

## Define generator truth before volume

Start from `assets/procedural-generation-contract.template.json`. Record generator and content-schema version, seed representation, deterministic RNG streams, mandatory landmarks/verbs, topology and solvability rules, placement/spacing constraints, content pools/weights, difficulty/resource bands, retry/fallback policy, save/resume representation, and generation-time/memory budgets.

Use separate RNG streams or derived hashed seeds for topology, rewards, encounters, decoration, and presentation when one extra cosmetic draw must not rewrite gameplay. Godot's `RandomNumberGenerator.seed` can reproduce a sequence, and its state can be restored, but the underlying algorithm is an implementation detail; preserve generator/content version and generated decisions when cross-version exact replay matters.

## Validate properties, not screenshots alone

Every generated result should expose a compact manifest: seed, version, topology hash, start/exit/objective IDs, critical route, required feature counts, placed content IDs, fallback/retry count, timing, and validation result. Test large deterministic seed cohorts plus named regression seeds.

Reject seeds with:

- disconnected start/goal or required objective, lock/key ordering traps, unreachable rewards, invalid spawn/nav/collision, or no recovery path;
- required mechanic, resource floor, safe area, landmark, checkpoint, or exit missing;
- impossible density, overlaps, occluded interactions, camera violations, or performance spikes;
- trivial repeated layouts masked only by decoration;
- reward/difficulty distributions outside declared bands;
- retries without a deterministic limit and fallback.

Run:

```bash
python <skill-dir>/scripts/procedural_generation_probe.py --model reports/procedural-generation-contract.json --summary --json-output reports/procedural-generation-audit.json
```

The probe checks seed/repeat coverage, same-seed topology hashes, connectivity/required features, invalid counts, retry/fallback bounds, save/resume parity, generation budgets, distribution ranges, and dominant-layout share.

## Preserve authored presentation

Generation should assemble authored rooms, tiles, encounters, props, lighting sets, audio zones, and rules rather than producing raw engine geometry as final art. Validate seams, entrances, pivots, nav links, lighting transitions, dressing collisions, semantic landmarks, camera sightlines, audio continuity, and dense VFX states across quiet/typical/extreme seeds.

Complete `assets/procedural-generation-review.template.md`. Human runs must judge route comprehension, repetition, meaningful decisions, pacing variance, visual rhythm, surprising-but-fair combinations, and whether the worst valid seeds still meet the player promise. Seed count cannot prove novelty or fun.

Primary Godot reference: [RandomNumberGenerator](https://docs.godotengine.org/en/stable/classes/class_randomnumbergenerator.html).

