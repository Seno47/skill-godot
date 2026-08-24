# Quest and Mission Systems

Read this for quests, missions, objectives, branching chains, contracts, achievements with progress, or other event-driven progression that survives scene changes.

## Separate definition, runtime state, and presentation

- Author immutable quest/objective/reward definitions as typed `Resource` assets with stable `StringName` IDs and localization keys.
- Store mutable accepted/active/completed/failed state as versioned primitive save data, not by mutating shared definition resources or serializing live nodes.
- Give one session/persistence owner responsibility for accept, progress, branch resolution, completion, failure, reward transaction, and save/load.
- Let enemies, items, dialogue, areas, and minigames emit domain events or talk to a narrow objective adapter. They do not hardcode quest completion/reward logic.
- UI observes the model and renders a tracker/journal scene. It does not poll the world every frame or compute completion independently.

Autoload is appropriate only when quest lifetime is genuinely cross-scene/global. In a bounded mode or one scene, a scene-owned service/resource can be clearer. Do not install a second global manager into an existing progression architecture.

## State and event contract

Define:

- allowed quest states and transitions;
- objective types, counters/sets/booleans, optional/hidden objectives, and completion policy;
- prerequisites, exclusivity, branches, timeout/failure/retry, abandonment, and repeatability;
- event schema and stable subject/context IDs;
- reward transaction ID and exactly-once policy;
- save version/migration and behavior for removed/renamed content;
- localization keys, plural rules, waypoint policy, and spoiler visibility.

Validate all IDs at content-load/editor time. Reject duplicate quest/objective IDs, missing prerequisite/branch targets, impossible requirements, and dependency cycles unless a cycle is deliberately repeatable and bounded. A progression graph can be modeled with flags and checked using `scripts/progression_graph_audit.py`.

Treat repeated or replayed events as normal: scene reconnects, save restore, rollback/network delivery, and duplicate signals must not increment an objective or grant a reward twice when the event has already been consumed. Connect/disconnect listeners with clear lifetime ownership.

## Exactly-once completion

A safe completion flow is:

```text
validate active state -> apply objective event -> detect completion ->
record completion/reward transaction -> delegate grants -> persist -> emit presentation events
```

The inventory/economy/stat system performs grants. The quest definition describes rewards but does not mutate those systems itself. If a grant fails, define whether the transaction retries, rolls back, or records partial fulfillment; do not emit a success screen while silently losing rewards.

## UI and wayfinding

- Track only information useful to the current decision. Offer journal/history/detail without filling the active HUD with every objective.
- Localize titles, descriptions, counters, singular/plural, branch choices, and failure reasons; test narrow layouts and hidden-objective reveal.
- Distinguish available, accepted, updated, complete-unclaimed, completed, failed, locked, timed, and optional states when they exist.
- Update world markers on objective/state change, not every frame. A marker needs off-screen/occlusion policy and must not reveal hidden content.
- Quest-giver dialogue reads the current state and dispatches actions through the owner rather than maintaining a separate copy.

## Verification matrix

- accept, duplicate accept rejection, progress, unrelated-event rejection, completion, and repeat policy;
- two objectives receiving the same event without cross-contamination;
- repeated event/connection/reload does not double progress or reward;
- save/reload while active, immediately before completion, after completion, and during timeout;
- prerequisite, exclusive branch, cancel/abandon, failure/retry, and removed-content migration paths;
- reward inventory-full/error behavior and exactly-once recovery;
- localized tracker/journal at zero/singular/plural/large counts and narrow viewports;
- waypoint changes, scene transitions, pause, and multiplayer/rollback ordering if applicable;
- independent playtest can understand the next objective without developer narration.

Useful primary references:

- [Godot resources](https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html)
- [Godot signals](https://docs.godotengine.org/en/stable/getting_started/step_by_step/signals.html)
- [Godot saving games](https://docs.godotengine.org/en/stable/tutorials/io/saving_games.html)
- [Godot internationalization](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)
