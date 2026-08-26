# Metroidvania Production

Read this for ability-gated exploration, interconnected rooms/regions, persistent world changes, backtracking, map revelation, and traversal abilities that unlock routes. A platformer with linear stages does not need this architecture.

Also apply [progression-and-balance.md](progression-and-balance.md) when ability/reward cadence, build choices, currency, power growth, or difficulty escalation are material. A graph can be reachable and soft-lock-free while its reward, return-traversal, or challenge pacing is still poor.

## Define the world/progression contract

Before detailed level art, record:

- world regions/rooms and directed connections, including one-way edges, drops, lifts, warps, and fast travel;
- stable room, transition, spawn, gate, collectible, boss, shortcut, and save-point IDs;
- initial abilities/flags, every ability grant, every hard/soft gate, and required ending nodes;
- player state that persists across rooms and world state that persists across sessions;
- map/fog representation, camera transition model, loading strategy, and recovery/save policy;
- how each ability changes traversal, combat, or both; how it is taught before punishment;
- landmarks, optional rewards, shortcuts, and how returning through old areas becomes meaningfully different or faster.

Store world/ability definitions as editable resources and rooms as authored scenes. Keep runtime save state separate from immutable definitions. Room scripts may expose stable local events; they must not become competing owners of global progression.

Represent the planned topology in a small JSON graph and audit it before art lock:

```bash
python <skill-dir>/scripts/progression_graph_audit.py \
  --graph <world-graph.json> --summary \
  --json-output <reports/world-graph.json>
```

The graph is a model, not proof of physical playability. It catches unreachable required nodes, impossible flag prerequisites, unused transitions, declared escape traps, and obvious dead ends; the real room collision, spawn, camera, and save flow still need playtests.

## Ability gates and teaching

- A hard gate must query a stable ability/flag registry rather than a free string embedded in the room.
- Distinguish information gates, skill gates, resource gates, and ability gates; do not label every obstacle a lock-and-key.
- Teach a traversal ability in a safe authored space, confirm mastery, then combine it with hazards or combat.
- Avoid one-purpose abilities unless the brief intentionally calls for them. Prefer abilities that create new routing/decision possibilities, not just colored doors.
- Prevent sequence breaks only where they harm the design; if an advanced technique is allowed, define its persistence/spawn consequences and test it.

Every reachable one-way transition marked as requiring escape must have a route to a declared safe node using abilities the player can obtain from that state. Test death/respawn and save/reload on both sides of gates so a legal save cannot become a permanent trap.

## Persistence and room lifecycle

Use versioned save data keyed by stable IDs for abilities, opened gates, collected items, defeated bosses, visited/revealed cells, shortcuts, spawn/save location, and other required state. Do not serialize live room nodes or mutate one shared definition resource as per-save state.

On room entry:

1. Resolve the stable entry/spawn ID.
2. Apply saved world state before it becomes interactable/visible where needed.
3. Restore player/camera/input state without a one-frame wrong spawn or flash.
4. Prevent duplicate reward/event connections.
5. Make departure/loading ownership explicit and cancel stale requests.

Use synchronous loads for small measured transitions when they meet the hitch budget. Use `ResourceLoader.load_threaded_request()` when measured loads would block, and poll status before `load_threaded_get()` so retrieval does not unexpectedly block. Never manipulate the SceneTree from a worker thread.

## Map, backtracking, and space

- Use integer/grid identifiers where the map is cell-based; keep map coordinates distinct from rendered world floats.
- Landmarks, lighting, silhouettes, room shapes, and biome transitions should help form a mental map before a waypoint layer does all orientation work.
- Remote or difficult optional routes need a meaningful reward, revelation, shortcut, encounter, or authored story beat.
- Backtracking should change through new movement, shortcuts, enemies, routing, or discoveries. Repeating the same corridor unchanged is not progression.
- Preserve camera bounds and transition readability. Test high-speed entry, reverse entry, death during transition, and rapid room changes.

## Verification matrix

- graph audit passes for required nodes/flags and declared escape states;
- clean start reaches the first teach/grant/gate loop without narration;
- each ability grant persists through room change and reload;
- every gate is closed before and open/usable after its condition;
- collectibles, bosses, switches, and shortcuts do not respawn/reward twice unless designed to;
- save/load on both sides of one-way transitions and gates cannot softlock;
- death/respawn never selects an unreachable spawn;
- sequence breaks and fast travel preserve world state;
- threaded transition cancellation/failure and synchronous hitch budgets are tested as applicable;
- map/fog reveal, hidden rooms, localization, and controller/touch navigation remain correct;
- old-route return time/experience is assessed after relevant movement unlocks.

Useful primary references:

- [Godot background loading](https://docs.godotengine.org/en/stable/tutorials/io/background_loading.html)
- [Godot saving games](https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html)
- [Godot resources](https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html)
- [Godot groups](https://docs.godotengine.org/en/stable/tutorials/scripting/groups.html)
