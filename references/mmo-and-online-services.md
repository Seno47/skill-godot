# MMO and Persistent Online Service Production

Read this for persistent shared worlds, accounts, authoritative cross-session characters/inventory/economy, zones/shards, many concurrent players, guild/chat/social systems, live operations, or an MMO claim. Also read [multiplayer-networking.md](multiplayer-networking.md), [progression-and-balance.md](progression-and-balance.md), and the relevant gameplay/genre references.

## Label the deliverable honestly

Choose and record one scope:

- **offline MMO-like prototype:** local simulation only; no online-service claim;
- **network prototype:** multiple clients and temporary server state; no durable production claim;
- **production slice:** real authentication, authoritative persistence, one representative zone/service path, deployment and failure evidence at a declared small capacity;
- **launch candidate:** broader security, operations, content, capacity, compliance, support, and recovery acceptance outside what a generic Godot skill alone can certify.

A large map, many NPC nodes, fake login, local JSON save, or two connected clients is not an MMO backend. Do not call a production slice horizontally scalable or launch-ready without measured evidence.

## Separate client, simulation, and services

Record the owner and trust boundary for:

- Godot client presentation, prediction, input, local settings, and cached non-authoritative data;
- authoritative zone/world simulation and interest management;
- identity/authentication/session issuance;
- character, inventory, currency, progression, mail/auction/trade, guild, and social persistence;
- matchmaking/directory/region selection;
- chat, moderation, abuse reporting, bans, and support tooling;
- telemetry, configuration, content/version rollout, and operational control.

Godot can run a headless dedicated server and can host authoritative session/world simulation. It does not make an autoload dictionary a durable distributed database, turn RPCs into secure service APIs, supply global matchmaking/identity/moderation, or guarantee cross-zone transactions. External services may use another runtime/database when that is the maintainable choice; preserve versioned contracts between them and Godot.

## Make durable mutations transactional

Every valuable mutation needs:

- authenticated account/character/session identity;
- server-owned preconditions and authorization;
- idempotency/transaction key;
- atomic or explicitly compensating changes;
- optimistic version/revision or another concurrency policy;
- retry and duplicate-delivery behavior;
- audit event without secrets;
- schema/content version and migration path.

Test currency/item transfer, loot settlement, purchase/craft, quest reward, mail/trade/auction, guild action, and zone handoff where applicable. A success response before durable commit, blind last-write-wins save, or client-generated final balance is blocking.

## Partition and reveal the world deliberately

Define zone/shard/instance ownership, player routing, stable entity IDs, transfer protocol, and failure boundary. For a handoff, prove source ownership release, destination acceptance, durable checkpoint, duplicate request handling, timeout/rollback/compensation, and reconnect to exactly one authoritative location.

Interest management is both performance and privacy/security. Each client should receive only the entities and fields it is allowed and needs to observe. Measure visible/replicated entities, update bytes, serialization time, server tick, and churn while players cross interest boundaries. Godot `MultiplayerSynchronizer` visibility can help within a suitable session topology, but it is not a complete global sharding architecture.

## Engineer operations as part of the product

Instantiate `assets/online-service-readiness.template.md`. For a production slice, require:

- reproducible client and authoritative server/service builds;
- environment/config/secret separation and least-privilege service identities;
- health/readiness signals and graceful drain/shutdown;
- structured logs, metrics, traces, build/protocol/content versions, and correlation IDs;
- capacity model plus load and soak at the declared concurrency;
- dependency latency/outage, process crash, restart, duplicate message, and partial-failure injection;
- backup plus measured restore, schema migration, rollback/forward-fix policy, and declared RPO/RTO;
- deployment/rollback or safe staged rollout evidence;
- rate limiting, abuse controls, moderation/support path, and data-retention/privacy review appropriate to the audience/regions.

Do not put credentials, signing secrets, database passwords, or administrative authority in the client/PCK. Do not log auth tokens, personal data, chat secrets, or payment payloads. Legal/privacy/child-safety compliance requires project-specific qualified review; the skill records the unresolved boundary instead of declaring compliance.

## Scale with a workload model

Declare concurrent users per zone/process, active entities, interest set, action rates, persistence writes, chat/social traffic, payload sizes, tick target, memory, network egress, database/service latency, and headroom. Test representative busy states, not idle sockets. Distinguish:

- functional concurrency (several users can connect);
- declared-capacity load (budgets pass);
- soak (state/memory/connection stability over time);
- failover/recovery (service returns without duplication or split ownership);
- fleet/global scale (outside a single-process test).

Extrapolation from ten bots to thousands is a hypothesis, not evidence. Record what ran, where, for how long, with which build/config/data, and what was intentionally mocked.

## Human and independent acceptance

The builder owns routine correctness, load tooling, failure injection, and artifact collection. Use an independent architecture/operations review for trust boundaries, data ownership, transaction semantics, capacity assumptions, failure modes, observability, backup/restore, deployment, and honest scope. Also perform real concurrent human play for client experience and network feel.

An MMO production slice remains blocked if authentication is fake, authoritative persistence is local-only, backup restore is unmeasured, zone/interest behavior is untested, load evidence is absent, or operational/security review is self-awarded. If those systems are intentionally mocked, label the result network/MMO-like prototype rather than production-ready.
