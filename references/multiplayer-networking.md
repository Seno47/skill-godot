# Networked Multiplayer Production

Read this for online co-op, competitive sessions, peer-hosted play, dedicated servers, rollback, synchronized persistent state, matchmaking/lobbies, reconnect, or a Web multiplayer target. Local same-device multiplayer does not need this layer unless it shares the network simulation path.

## Lock the network contract before gameplay spreads

Start from `assets/network-contract.template.json`. Record:

- supported platforms, client count, session duration, region assumptions, and cross-play scope;
- topology: listen server, peer-to-peer, relay, dedicated authoritative server, or custom backend;
- transport per platform and why its latency/reliability/security properties fit;
- simulation tick, snapshot/send rates, interpolation delay, prediction/reconciliation or rollback boundary;
- authority owner for movement, combat, inventory, rewards, match result, time, AI, and world state;
- authentication/session-ticket boundary and behavior before authentication completes;
- spawn/despawn, late join, scene transition, reconnect, host loss, version mismatch, and shutdown behavior;
- bandwidth, server tick, state-error, recovery-time, and target-client budgets;
- persistence owner and idempotency key for every durable transaction.

Do not add networking as a final serialization pass over a finished single-player architecture. Decide which state is authoritative, predicted, interpolated, cosmetic, durable, and private before implementing the dependent systems.

## Keep one authority per fact

For competitive or persistent play, treat all client input and client-reported state as untrusted. Prefer client intent/input sent to an authority that validates and applies the result. The server owns gameplay-critical position, hit results, cooldowns, inventory, currency, extraction/mission settlement, and match outcome unless the brief explicitly chooses a weaker trust model and records its risk.

Authority is not the same as node ownership or local responsiveness. A client can predict its movement and immediately play provisional presentation while the server remains authoritative. Reconciliation must correct state without double-applying damage, inventory changes, audio, VFX, achievements, or rewards.

Inventory every remotely callable surface:

- allowed caller and authentication state;
- authority and target object/identity;
- type, range, ownership, cooldown, sequence/version, and state-transition validation;
- replay/idempotency protection for durable actions;
- rate and payload-size limits;
- failure response and security logging without secrets.

An `@rpc("any_peer")` annotation is an entry point, not permission to trust its arguments. Use the remote sender identity inside the call and resolve server-owned player/account state from that identity rather than accepting a client-supplied owner ID.

## Use Godot replication deliberately

Godot's high-level `MultiplayerAPI`, RPCs, `MultiplayerSpawner`, `MultiplayerSynchronizer`, and `SceneReplicationConfig` are useful when their scene-tree and authority model fit. Preserve stable scene paths/names for RPC peers. Author spawnable scenes and replication configuration visibly where practical.

- Spawn and despawn through the authority. A locally created lookalike node is not replicated truth.
- Synchronize the minimum gameplay state needed by each peer, not whole characters/resources by habit.
- Use visibility filters/interest rules so peers do not receive every entity in a large world.
- Do not attempt to synchronize `Resource`, RID, instance ID, or other peer-local object identity as portable state; serialize stable IDs and primitive/value data.
- Separate frequent homogeneous streams from reliable transactions. Chat, inventory, match settlement, and movement should not head-of-line block one another.
- Record transfer mode and channel for every replicated stream. Reliable-every-frame transforms are a red flag unless measured and justified.

## Choose responsiveness explicitly

Select only the techniques required by the game:

- **Interpolation:** render remote snapshots behind real time; test missing/out-of-order snapshots and teleports.
- **Client prediction + reconciliation:** retain numbered inputs/state history, acknowledge authoritative ticks, replay unacknowledged input, and bound visible correction.
- **Lag compensation:** rewind only authoritative query state needed for the action, bound the history/window, and prevent clients choosing arbitrary timestamps.
- **Rollback:** snapshot deterministic gameplay state, exchange inputs, resimulate, hash states, and deduplicate presentation. Do not claim rollback because a state can be serialized once.
- **Lockstep/turn-based:** define command ordering, timeout, reconnect/catch-up, deterministic random seeds, and version compatibility.

If none is needed, do not add it. A slow cooperative or turn-based game may prefer simpler reliable commands and server snapshots.

## Test the real lifecycle

At minimum, exercise separate processes or exported instances for:

1. server boot/listen and clean shutdown;
2. authentication rejection and success;
3. connect, spawn, initial snapshot, and normal concurrent play;
4. late join while state is already changing;
5. duplicate, stale, reordered, oversized, unauthorized, and over-rate requests;
6. declared latency, jitter, and packet loss during the densest supported interaction;
7. abrupt client disconnect and reconnect/catch-up;
8. server/host loss and the declared recovery or honest session-failure UI;
9. scene/round transition and repeated rematch without leaked peers or duplicate handlers;
10. version/protocol mismatch;
11. durable transaction retry and save/service outage;
12. target client count, server tick, bandwidth, and interest-set load.

Loopback proves wiring, not Internet behavior. One process containing sibling client/server APIs is useful for deterministic tests but cannot alone prove process isolation, transport, port binding, authentication, packaging, timing under load, or reconnect.

Run the declared trace audit:

```bash
python <skill-dir>/scripts/network_contract_probe.py --model reports/network-contract.json --summary --json-output reports/network-contract-audit.json
```

The probe checks the declared authority surface, scenario coverage, hostile-input rejection, impairment profile, convergence, reconnect, dedicated-server behavior, persistence idempotency, interest management, capacity budgets, and Web transport contract. Its input must come from the tested build/processes; fabricated rows do not become runtime evidence.

## Dedicated servers and Web

For a dedicated topology, export and run a real server artifact. Godot supports headless execution and a dedicated-server resource export mode; confirm the server is not silently treated as a player, client-only resources are absent or safely stripped, required resources still load, signals/logs flush, and shutdown/restart preserves the declared transaction boundary.

For Web, do not assume desktop ENet/UDP works in the browser. Record WebSocket or WebRTC/custom service architecture, TLS/signaling/relay needs, browser lifecycle, background-tab behavior, origin/auth policy, and native compatibility. WebSocket is suitable for reliable bidirectional messaging but may be a poor fit for fast real-time state; WebRTC requires signaling and may require relay infrastructure. Validate the actual deployed origin, not only localhost.

## Human multiplayer acceptance

Builder-owned probes must catch routine authority, lifecycle, desync, duplication, performance, and packaging failures. Then use `assets/networked-multiplayer-review.template.md` for uncoached concurrent human play from separate endpoints. Review communication, readability, perceived delay, correction, fairness, teammate/opponent identity, disconnect messaging, and recovery. The user is not the default network QA operator.

Do not call a networked game complete when only one client, loopback, perfect network, host-only behavior, or editor runs were tested. If external services, ports, accounts, regions, relays, or consoles are unavailable, mark those states `NOT TESTED` and narrow the claim.

Primary Godot references:

- [High-level multiplayer](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html)
- [MultiplayerSpawner](https://docs.godotengine.org/en/stable/classes/class_multiplayerspawner.html)
- [MultiplayerSynchronizer](https://docs.godotengine.org/en/stable/classes/class_multiplayersynchronizer.html)
- [Dedicated-server export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html)
- [WebRTC](https://docs.godotengine.org/en/stable/tutorials/networking/webrtc.html)
- [WebSocket](https://docs.godotengine.org/en/stable/tutorials/networking/websocket.html)
