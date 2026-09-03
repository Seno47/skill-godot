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

## Build the presentation loop before scaling the economy

An idle/clicker is unusually exposed to weak animation because the player watches the same actions hundreds of times. Before multiplying producers, upgrades, locations, or prestige tiers, build one representative scene-authored motion cell and pass `assets/production-motion-review.template.md`:

- one click/tap or direct action responds immediately and visibly;
- the acted-on object, worker, machine, vehicle, creature, or environment performs a readable cause -> work/contact -> result -> settle sequence;
- the reward is emitted and booked exactly once at the visible consequence rather than before the cause or after an arbitrary delay;
- one purchase creates an obvious visual and motion change, not only a faster number;
- one automation cycle runs without input and a dense state shows several simultaneous producers without robotic phase lock, collisions, or attention noise;
- pause/resume, speed-up, offline settlement, scene change, and repeated input leave every visual and transaction in a valid state.

Choose 2D, 2.5D, or 3D from the intended presentation, asset/animation pipeline, device budget, and the physical clarity the loop needs. Do not choose 2D only because static images are easier to generate, or 3D merely because a reference game uses it. The user-selected dimension wins. If believable turning, approach, depth contact, articulated machinery, or spatial transformation is central, prove that exact motion in the early slice before committing to the dimension.

Use [motion-and-animation.md](motion-and-animation.md) for motion direction, path/facing/contact rules, loop variation, target-build watchback, and the distinction between deterministic correctness and perceptual quality.

### Click feedback and repeated production

- Animate a presentation wrapper, not the authoritative economy value or container layout. Repeated clicks must accumulate economy transactions correctly without stacking uncontrolled tweens or leaving scale/rotation drift.
- Preserve one focal beat. Press response, acted-on object, reward flight/count-up, particles, camera response, and sound should form a causal sequence rather than six unrelated effects firing at once.
- Do not use the same scale-bounce/ease for the manual action, every producer, every purchase, every number, and every panel. Derive motion from material, weight, function, and hierarchy.
- Make frequent loops shorter and quieter than milestones. Vary phase, route, pose, or clip within bounded families; avoid both identical synchronized workers and per-frame random jitter.
- When production becomes fast, aggregate transactions and presentation. Blend into a continuous machine/conveyor/ambient state, batch number changes, and reserve distinct effects/audio for meaningful milestones instead of compressing one-shot animations into unreadable flashes.
- Keep animation density within the frame-time and visual-attention budget on the weakest target. Economy correctness does not excuse dropped frames, unreadable overlap, or hundreds of transient nodes.

### Travel, service, and factory loops

When the clicker shows agents, resources, orders, customers, or vehicles moving between stations, author route curves and stateful approach -> align -> work/transfer -> depart behavior. Facing follows the path with bounded turning; contacts use markers/sockets/slots; visible collision, shadow, wheel/foot motion, effect origin, and ownership remain aligned. Independent X/Y/Z tweens, translation without turning, endpoint rotation, teleporting resources, and effects that miss their work field are blocking defects even if throughput arithmetic is exact.

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

Community clicker demos in `evaluated-ecosystem.md` are learning fixtures, not production architecture. Their per-frame UI updates, hardcoded tiers, mixed numeric types, generic tween feedback, and absent save/offline contracts are specifically not defaults for this skill.
