# Assets and Art Direction

Read this to establish and enforce visual coherence. For execution details, route to:

- [visual-style-selection.md](visual-style-selection.md) when the direction itself is new, materially open, or needs a family-specific production profile;
- [asset-sourcing.md](asset-sourcing.md) for search, comparison, provenance, licensing, and downloads;
- [asset-generation.md](asset-generation.md) for creating and editing source assets;
- [asset-integration.md](asset-integration.md) for adapting files and turning them into native Godot objects;
- [audio-vfx-fonts.md](audio-vfx-fonts.md) for sound, music, voice, effects, shaders, and typography.

## Establish a visual contract

Derive a compact art direction from the user's description and references before producing a large asset set. For a new complete game or production slice, make the selection durable with `assets/art-direction-selection.template.md`; do not leave the reason for a bulk visual commitment only in transient conversation. Existing projects and smaller changes may keep a bounded contract in working notes when no direction is being selected or replaced.

Define enough constraints to make rejection possible:

- silhouette and shape language;
- palette, contrast, saturation, and value hierarchy;
- texture/material language and intended surface detail;
- camera, projection, field of view, framing, and typical on-screen scale;
- lighting direction, softness, atmosphere, and time-of-day logic;
- typography and icon language;
- motion character: snappy, weighty, elastic, mechanical, restrained, etc.;
- detail density by importance and distance;
- explicit exclusions taken from the user's brief.

Do not invent a fashionable style to fill ambiguity. A coherent simple direction is better than an assortment of individually impressive assets.

When the direction is materially ambiguous, do not choose whichever free pack or generation route is easiest. Compare viable routes through [visual-style-selection.md](visual-style-selection.md), preserve user authorship, and lock a gameplay-size hero plus representative composition before bulk asset or level production. A fixed user direction does not need performative alternatives, but it still needs production constraints and a rendered anchor.

## Give the shipped identity semantic content

For a complete game or vertical slice, treat the app/export icon and primary menu brand mark as hero assets, not as leftover decoration. Before finalizing them, record:

- the core loop or central fantasy in one sentence;
- what an uncoached viewer is expected to see in the mark;
- which visual element maps to which game-specific object, action, relationship, or world motif;
- which final contexts and pixel sizes must remain legible, including the actual exported app/window/taskbar or platform tile where applicable.

Simple geometry and abstraction are valid when the reading is deliberate. Reject a mark whose only defense is a shared palette, symmetry, polish, a letter-like arrangement, or the developer's explanation after the fact. Rectangles, a circle, a plus, generic sparkles, initials, and engine-default shapes do not become meaningful identity merely because they are neatly composed. Prefer a game-specific silhouette, interaction, object pairing, spatial rule, or recognizable consequence of the core verb.

Capture the mark raw at its actual final display sizes and inside the main menu/exported build; do not judge only a zoomed source file. Have a person or independent evaluation context that did not design it state what it appears to depict before seeing the intended explanation, then record PASS/FAIL and any ambiguity with `assets/semantic-identity-review.template.md`. A coherent palette supports identity but cannot substitute for semantic recognition.

Review the complete main menu separately with `assets/menu-identity-craft-review.template.md`. The title may remain native localized text, but it must read as an authored wordmark or deliberate typographic system through font choice, letter/line spacing, treatment, placement, scale, and relationship to the background/mark. A large default/common-font label, generic badge, decorative rule, redundant premise tagline, and stack of identical rectangles are not production identity merely because they share colors. Remove explanatory or marketing-shaped copy that has no player-facing purpose; empty space is preferable to synthetic personality.

## Plan assets by role

Before bulk sourcing, generation, or authoring, identify the minimum representative set:

- hero assets that define the style;
- modular/repeated world assets;
- interaction and gameplay-readability assets;
- background/support assets;
- UI, icons, effects, audio, and typography;
- temporary assets whose replacement status is explicit.

For a fixed-camera, isometric, or orthographic complete game, a loose asset sample is not enough. Before bulk level authoring, render an early representative gameplay slice at the final camera distance and target framing. It must contain the hero, one mechanism in default and changed states, the objective/beacon, representative structural and dressing decor, near-final lighting/material response, and gameplay UI/tutorial feedback. Have an independent reviewer judge the raw frame at gameplay size. Do not scale the level count while the hero is lost against the floor, the mechanism change is unclear, the world reads as sparse rows of tiles, or the composition is still defended as “temporary.” Record the decision in `assets/isometric-complete-review.template.md` when that case applies.

For other game types, still validate one hero asset and one representative environment composition before scaling the style to dozens of files.

For every complete game or production vertical slice, fill `assets/production-art-state-review.template.md` before handoff. Review raw target-build quiet, normal gameplay, dense interaction, peak VFX/contact, and result states. The dense state is mandatory because empty openings hide intersections, bad sorting/depth, detached effects, debug-looking particles, broken action poses, and asset-family clashes.

Do not treat a primitive as production art because it is serialized in a scene or wrapped in a shader/material. `BoxMesh`, `SphereMesh`, `CylinderMesh`, CSG, flat quads, cones, billboards, and procedural particles are appropriate for blockout, collision, or an explicitly declared minimalist language. In a claimed-finished state they need final-camera evidence that their silhouette, surface treatment, repetition, contact, and effects are deliberate. A painterly panorama behind rounded primitive characters, coarse billboard smoke, rectangular water columns, or flat flame quads is an art-direction failure, not a technical success.

Track provenance when external or generated assets enter a real project: source URL/tool, license or ownership, author when required, original source file, and modifications. Never imply that an unverified internet asset is safe to ship.

## Visual coherence review

Review representative screenshots, not isolated files. Check:

- focal hierarchy: the important actor/action reads first;
- silhouette separation and contrast against the actual background;
- actual gameplay-scale character size and local edge separation, not only an isolated turnaround or enlarged asset preview;
- consistent scale, perspective, outline, texture density, and material response;
- lighting and shadows agree across authored and generated assets;
- repeated assets have controlled variation;
- effects reinforce gameplay without obscuring it;
- UI belongs to the same visual world without harming legibility;
- no default icons, fonts, primitives, checkerboards, debug shapes, or accidental placeholders remain in claimed-finished states.
- the app icon and main menu mark communicate a game-specific identity at final size rather than a generic or AI/default-looking arrangement of shapes.
- the runtime title/wordmark, copy, background, hierarchy, and controls form a game-specific menu rather than a default-font title plus decorative line/tagline/button-stack template;
- dense interaction and peak-effects states preserve readable contacts, depth, silhouettes, asset-family coherence, authored detail, and production-looking VFX.

If an asset does not fit, revise or reject it. Do not hide incoherence with post-processing, bloom, fog, vignette, or color grading.

Useful official references:

- [Godot asset pipeline](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/)
- [Importing images](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html)
- [Importing 3D scenes](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/)
