---
name: skill-godot
description: Build, extend, optimize, and visually and sonically polish Godot 4 games from a user-defined brief using native scenes, resources, imported assets, focused scripts, editor tooling, profiling, and verified playable results. Use for 2D, 3D, 2.5D, isometric, orthographic, hybrid, UI, gameplay, levels, asset pipelines, audio, performance, loading, memory, export size, and project architecture in Godot; do not use for projects targeting another engine.
---

# Godot Game Development

Turn the user's design into an editable Godot project, not a scripted imitation of one. Preserve the requested genre, dimension, style, controls, platform, scope, performance target, and existing project conventions.

## Non-negotiable outcomes

- Treat `.tscn` scenes and Godot resources as the authored game; use scripts for behavior, orchestration, procedural systems, and editor automation.
- Serialize persistent composition—actors, props, levels, cameras, lights, collisions, navigation, effects, and UI—so a human can edit it in Godot.
- Make reusable concepts reusable scenes and shared tunable definitions typed/external resources.
- Construct substantial runtime node trees only for genuinely procedural, data-driven, transient, streamed, or performance-driven content.
- Do not hide ordinary authored composition in `_ready()`, giant controllers, factory scripts, or long `Node.new()` chains.
- Never present raw primitives, default controls, mismatched assets, or unreviewed placeholders as finished design.
- For a complete game or vertical slice, give the app/export icon and main menu identity a semantically legible relationship to the game and obtain an independent final-size review; palette consistency cannot turn arbitrary primitive geometry into a meaningful mark.
- For a complete game or vertical slice, deliver coherent, licensed, integrated music/SFX and mixer controls unless the user explicitly requests a silent experience or non-production prototype. Code-synthesized beeps and generic tracks are placeholders, not finished audio.
- For every production character expected to move, autonomously pass a builder-owned motion gate before release: required idle/locomotion/context states run on the production visual, ordinary play never leaves it in bind/rest/T-pose, gameplay causes the state changes, animated attachments follow, and raw target-build motion is inspected. Do not make the user discover routine animation defects.
- For a complete game or vertical slice, prove the clean-profile first-use path through every required onboarding state transition, then obtain independent UX/visual review across representative viewport extremes. Static tutorial text, one generic action, seeded QA state, and the building agent's own screenshot approval are insufficient completion evidence.
- Make complete-game duration/content claims auditable: map them to authored objectives, mechanic permutations/combinations, estimated solve time, and uncoached playtest evidence. A short slice must be labeled as a slice rather than scored as unbuilt hours.
- For fixed-camera isometric/orthographic complete work, block bulk level authoring until a rendered gameplay-size slice—hero, mechanism states, objective, decor, lighting, and UI—passes independent review; later prove character/background separation, route readability, and density/composition in the target camera.
- Do not claim polish, performance, memory, or size improvements without testing the relevant built/rendered result.
- Keep the result maintainable and editable after the agent finishes.

## Inspect before changing

Locate `project.godot`; inspect its Godot features/version, renderer, language, main scene, input map, autoloads, plugins, display/export settings, nearby scenes/resources/imports, conventions, and version-control state. Start with a bounded snapshot instead of dumping the repository:

```bash
python <skill-dir>/scripts/project_snapshot.py --project <project-dir> --summary --json-output <report.json>
```

Then read only the task-relevant scene/resource dependency chain. Determine the available editor/CLI version. Do not silently migrate the engine, renderer, language, addons, or project-wide settings.

Extract the actionable brief from the user's words and references. Infer reversible details when safe; ask only when a missing decision materially changes the result. For a new project, use the installed Godot 4 editor and GDScript unless the user specifies otherwise.

## Read only relevant guidance

Core construction:

- Open-ended brief or new slice: [references/brief-and-genre.md](references/brief-and-genre.md)
- Creating/restructuring scenes: [references/scene-architecture.md](references/scene-architecture.md)
- 2D world/gameplay: [references/production-2d.md](references/production-2d.md)
- 3D world/gameplay: [references/production-3d.md](references/production-3d.md)
- Isometric, dimetric, orthographic, or mixed 2D/3D world/gameplay: [references/isometric-and-2-5d.md](references/isometric-and-2-5d.md), plus the 2D or 3D guide for the selected primary architecture
- UI/HUD/menus: [references/ui.md](references/ui.md)
- Gameplay HUDs, contextual prompts, notifications, or diegetic/world-space UI: [references/game-ui-patterns.md](references/game-ui-patterns.md), plus the base UI guide
- Approved screenshot/mockup-to-Godot parity work: [references/ui-reference-integration.md](references/ui-reference-integration.md), plus the base UI and visual-validation guides
- Traditional/platform fighting or frame-defined buffered combat: [references/genre-fighting.md](references/genre-fighting.md)
- Ability-gated interconnected exploration/metroidvania: [references/genre-metroidvania.md](references/genre-metroidvania.md)
- Idle, clicker, incremental, automation, or prestige economies: [references/genre-idle-clicker.md](references/genre-idle-clicker.md)
- Quests, missions, branching objectives, or persistent event-driven progression: [references/quest-and-progression.md](references/quest-and-progression.md)
- Complete game/vertical slice or autonomous build: [references/playability-and-evaluation.md](references/playability-and-evaluation.md) and [references/audio-vfx-fonts.md](references/audio-vfx-fonts.md)
- Live editor automation, bridge, or MCP: [references/editor-bridge-mcp.md](references/editor-bridge-mcp.md)

Assets and presentation:

- Art direction/coherence: [references/assets-and-art-direction.md](references/assets-and-art-direction.md)
- Search, provenance, licensing, downloads: [references/asset-sourcing.md](references/asset-sourcing.md)
- Concrete source selection for 2D, 3D, UI, audio, fonts, shaders, or animation assets: [references/asset-source-catalog.md](references/asset-source-catalog.md), plus the sourcing guide
- Choosing a community addon/template/framework/theme/shader or interpreting the reviewed source catalogue: [references/evaluated-ecosystem.md](references/evaluated-ecosystem.md)
- Generation/editing: [references/asset-generation.md](references/asset-generation.md)
- Import/adaptation/wrapper scenes: [references/asset-integration.md](references/asset-integration.md)
- Audio, VFX, shaders, fonts: [references/audio-vfx-fonts.md](references/audio-vfx-fonts.md)

Optimization and release:

- FPS, CPU/GPU/physics bottlenecks or performance budgets: [references/performance-and-profiling.md](references/performance-and-profiling.md)
- RAM/VRAM, loading, streaming, stutter, lifecycle: [references/memory-and-loading.md](references/memory-and-loading.md)
- Export/package/download size or release presets: [references/export-and-size.md](references/export-and-size.md)
- Yandex Games Web integration, monetization, saves, lifecycle, moderation, or archive QA: [references/yandex-games-web.md](references/yandex-games-web.md)

Validation:

- Always before completion: [references/validation.md](references/validation.md)
- Visual deliverables: [references/visual-validation.md](references/visual-validation.md)
- External/generated assets: [references/asset-validation.md](references/asset-validation.md)
- Sprite sheets or generated 2D production art: sprite checks in [references/asset-generation.md](references/asset-generation.md)
- GLB/glTF models: model checks in [references/asset-integration.md](references/asset-integration.md)
- Performance/memory optimization: validation section in the relevant optimization reference
- Export/build-size work: validation section in the export reference
- Complete mobile/web evidence setup or rubric migration: generate fresh evidence files with `scripts/evidence_helper.py` instead of reconstructing gates, profiles, and the viewport matrix from memory
- Complete-game app icon/menu identity: complete `assets/semantic-identity-review.template.md` with raw final-size captures and an independent verdict
- Production character expected to animate: complete `assets/production-character-motion.template.md` with builder-owned state dispatch, pose variation, bind/rest/T-pose rejection, attachment-follow checks, and raw target-build motion evidence before optional human preference feedback
- Required touch-scroll behavior: adapt `assets/godot-tests/touch_scroll_probe.gd` into a deterministic project test scene; node presence alone is not proof
- Localized compound/icon-only button alignment or pointer-click cleanup: adapt `assets/godot-tests/button_composition_probe.gd` and retain a release-like Web click check
- Strict/adapted UI-reference integration: fill `assets/ui-reference-parity.template.md` and create same-resolution comparison artifacts with `scripts/image_compare.py`; pixel metrics do not replace region-level human review
- Third-party code/addon adoption: fill `assets/addon-adoption-record.template.md`; a repository link, aggregator summary, clean import, or compatible license alone does not prove ownership/architecture fit
- Metroidvania or quest dependency/escape topology: start from `assets/progression-graph.template.json` and run `scripts/progression_graph_audit.py`, then prove the modeled paths in the actual authored rooms/flows
- Idle/clicker economy work: export a project-specific model from `assets/idle-economy.template.json`, run `scripts/idle_economy_probe.py`, then verify actual transactions, save/offline idempotence, numeric UI, and human pacing in the target build
- Free-orbit third-person locomotion/camera/visibility work: adapt `assets/godot-tests/third_person_controller_probe.gd`, `assets/godot-tests/third_person_hud_mouse_probe.gd`, and `assets/godot-tests/third_person_visibility_probe.gd`, then complete the target-build matrix in `assets/third-person-3d-review.template.md`
- Isometric projection, picking, grid navigation, height transitions, depth sorting, or occlusion: apply the conditional validation in [references/isometric-and-2-5d.md](references/isometric-and-2-5d.md); adapt `assets/godot-tests/isometric_projection_probe.gd` and `assets/godot-tests/isometric_navigation_probe.gd` where their contracts fit
- Complete fixed-camera isometric/orthographic game: before bulk content, fill `assets/isometric-complete-review.template.md`; measure same-frame character/background separation with `scripts/isometric_readability_audit.py --require-thresholds`; and support the claimed scope with `assets/content-duration-contract.template.md`

Hybrid tasks may require several references. Do not read unrelated references preemptively.

## Keep context efficient

- Map the project with scoped file/path searches before opening large scenes or scripts; ignore caches, imports, generated builds, and binaries unless the task targets them.
- Read the relevant scene/resource dependency chain and changed regions instead of repeatedly dumping the repository or whole large files.
- Prefer compact console summaries with full diagnostics written to report files. Use `--summary`/`--json-output` where bundled auditors support them.
- Preserve durable decisions in scenes, resources, manifests, budgets, or short project notes rather than restating them every turn. Never trade away verification or maintainability merely to save tokens.

## Execute in authored slices

Build the smallest complete slice that demonstrates the requested experience: establish scale/camera/input plus visual and sonic language, create reusable scenes/resources, compose the playable scene, add focused behavior, integrate representative production assets including audio, run it, inspect representative states, and iterate. For fixed-camera isometric/orthographic work, do not multiply levels until the representative gameplay-size art/readability gate passes. Do not postpone all sound until after the gameplay and presentation are otherwise declared complete.

Use direct `.tscn`/`.tres` edits for small understood structures; use the Godot editor for visual placement and fragile serialization; use `EditorScript`/`@tool` for repeatable bulk authoring; use appropriate content tools for source assets. Generated output must remain normal Godot scenes/resources. Never edit `.godot/` cache contents as source or invent UIDs when safer editor/path workflows exist.

## Handoff truthfully

Report the scenes/resources/assets changed and how they compose; commands/tests/builds run; rendered or profiled states inspected; intentional runtime-generated content; performance/size baselines and deltas when relevant; and remaining placeholders, license obligations, dependencies, or unverified states.
