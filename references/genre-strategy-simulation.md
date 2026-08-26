# Strategy, Management, and Simulation Games

Read this when the player commands multiple actors, manages production/logistics, advances simulation time, or makes decisions over a long-running world. Apply [progression-and-balance.md](progression-and-balance.md), [game-ai-and-navigation.md](game-ai-and-navigation.md), and [save-data-integrity.md](save-data-integrity.md) where relevant.

## Separate simulation from presentation

Use one authoritative fixed-step or event-scheduled model for resources, tasks, combat, production, and time. UI, animation, audio, particles and selection outlines observe model events; they do not become the only owner of timers or outcomes. Record tick rate, time-scale levels, pause semantics, deterministic seed/version, command ordering, and maximum supported entities/jobs.

Commands need stable actor/target IDs, issue tick, validation, ordering and cancellation policy. Test selection/control groups, queued orders, build placement, reservations, resource debit/rollback, destroyed or changed targets, fog/visibility permissions, pause/unpause and rapid time-scale changes.

## Prove systems under pressure

Use `assets/strategy-simulation-review.template.md` and target-build traces for:

- early, mid and late economies with multiple viable openings;
- mass selection and command dispatch at entity capacity;
- path congestion, formation breakup, job reservation and deadlock recovery;
- construction/production completion exactly once across pause/save/load;
- speed 1×/maximum/pause producing the same authoritative result where intended;
- long-session drift, numeric bounds, memory growth and UI update cost;
- defeat, recovery/comeback and completion without a soft lock.

The strategy gate fails when a tiny demonstration is extrapolated to promised entity counts, the UI requires inspecting every unit individually, one opening dominates, simulation changes while paused, or higher time scale changes economic/combat results beyond declared tolerance.

