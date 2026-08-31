# Game AI and Navigation

Read this when non-player actors perceive, decide, navigate, fight, cooperate, flee, work, or simulate off-screen. A behavior tree, state-machine node, navigation path, or animation transition does not prove believable or fair behavior.

## Contract observable behavior

Start from `assets/ai-navigation-contract.template.json`. For each production archetype record:

- goals, states and legal transitions;
- sensed facts, ranges, occlusion, memory, uncertainty, faction/ownership and update cadence;
- path owner, locomotion types, traversal links, dynamic obstacle and unreachable-target policy;
- decision/reaction/telegraph budgets and which information AI is forbidden to read;
- group coordination, reservation/formation/crowd limits and anti-dogpile rules;
- off-screen level of detail, sleeping/wake rules and persistence boundary;
- target actor counts plus CPU/path-query/memory budgets.

AI should act on an authored perception model, not raw access to player input, hidden inventory, exact aim, or future random results unless the game explicitly communicates that power. Difficulty may change timing, tactics, resources, accuracy, coordination, or mistake rate within declared limits; it should not quietly bypass the rules taught to the player.

## Separate deciding, moving, and presenting

Keep authoritative state/decision logic separate from navigation requests, physical locomotion, animation/audio/VFX, and UI markers. The same state transition should not be triggered independently by animation completion, collision, timeout, and perception without an explicit arbiter.

Godot navigation changes are synchronized with the navigation server rather than always becoming visible in the same script instant. Avoidance is local motion steering, not pathfinding or physics collision. Test the actual order used by the production actor: request/update path, set desired velocity, receive safe velocity when used, move through physics, and recover when the map or target changes.

## Test adversarial spaces and timing

Exercise authored fixtures and real levels for:

- perception just inside/outside distance and field-of-view boundaries, partial occlusion, sound/memory expiry and reacquisition;
- spawn/idle/patrol, chase, attack telegraph/commit/recovery, disengage and return;
- narrow doors, corners, slopes, drops, jump/climb links, moving obstacles and multiple locomotion maps;
- blocked route and replan, unreachable or deleted target, actor displacement/teleport and nav-map rebake/update;
- repeated failure against the same facade/obstacle: first recovery side blocked, next attempt changes candidate or proves a changed/revalidated environment, then recovers or escalates within a declared budget;
- crowd crossing, doorway contention, formation break, priority agents and deadlock recovery;
- pause/time-scale/save-load/scene transition without decision or cooldown drift;
- off-screen sleep/wake and target-capacity load.

Run:

```bash
python <skill-dir>/scripts/ai_navigation_probe.py --model reports/ai-navigation-contract.json --summary --json-output reports/ai-navigation-audit.json
```

The probe checks archetype/scenario coverage, fairness boundaries, perception results, route/replan/unreachable handling, repeated-recovery candidate memory, stuck/deadlock counts, telegraph/reaction budgets, pause stability, off-screen cadence, and capacity performance. It does not certify fun, personality, tactics, animation quality, or whether the player can read intent.

Stuck recovery must be stateful. Record the obstacle/environment revision, attempted side/waypoint, selection basis, measured progress and terminal recovery/escalation. A stable instance-ID hash that chooses the same blocked side after every no-progress timeout is a loop, not recovery. Retain failed candidates for the current geometry revision, prefer an untried valid candidate, and cap attempts before a declared replan, backtrack, safe reset or target abandonment. A candidate may be retried only after the relevant geometry/path state changed and was revalidated. Run the sequence through the production movement/physics path against an adjacent facade, not by directly invoking the selector.

## Human-facing acceptance

Complete `assets/ai-navigation-review.template.md` with raw normal and crowded target-build motion. Review whether intent is legible before consequence, actors look purposeful rather than jittery, failure recovery is plausible, allies do not obstruct the player, enemies do not attack through geometry, navigation matches visible collision, and higher difficulty remains fair.

Primary Godot references:

- [Using NavigationServer](https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_using_navigationservers.html)
- [NavigationServer2D](https://docs.godotengine.org/en/stable/classes/class_navigationserver2d.html)
- [Using NavigationAgents](https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_using_navigationagents.html) documents that navigation supplies path state while the project remains responsible for physical movement and its recovery behavior.
