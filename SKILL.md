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
- For a complete game or vertical slice, deliver coherent, licensed, integrated music/SFX and mixer controls unless the user explicitly requests a silent experience or non-production prototype. Code-synthesized beeps and generic tracks are placeholders, not finished audio.
- For a complete game or vertical slice, prove the clean-profile first-use path through an interactive onboarding action, then obtain independent UX/visual review across representative viewport extremes. Static tutorial text, seeded QA state, and the building agent's own screenshot approval are insufficient completion evidence.
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
- Complete game/vertical slice or autonomous build: [references/playability-and-evaluation.md](references/playability-and-evaluation.md) and [references/audio-vfx-fonts.md](references/audio-vfx-fonts.md)
- Live editor automation, bridge, or MCP: [references/editor-bridge-mcp.md](references/editor-bridge-mcp.md)

Assets and presentation:

- Art direction/coherence: [references/assets-and-art-direction.md](references/assets-and-art-direction.md)
- Search, provenance, licensing, downloads: [references/asset-sourcing.md](references/asset-sourcing.md)
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
- Required touch-scroll behavior: adapt `assets/godot-tests/touch_scroll_probe.gd` into a deterministic project test scene; node presence alone is not proof
- Localized compound/icon-only button alignment or pointer-click cleanup: adapt `assets/godot-tests/button_composition_probe.gd` and retain a release-like Web click check
- Isometric projection, picking, grid navigation, height transitions, depth sorting, or occlusion: apply the conditional validation in [references/isometric-and-2-5d.md](references/isometric-and-2-5d.md); adapt `assets/godot-tests/isometric_projection_probe.gd` and `assets/godot-tests/isometric_navigation_probe.gd` where their contracts fit

Hybrid tasks may require several references. Do not read unrelated references preemptively.

## Keep context efficient

- Map the project with scoped file/path searches before opening large scenes or scripts; ignore caches, imports, generated builds, and binaries unless the task targets them.
- Read the relevant scene/resource dependency chain and changed regions instead of repeatedly dumping the repository or whole large files.
- Prefer compact console summaries with full diagnostics written to report files. Use `--summary`/`--json-output` where bundled auditors support them.
- Preserve durable decisions in scenes, resources, manifests, budgets, or short project notes rather than restating them every turn. Never trade away verification or maintainability merely to save tokens.

## Execute in authored slices

Build the smallest complete slice that demonstrates the requested experience: establish scale/camera/input plus visual and sonic language, create reusable scenes/resources, compose the playable scene, add focused behavior, integrate representative production assets including audio, run it, inspect representative states, and iterate. Do not postpone all sound until after the gameplay and presentation are otherwise declared complete.

Use direct `.tscn`/`.tres` edits for small understood structures; use the Godot editor for visual placement and fragile serialization; use `EditorScript`/`@tool` for repeatable bulk authoring; use appropriate content tools for source assets. Generated output must remain normal Godot scenes/resources. Never edit `.godot/` cache contents as source or invent UIDs when safer editor/path workflows exist.

## Handoff truthfully

Report the scenes/resources/assets changed and how they compose; commands/tests/builds run; rendered or profiled states inspected; intentional runtime-generated content; performance/size baselines and deltas when relevant; and remaining placeholders, license obligations, dependencies, or unverified states.
