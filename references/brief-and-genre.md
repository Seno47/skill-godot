# From Game Brief to Buildable Slice

Use this guide when the user's description is open-ended, genre-heavy, or visually ambitious. Do not replace the user's idea with a stock genre template.

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
- sonic references and exclusions, music/ambience role, important audible feedback, voice needs, and whether generative audio is allowed;
- requested deliverable: experiment, vertical slice, level, system, content pass, polish pass, or finished build.
- explicit non-goals that prevent the slice from quietly expanding into unrelated systems.

For a portal/web release where advertising is available, record `ads: none | conservative | aggressive-but-compliant` before designing the flow. If the brief does not decide and ads would change menus, pauses, rewards, or progression, ask once rather than inferring a policy. Record where game-initiated interstitials and banners may appear and what voluntary reward, if any, justifies rewarded video. Platform-controlled advertising is distinct from game-initiated calls.

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
