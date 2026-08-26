# Replay, Ghost, Spectator, and Determinism

Read this when the game records inputs, replays matches/runs, displays ghosts, supports rollback/spectators, or uses deterministic traces as a player-facing feature.

Declare the authoritative recorded data: input commands, semantic decisions, state snapshots/deltas, RNG stream states, external outcomes, tick rate, build/content/schema versions and checksum cadence. Godot physics is not guaranteed deterministic; do not promise cross-machine physics replay from input alone unless the project has replaced or bounded every nondeterministic dependency and proved it on target hardware.

Separate authoritative replay state from rendering/interpolation. Test render caps, pause/seek/speed changes, save/load boundaries, late join/spectator catch-up, ghost non-interference, corrupted/truncated data, old-version rejection or migration, and divergence reporting. A replay must fail explicitly at the first checksum mismatch rather than continue as plausible fiction.

Use `assets/replay-contract.template.json`, run `scripts/replay_probe.py`, and complete `assets/replay-review.template.md`. Human/independent playback review still checks camera, controls, timeline comprehension and whether results match the remembered event.

Primary Godot references:

- [Physics introduction](https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html)
- [Physics interpolation introduction](https://docs.godotengine.org/en/stable/tutorials/physics/interpolation/physics_interpolation_introduction.html)
