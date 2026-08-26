# From Game Brief to Buildable Slice

Use this guide when the user's description is open-ended, genre-heavy, or visually ambitious. Do not replace the user's idea with a stock genre template.

## Match collaboration to the brief

Read how the task is framed. An exploratory direction benefits from an early playable slice and short checkpoints only at decisions of taste, scope, platform, or paid cost. A finished brief authorizes reasonable reversible implementation choices and steady autonomous progress; do not turn it into a sequence of avoidable questions. Neither mode changes permission boundaries or weakens completion evidence.

For a run likely to span several phases or context compaction, instantiate `assets/project-run-state.template.md`. Keep current playable truth, durable decisions, build/evidence IDs, reproducible commands, asset/cost records, next bounded actions, and genuine blockers there. Update it in place after meaningful checkpoints; a chronological diary wastes context and quickly becomes stale.

## Extract decisions that affect construction

Capture what the user has actually specified:

- player promise/fantasy in one sentence and the target feeling during ordinary play;
- primary verb and core repeated action;
- 2D, 3D, or hybrid presentation;
- camera/projection and how the player reads space;
- target platform, input devices, orientation, and performance class;
- solo/local/online structure if relevant;
- world topology: rooms, scrolling levels, arenas, tracks, open regions, boards, or generated spaces;
- important actors, interactables, hazards, objectives, progression, and failure/recovery;
- immediate/core loop (roughly seconds), longer progression loop (roughly minutes), and fast retry/recovery loop;
- player decisions and pressure, what a more skilled player does differently, and how the next decision stays readable;
- first representative level/encounter: start, first decision, first reward, first threat, landmark, escalation, and recovery beat;
- for a finite selector with many levels/missions/items, the navigation model (`scroll`, `pages`, `chapters`, search/filter, or a deliberate combination), chosen from content volume, comparison needs, resume position, and mobile reachability rather than habit;
- visual references, exclusions, mood, palette, density, and animation character;
- production characters expected to move and their smallest required idle/locomotion/context-action state set; do not infer that a rigged/imported character is acceptably animated;
- sonic references and exclusions, music/ambience role, important audible feedback, voice needs, and whether generative audio is allowed;
- requested deliverable: experiment, vertical slice, level, system, content pass, polish pass, or finished build.
- explicit non-goals that prevent the slice from quietly expanding into unrelated systems.

Translate the brief into one base rubric case plus every material modifier instead of choosing one genre label. For example, an online extraction shooter with progression, Russian/English release, replay and a reproducible Windows pipeline composes those cases with `+`; its applicable gates are the union and its score floors are the maximum for each dimension. Run `scripts/rubric_case_plan.py` before scaffolding evidence so the plan, loaded references and acceptance owners are explicit without reading every guide.

If the requested deliverable includes a duration, finite level/chapter count, or “complete game” claim, make the scope measurable before bulk authoring. Instantiate `assets/content-duration-contract.template.md` and map the claim to authored puzzle/objective count, mechanic introductions and meaningful permutations, estimated first-solve time, and later uncoached playtest evidence. Keep tutorial, menus, retries, grind, replay, and procedural/unbuilt assumptions separate. Never let a strong short slice silently inherit the duration claim of the intended future game.

If persistent progression, upgrades/builds, rewards/resources, or escalating challenge materially shape the game, define their budgets before multiplying content. Read [progression-and-balance.md](progression-and-balance.md), adapt `assets/progression-balance.template.json`, and choose representative player archetypes plus early/mid/late checkpoints. Do not let level count, one optimal autoplay, or designer familiarity stand in for option viability, source/sink health, recovery, and uncoached pacing.

If state survives a run, level, profile, device, or app update, define the save envelope, stable IDs, ownership, migration support, atomic commit/recovery policy, reset scope, and applicable cloud conflict rule before multiple systems depend on it. Read [save-data-integrity.md](save-data-integrity.md) and adapt `assets/save-data-contract.template.json`; serialization format choice alone does not prove integrity.

If spaces, encounters, loot, quests, or populations are procedural, declare generator/version identity, named random streams, seed policy, solvability invariants, retry/fallback bounds, distribution budgets, regression seeds, and save/resume semantics. Read [procedural-generation.md](procedural-generation.md) before bulk content. A random seed is a debugging handle, not evidence that outputs are fair, varied, or presentable.

If NPCs or enemies perceive, navigate, choose, coordinate, or simulate off-screen, define their legal information, perception boundaries, behavior states, navigation/replan/failure policy, telegraph budget, tick cadence and actor-capacity target. Read [game-ai-and-navigation.md](game-ai-and-navigation.md); include representative failure and crowd states in the first slice instead of validating only a quiet successful route.

If the brief promises keyboard/mouse, controllers, touch, multiple local players, remapping, subtitles/captions, reduced motion/flash/shake, non-color cues, hold/toggle alternatives, or assists, record the actual device/action/accessibility contract. Read [input-and-accessibility.md](input-and-accessibility.md). Settings and glyphs must follow real behavior, hot-plug/focus lifecycle, and player ownership.

Route strategy/simulation work through [genre-strategy-simulation.md](genre-strategy-simulation.md); vehicle/racing through [genre-vehicles-racing.md](genre-vehicles-racing.md); shooter/action combat through [genre-shooter-action.md](genre-shooter-action.md); and dialogue/cinematics through [narrative-dialogue-cinematics.md](narrative-dialogue-cinematics.md). These guides add specialized correctness and feel contracts without replacing the base scene, art, audio, input, save, performance, or accessibility workflow.

If the game is networked, decide the maximum concurrent players per session/zone, host or dedicated topology, supported client/server platforms, compatible transport, authority and trust boundaries, authentication, reconnect policy, simulation/update rates, latency/jitter/loss budgets, persistence ownership, and capacity target before building dependent mechanics. Read [multiplayer-networking.md](multiplayer-networking.md) and adapt `assets/network-contract.template.json`; do not infer “multiplayer” means peer-hosted, authoritative, rollback, or MMO scale.

For extraction, separately define raid state, durable stash state, loadout commitment, secure/insurance rules, voluntary extraction, death/disconnect settlement, retry idempotence, route risk/reward, and recovery from a bad run. Read [genre-extraction.md](genre-extraction.md). For an MMO or persistent online world, record an honest scope label and the real service/operations boundary using [mmo-and-online-services.md](mmo-and-online-services.md); unbuilt backend, moderation, capacity, restore, or deployment work is a limitation, not implied future evidence.

For fixed-camera isometric/orthographic complete work, also schedule the early rendered art gate from `assets/isometric-complete-review.template.md` before multiplying levels. This is a production decision: hero, mechanism states, objective, representative decor, lighting, and UI must coexist readably at the actual gameplay camera first.

When a focal production character is expected to move, schedule the builder-owned `assets/production-character-motion.template.md` contract before release. This is routine implementation acceptance, not a preference question for the user: idle, locomotion, required actions, real dispatch, bind/rest-pose rejection, and animated attachments must be proved in the target build.

For a portal/web release where advertising is available, record `ads: none | conservative | aggressive-but-compliant` before designing the flow. If the brief does not decide and ads would change menus, pauses, rewards, or progression, ask once rather than inferring a policy. Record where game-initiated interstitials and banners may appear and what voluntary reward, if any, justifies rewarded video. Platform-controlled advertising is distinct from game-initiated calls.

If delivery includes a store/platform release rather than only a local export, record the exact platforms, stores, package identity, signing, SDK features, install/update path, supported input/display/lifecycle cases, old-save compatibility, upload scope, and rollback route using [platform-release-and-stores.md](platform-release-and-stores.md). If mods or UGC are in scope, separately declare accepted content types, trust tier, override namespace, executable-code policy, distribution rights/moderation and removed-content save behavior using [modding-and-ugc.md](modding-and-ugc.md).

Do not interrogate the user for fields that are irrelevant to the requested slice. If no target resolution or input scheme is given, choose a reversible project default appropriate to the described platform and state it briefly.

For a complete game or vertical slice, make audio part of the buildable contract from the start. Define the music/ambience states, must-hear gameplay and UI events, mixer/settings expectations, source/rights policy, and explicit audio exclusions. Production audio is required unless the user requests a silent experience or clearly labels the deliverable as a non-production prototype. Read [audio-vfx-fonts.md](audio-vfx-fonts.md) before sourcing or integrating it.

## Convert nouns into authored artifacts

Map stable concepts to native Godot artifacts before writing behavior:

| Brief concept | Likely artifact |
| --- | --- |
| Player, enemy, projectile, pickup, door, vehicle | Reusable scene with focused behavior |
| Level, room, arena, menu, encounter | Composition scene instancing reusable scenes |
| Weapon stats, unit definition, item data, biome palette | Typed `Resource` and `.tres` instances |
| Visual skin shared across UI | `Theme` and related resources |
| Cross-scene save/session/service | Small autoload only when lifetime is truly global |
| Repeated authored geometry | Instanced scene; `MultiMesh` when scale requires it |
| Generated dungeon, crowd, loot roll, terrain chunk | Data-driven runtime system with deterministic inputs when useful |

This mapping is a hypothesis. Adjust it to existing project architecture and the ownership/lifetime of each concept.

## Slice by experience, not by department

A useful slice contains a narrow amount of every layer needed to judge the experience:

- one representative playable space;
- the core input and feedback loop;
- representative player and world visuals;
- camera, lighting, production audio, effects, and UI needed to read the loop;
- failure/success or another clear state transition;
- enough content variation to expose whether the architecture generalizes.

Avoid implementing ten invisible systems before the first representative scene exists. Also avoid creating a beautiful diorama that cannot demonstrate the requested interaction.

Before investing in final art, greybox the representative space and reject the design if the first playable section has no real decision, the main mechanic can be ignored, the objective/failure is understandable only from developer narration, or the space is decorative rather than decision-shaping. Introduce one new concept at a time, combine understood concepts, and include recovery after high-pressure beats unless the brief deliberately rejects that pacing.

## Adapt without genre assumptions

Derive architecture from behavior and lifetime rather than labels such as RPG, shooter, simulator, strategy, or puzzle. Two games in the same genre may require opposite scene structures.

Examples of questions to answer from the brief or project evidence:

- Does the camera follow one actor, frame an arena, move on rails, or remain user-controlled?
- Are game objects independently reusable, or meaningful only as part of one authored level?
- Is the space authored, generated, streamed, or some combination?
- Does simulation continue off-screen?
- Is UI informational, diegetic, spatial, modal, or editor-like?
- Which data must persist across a scene change?

Only ask the user when competing answers would produce materially different work and no project evidence resolves them.

## Preserve user authorship

- Treat examples and references as constraints, not permission to copy copyrighted work.
- Do not invent monetization, progression, narrative, multiplayer, live services, or scope expansion.
- Do not normalize unusual art direction into generic fantasy, cyberpunk, cozy, low-poly, or pixel-art conventions.
- If a requested visual is infeasible with available tools, keep the design intent and propose the smallest honest substitution.
