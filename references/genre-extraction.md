# Extraction Game Production

Read this when the core loop commits a loadout or other stake, enters a bounded run/raid, acquires uncertain value under escalating risk, chooses whether and where to extract, settles success or loss, updates a persistent stash, and prepares the next run. Apply [progression-and-balance.md](progression-and-balance.md); for online play also apply [multiplayer-networking.md](multiplayer-networking.md).

## Prove the extraction loop before content multiplication

The smallest representative slice must include:

- a meaningful pre-run loadout/stash decision;
- at least two loot/risk routes or a comparable stay-versus-leave decision;
- contested pressure, scarcity, time, or another reason extraction is not automatic;
- a clearly readable extraction condition and route;
- successful extraction settlement;
- death/failure settlement with the declared secure/insurance policy;
- next-run preparation using the resulting stash;
- a renewable recovery path from a poor or bankrupt state.

A combat map with a victory trigger is not an extraction loop. A loot counter that resets at the menu is not persistent stakes. A scripted evacuation after all objectives are complete removes the defining leave-or-stay decision unless the brief intentionally uses another form of extraction tension.

## Separate raid state from durable state

Keep immutable item/loot/route definitions separate from:

- authoritative in-raid ownership and container state;
- provisional client/UI presentation;
- settlement ledger for the completed raid;
- durable stash/account state.

Use stable item-instance, raid, account/profile, and settlement IDs. Settlement is one idempotent transaction: commit/debit entry cost, return surviving gear, persist allowed loot, apply loss/insurance/fees, and advance quests exactly once. A reconnect, timeout, retry, duplicate RPC, repeated result screen, or service retry must not duplicate or erase value.

Start from `assets/extraction-loop.template.json` and run:

```bash
python <skill-dir>/scripts/extraction_loop_probe.py --model reports/extraction-loop.json --summary --json-output reports/extraction-loop-audit.json
```

The probe checks stash conservation, death/secure-container limits, insurance bounds, exactly-once settlement, duplicate/unauthorized item rejection, required routes/archetypes/scenarios, extraction windows, bankruptcy recovery, route dominance, and the declared risk/reward gradient. Export rows from the same item values and settlement results used by the target build.

## Make risk and information legible

The player should understand enough to make a decision without knowing hidden designer tables:

- approximate value/rarity and capacity pressure;
- what will be lost, protected, insured, or returned;
- extraction availability, conditions, direction, travel time, and remaining danger;
- sound/world cues for nearby threats without impossible omniscience;
- injuries, ammo/resources, team status, and encumbrance at a glance;
- whether an action is provisional, committed, or awaiting service confirmation.

Do not solve this with permanent paragraphs in several screen corners. Prefer authored item language, map/world landmarks, concise contextual prompts, coherent icons, and accessible non-color cues. Test dense inventory/loot/combat/extraction states, not only an empty stash.

## Balance loss and recovery

Combine the extraction ledger with the general progression model. Test safe, balanced, aggressive, hoarder, novice, and expert behavior as applicable. Include:

- low-roll, average, and high-roll loot seeds;
- immediate extract, normal route, and prolonged greed;
- repeated deaths and one successful recovery;
- cheapest viable loadout and high-value loadout;
- full stash, nearly empty stash, invalid/removed item, and version migration;
- insurance return timing and retry;
- disconnect before extraction, during extraction, and during settlement;
- squad ownership/loot contention when multiplayer is in scope.

The economy must not require paid value to escape an ordinary loss spiral. Recovery may be demanding, but its expected runs/time and viable starter path must be declared and tested. Conversely, secure storage, insurance, AI farming, route safety, or duplicate settlement must not erase all meaningful risk.

## Author space for extraction decisions

Spawn and extraction placement, sightlines, audio propagation, cover, traversal, verticality, loot density, landmarks, and route intersections create the real risk model. Validate multiple seeds/spawn pairs and actual traversal times. Block:

- unavoidable spawn kills or extraction camping without counterplay;
- one route dominating because it is safest, richest, and shortest;
- extraction markers visible in UI but unreadable in the world;
- loot interaction/contact failures during combat pressure;
- dead space added only to inflate raid duration;
- NPCs or effects that obscure ownership, hit feedback, exits, or dropped items.

## Acceptance

Builder-owned evidence includes successful extraction, death, settlement retry/reconnect, stash reload, and bankruptcy recovery in the target build plus the deterministic ledger audit. Then complete `assets/extraction-review.template.md` with uncoached human runs that expose loot decisions, leave/stay tension, loss response, recovery, and next-raid preparation. A model PASS cannot prove tension, fairness, fear, relief, or whether loss motivates another run.
