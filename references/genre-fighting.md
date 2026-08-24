# Fighting Game Production

Read this for traditional fighters, platform fighters, arena fighters with frame-defined combat, or combat systems that require buffered commands, cancels, hit/hurt boxes, trades, and deterministic replay. Do not force these rules onto ordinary action combat.

## Lock the combat contract

Record before implementation:

- subgenre, player count, local/online/AI scope, target devices, and supported refresh rates;
- simulation tick rate and separation from rendered frame rate;
- movement space, facing/cross-up rule, camera/arena bounds, push interaction, and round flow;
- input vocabulary, buffer/leniency policy, simultaneous-opposite-direction policy, rebinds, deadzones, and motion commands;
- authoritative timing source for move phases and animation;
- hit, block, armor, throw, projectile, invulnerability, clash/trade, hitstop, knockdown, wake-up, combo, cancel, meter, and timeout rules that actually exist;
- netcode model and determinism boundary if online play is in scope.

Do not import community frame numbers or a universal damage-scaling formula as design truth. Store tunable move/balance definitions in typed `Resource` assets and validate the roster against the intended pace.

## One deterministic simulation authority

Advance combat rules on a fixed simulation tick. Rendering, interpolation, particles, and presentation may run independently. Capping `application/run/max_fps` is not a substitute for a fixed combat step and may harm high-refresh presentation.

Choose one source of truth:

- **frame-data authoritative:** integer phase counters drive startup/active/recovery/cancels and manually or deterministically advance matching animations; or
- **animation authored:** animation tracks/events define volumes and phase markers, while a fixed-tick combat controller consumes those markers deterministically.

Do not let a free-running `AnimationPlayer`, timers, awaits, and a second frame counter all decide whether a move is active. Snapshot/replay tests must observe the same phase and boxes at the same simulation frame.

If rollback is required, keep rollback state small, serializable, and free from untracked SceneTree side effects. Exchange inputs, not arbitrary rendered-node state. Use deterministic randomness, explicit update order, rollback-safe audio/VFX deduplication, state hashes, and rollback-window/load tests. UDP/ENet or a rollback addon may be appropriate, but online architecture and dependencies require an explicit user/project decision.

## Authored fighters and collision volumes

A fighter should remain an editable scene with separate authored presentation and gameplay volumes. Typical reusable parts include:

- body/movement root and push box;
- visuals/animation subtree that can face independently without flipping the entire physics hierarchy;
- hurt boxes, hit boxes, throw/proximity/sensor volumes, and debug visualization;
- move set, frame data, cancel table, and balance resources;
- input/history component and explicit state machine;
- presentation hooks for hitstop, camera, VFX, audio, rumble, HUD, and training data.

Author and scrub volume changes in the editor/animation timeline or through an editor tool. Runtime boxes must match the captured frame-data view.

`Area2D` signals, overlap polling, and direct-space shape queries are implementation choices, not dogma. Choose a path whose same-tick ordering, filtering, multi-hit suppression, simultaneous hits, and rollback behavior are understood and tested. Never assume node presence proves frame-accurate resolution.

## Input and state rules

- Capture a timestamped/directional input history at the simulation boundary.
- Define buffer length, diagonal interpretation, charge duration, negative-edge behavior, priority, consumption, and leniency per command family.
- Read actual remapped actions and test keyboard ghosting constraints plus representative controllers.
- Make state transitions explicit for neutral, movement, attack phases, hit/block stun, knockdown, throw, armor, invulnerability, round transition, and pause states that exist.
- Define cancel windows/hierarchy in data; do not scatter special-case `if` chains across animations and fighter scripts.
- Resolve exactly once per attack/target according to the multi-hit rule. Define order for hit, block, trade, KO, meter, combo, hitstop, sound, and VFX.

## Verification matrix

At minimum, create deterministic project fixtures for:

- identical seeded input script twice -> identical per-frame state hashes;
- neutral movement, facing swap/cross-up, arena edge, and push-box interaction;
- input pressed early inside/outside the buffer window;
- quarter-circle/charge/sequence success plus near-miss rejection on each supported device;
- startup/active/recovery boxes at boundary frames;
- hit, block high/low, whiff, armor/invulnerability, throw, projectile, trade/clash, and multi-hit suppression as applicable;
- legal/illegal cancel boundaries and combo reset/scaling;
- hitstop without lost input or double-fired presentation;
- timeout, KO, round reset, pause/resume, input reconnect, and training reset;
- rollback resimulation, state restore, late input, and desync detection when online is in scope.

Hands-on review must assess input latency, motion leniency, animation/box alignment, hit readability, controller deadzones, round pace, and audio impact. Structural frame data alone cannot pass playability.

## Framework selection

Consult `evaluated-ecosystem.md` before adopting FightEngine, Fray, rollback demos, MUGEN-related code, or combat templates. For release work, an alpha framework needs a pinned revision, license/dependency record, project-owned adapter boundary, removal plan, and tests covering every used feature. Do not install several overlapping combat/state/input systems together.

Useful primary references:

- [Godot idle and physics processing](https://docs.godotengine.org/en/stable/tutorials/scripting/idle_and_physics_processing.html)
- [Godot input](https://docs.godotengine.org/en/stable/classes/class_input.html)
- [PhysicsDirectSpaceState2D](https://docs.godotengine.org/en/stable/classes/class_physicsdirectspacestate2d.html)
- [AnimationMixer](https://docs.godotengine.org/en/stable/classes/class_animationmixer.html)
- [Godot resources](https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html)

