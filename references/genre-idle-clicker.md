# Idle and Clicker Game Production

Read this for manual-click, incremental, idle, automation, prestige, or long-horizon economy loops. A large number and an upgrade list do not by themselves make a complete idle game.

Also apply [progression-and-balance.md](progression-and-balance.md) for active/mixed/offline archetypes, build or producer viability, source/sink concentration, milestone drought, failure/prestige recovery, and uncoached pacing. The idle-specific probe remains authoritative for exact curve/offline arithmetic; the cross-genre layer does not replace it.

## Define the economy as data

Record:

- currencies and their smallest exact units;
- manual action gain and cadence limits;
- each producer/upgrade's cost function, marginal production, unlock condition, purchase modes, and maximum level if any;
- short-session milestones, long-session targets, walls/recovery, automation, prestige/reset, and fail states if the design has them;
- offline progress formula, cap, clock rollback/forward policy, trusted-time needs, and player-facing explanation;
- save cadence/schema/migration and cloud/local conflict policy;
- numeric display notation, localization, rounding, and maximum supported magnitude.

Keep definitions in typed resources or a validated data table and runtime ownership in a central economy/session model. UI rows observe changes and issue commands; they do not own balances or run one independent producer loop per row.

Export a representative balance model and run:

```bash
python <skill-dir>/scripts/idle_economy_probe.py \
  --model <economy.json> --summary \
  --json-output <reports/economy.json>
```

The probe checks positive/monotonic curves, event-driven best-payback simulation, declared milestones, and offline caps with decimal arithmetic. It does not prove fun, save correctness, or the game's actual GDScript implementation.

## Exact and efficient simulation

- Prefer integer smallest units or a deliberate arbitrary-precision/fixed-decimal representation. Do not let binary float drift silently decide affordability, purchases, or saved balances.
- Advance production from one authoritative clock/tick. Batch long/offline intervals mathematically instead of simulating every missed frame.
- Update visible values on model changes or a bounded presentation refresh rate; do not format every label and recalculate every price in every `_process()` call.
- Cache or incrementally update cost/rate curves when safe. Profile before optimizing thousands of definitions that are not actually active.
- Define rounding at the transaction boundary. The displayed cost must agree with the debited cost.
- Keep time manipulation policy explicit. Negative elapsed time yields no reward; implausibly large elapsed time is capped/flagged according to the brief.

## Purchase and progression UX

- Show current currency, current production, exact purchase cost, production delta, owned level/count, and unavailable reason where those affect choice.
- Support only purchase modes the design needs (`x1`, `x10`, `xMax`, target level); compute them from the same transaction code.
- Keep large localized numbers in stable containers and test notation transitions, rounding, singular/plural, and extremely long values.
- A disabled upgrade must remain readable and explain the gap or unlock condition without relying on color alone.
- Give the manual action authored tactile/visual/audio feedback and varied production feedback; avoid a generic stock button surrounded by dashboard cards.
- Teach the first earn -> purchase -> visible production change through action. Do not start pressure, ads, or a wall before that loop is understood.

## Save and offline integrity

Save versioned primitive state: currency units, owned levels/counts, unlock/prestige state, timestamps, settings, and any deterministic seed. On load, validate ranges and IDs, migrate old schemas, compute offline gain once, record/clear the consumed interval, and save the post-award state so reloading cannot award twice.

Test:

- clean profile, normal save/reload, crash-window recovery, duplicate load, corrupted/missing fields, and old-version migration;
- local/cloud conflict with older/newer timestamps and a user-safe resolution policy;
- clock rollback, timezone/DST changes, huge forward jumps, cap boundary, and no-production state;
- offline summary semantics and exact credited amount;
- reset/prestige confirmation, retained bonuses, and inability to duplicate rewards;
- multi-purchase affordability and subtraction at numeric extremes.

## Balance evidence

Record target time-to-first-purchase, first automation, first meaningful choice, session-end milestone, and later walls. Compare them against deterministic simulations and several human sessions. Reject the economy when one obvious purchase dominates indefinitely, progress stalls without warning, rewards change only the number's formatting, or the player can ignore the core decision loop.

Community clicker demos in `evaluated-ecosystem.md` are learning fixtures, not production architecture. Their per-frame UI updates, hardcoded tiers, mixed numeric types, and absent save/offline contracts are specifically not defaults for this skill.
