# Assets and Art Direction

Read this to establish and enforce visual coherence. For execution details, route to:

- [asset-sourcing.md](asset-sourcing.md) for search, comparison, provenance, licensing, and downloads;
- [asset-generation.md](asset-generation.md) for creating and editing source assets;
- [asset-integration.md](asset-integration.md) for adapting files and turning them into native Godot objects;
- [audio-vfx-fonts.md](audio-vfx-fonts.md) for sound, music, voice, effects, shaders, and typography.

## Establish a visual contract

Derive a compact art direction from the user's description and references before producing a large asset set. Record it in the project only when a persistent brief is useful; otherwise keep it in the working notes.

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

## Plan assets by role

Before bulk generation, identify the minimum representative set:

- hero assets that define the style;
- modular/repeated world assets;
- interaction and gameplay-readability assets;
- background/support assets;
- UI, icons, effects, audio, and typography;
- temporary assets whose replacement status is explicit.

Validate one hero asset and one representative environment composition before scaling the style to dozens of files.

Track provenance when external or generated assets enter a real project: source URL/tool, license or ownership, author when required, original source file, and modifications. Never imply that an unverified internet asset is safe to ship.

## Visual coherence review

Review representative screenshots, not isolated files. Check:

- focal hierarchy: the important actor/action reads first;
- silhouette separation and contrast against the actual background;
- consistent scale, perspective, outline, texture density, and material response;
- lighting and shadows agree across authored and generated assets;
- repeated assets have controlled variation;
- effects reinforce gameplay without obscuring it;
- UI belongs to the same visual world without harming legibility;
- no default icons, fonts, primitives, checkerboards, debug shapes, or accidental placeholders remain in claimed-finished states.

If an asset does not fit, revise or reject it. Do not hide incoherence with post-processing, bloom, fog, vignette, or color grading.

Useful official references:

- [Godot asset pipeline](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/)
- [Importing images](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_images.html)
- [Importing 3D scenes](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/)
