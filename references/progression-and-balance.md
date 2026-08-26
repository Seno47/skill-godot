# Progression and Balance Across Genres

Read this when a game has material persistent progression, upgrades, levels, resources, rewards, unlocks, escalating challenge, meta-progression, or a player-facing economy. Apply it alongside the genre guide; it does not replace quest topology, metroidvania soft-lock checks, idle arithmetic, combat simulation, or target-build play.

## Decide whether the layer applies

Use the progression-heavy contract when one or more of these can materially change the player's future options or power:

- XP, ranks, equipment, skills, research, construction, crafting, followers, cards, perks, or permanent unlocks;
- currencies, consumable resources, production chains, upkeep, repair, death loss, shops, or prestige resets;
- authored level/chapter progression whose reward cadence or difficulty curve is part of the experience;
- branching routes or builds where one option can become dead, mandatory, or overwhelmingly dominant;
- offline progress, repeatable rewards, daily/session structures, or monetized acceleration.

A one-screen toy, a short mechanics prototype, or purely cosmetic menu unlock may document this layer as not applicable. Do not invent progression merely to satisfy the workflow.

## Write the balance contract before content multiplication

Start from `assets/progression-balance.template.json`. Replace every example budget with a project-specific hypothesis before using its PASS as evidence. Record:

- the player-facing progression promise and target session/completion cadence;
- the authoritative resources, sources, sinks, floors, caps, and reset boundaries;
- how player power and challenge are represented at comparable checkpoints;
- meaningful unlocks and choices, including options that must remain viable;
- failure cost and recovery time;
- representative player archetypes and strategies;
- monetization policy and the complete free path when monetization exists;
- the exact model/build version and deterministic seeds.

Choose archetypes that stress the actual game. `novice / typical / expert` is a useful baseline for a level campaign; a strategy game may use `turtle / expansion / rush`, a roguelite `safe / balanced / high-risk`, a survival game `hoarder / builder / explorer`, and an idle game `active / mixed / offline`. Do not rename one optimal script three times and call it coverage.

Declare only applicable checks in `contract.required_checks`:

- `power_challenge` — player power does not fall far below or trivialize comparable challenge;
- `unlock_cadence` — meaningful unlock drought stays within the declared budget;
- `choice_cadence` — the player is not left without a meaningful decision for too long;
- `failure_recovery` — a reasonable failure does not create an undeclared recovery grind or irreversible spiral;
- `option_viability` — required builds/upgrades/routes are exercised and no option exceeds the declared pick-share ceiling;
- `resource_bounds` — balances cannot cross floors/caps through supported play;
- `source_sink_concentration` — one source or sink does not accidentally make the rest irrelevant.

Absence from `required_checks` is not a loophole. Give a short rationale for any obviously relevant omitted check in the review record.

## Keep the model honest

Export project-specific traces from the same data or formulas the game uses where practical. Use decimal strings for economic values and record whether each trace came from deterministic simulation or the target build. Run:

```bash
python <skill-dir>/scripts/progression_balance_probe.py --model reports/progression-balance.json --summary --json-output reports/progression-balance-audit.json
```

The probe validates declared archetype/checkpoint coverage, resource floors/caps, source/sink presence and concentration, power-to-challenge bands, unlock/choice drought, recovery time, and option viability/dominance. It cannot establish whether the game is fun, whether a choice is cognitively meaningful, or whether the target build implements the model correctly.

Therefore a builder-owned balance gate needs both deterministic model evidence and at least one target-build transaction trace. Prove displayed cost equals debited cost, reward is granted exactly once, unlock conditions match the authored data, save/reload preserves the result, and the player cannot duplicate, skip, or lose the transaction through pause/retry/scene transitions.

## Test the whole curve, not only averages

Inspect at least onboarding/first reward, first meaningful choice, early stable loop, representative midgame, late/high-pressure state, and completion or reset. Add any discontinuity: new currency, difficulty tier, prestige, chapter boundary, procedural modifier, death-loss rule, or paid/rewarded acceleration.

Look for:

- bankruptcy or soft locks caused by mandatory costs, upkeep, death loss, or an exhausted source;
- hoarding because a resource has no useful sink or future prices make current spending irrational;
- a dominant upgrade/build and options that are presented but never rationally selected;
- multiplicative stacking, integer/decimal overflow, rounding arbitrage, negative prices, duplicate rewards, and save/offline exploits;
- power spikes that erase the next challenge and challenge spikes that invalidate previously taught play;
- reward drought, constant low-value reward noise, and late rewards that arrive after they matter;
- recovery loops that make one failure compound into more failures;
- grind used to inflate a duration claim rather than create decisions.

Average completion time can hide all of these. Preserve per-archetype traces and inspect the worst supported case, not only the mean.

## Adapt by progression shape

- **Level campaign/puzzle:** model unlock cadence, difficulty steps, retries, content permutations, and whether rewards change decisions rather than only numbers.
- **RPG/action RPG:** model XP/level bands, equipment and skill alternatives, consumable economy, enemy scaling, respec/recovery, and power stacking.
- **Roguelite:** separate run power from permanent meta-power; test unlucky and high-roll seeds, reset value, dead unlocks, and whether meta-progression erases the core challenge.
- **Strategy/management:** test multiple openings, expansion/upkeep constraints, resource conversion loops, snowballing, comeback/recovery, and late-game sink relevance.
- **Survival/crafting:** test depletion/regeneration, mandatory needs, crafting chains, death loss, renewable recovery paths, storage caps, and exploit loops.
- **Metroidvania/quest:** combine this layer with graph/transaction audits; topology can be valid while ability, reward, or backtracking pacing is poor.
- **Idle/incremental:** retain the exact idle-economy probe for curve/offline arithmetic; use this layer for build diversity, source/sink health, milestone drought, prestige recovery, and active/offline archetypes.
- **Extraction:** combine this layer with [genre-extraction.md](genre-extraction.md); separately model raid commitment/loss, durable settlement, secure/insurance boundaries, route risk, and recovery rather than treating one expected-value curve as proof.
- **Persistent online/MMO:** combine this layer with [mmo-and-online-services.md](mmo-and-online-services.md); prove authoritative durable transactions, migration/rollback behavior, cohort and capacity assumptions, and live failure recovery instead of balancing only a local client model.
- **Live-service or monetized:** evaluate the free path independently. Paid or rewarded acceleration must not conceal a broken free curve, manufacture a problem solely to sell its removal, or violate the user-approved monetization policy.

## Human pacing evidence

Routine correctness remains builder-owned. The builder must autonomously fix arithmetic, transactions, impossible states, exploits, and model/build divergence. Do not wait for the user to discover them.

For a complete progression-heavy game, also instantiate `assets/progression-balance-review.template.md` and obtain uncoached human play traces from separate clean profiles. Use representative cohorts and preserve observed time, choices, failures, abandoned goals, and comments. This reviewer need not be the user; the user is not the default QA department.

Human evidence answers what simulation cannot:

- did players understand what they were working toward;
- did rewards change a decision or merely add noise;
- did a drought feel intentional, dull, or coercive;
- did a failure invite another attempt or create fatigue;
- did a supposedly viable option feel like a trap;
- could critical state be read without spreadsheet knowledge.

If these traces are unavailable, report the pacing gate as `NOT TESTED`. Do not convert a deterministic autoplay, designer playthrough, theoretical solve-time sum, or model PASS into human pacing evidence.

## Completion rule

Do not hand off a progression-heavy complete game as balanced when either the builder-owned model/target-build gate or the uncoached pacing gate is unresolved. A vertical slice may be handed off as a slice with explicit tested range and limitations; it must not imply that an unmodeled midgame, endgame, prestige, or monetized path is ready.
