# Asset Integration

Read this before copying accepted external/generated assets into a Godot project or adapting a ready-made pack. The goal is a maintainable native Godot object, not merely a file visible in the FileSystem dock.

## Inspect the project convention first

Preserve existing paths and naming. If the project has no convention, separate concerns without over-nesting:

```text
art_source/              editable sources kept in-repository when useful
assets/                  runtime-imported images, models, audio, and fonts
materials/               shared Godot materials and shaders
scenes/props/            reusable wrapper scenes
scenes/characters/
ui/                      UI scenes/themes/icons when the project groups them
```

Do not reorganize unrelated existing assets merely to match this example. Avoid importing rejected candidates by keeping the search/generation work area outside the Godot project until acceptance.

## Intake and normalization

Before placing the asset in production paths:

1. Preserve the canonical source URL/tool and license/provenance record.
2. Inspect every included file and remove unrelated demos, duplicates, binaries, plugins, and unused resolutions/variants.
3. Choose stable descriptive filenames and paths before scenes reference them.
4. Normalize scale, orientation, pivot/origin, canvas/padding, palette, texture density, material slots, audio channels, animation names, and loop boundaries as applicable.
5. Preserve editable source files only when they serve repair, variants, re-export, or compliance.
6. Put license/attribution material where the project release process can retain it.

Avoid destructive edits to the only copy of a source asset. Derived runtime files should be reproducible or traceable to the source.

## Configure Godot import intentionally

Let Godot import source files, then configure settings according to use and platform:

- 2D filtering, mipmaps, repeat, compression, lossless mode, SVG scale, animation slicing, and normal-map handling;
- 3D animation clips, rest/reset pose, materials, mesh compression, LODs, lightmap UVs, shadow meshes, collision/navigation generation, and per-node import rules;
- audio sample/stream choice, loop metadata, compression, mono/stereo, and platform overrides;
- font variation/fallback and oversampling choices;
- renderer/platform-specific texture or model overrides.

Do not copy `.godot` cache data between projects or edit it as source. Preserve intentional import metadata tracked by the project.

## Adapt visuals to the game

Ready-made assets usually need art-direction work:

- remap palette and values without destroying readability;
- align outline width, pixel density, perspective, light direction, roughness/metallic response, texture density, and proportions;
- replace or externalize materials so the asset responds consistently to project lighting;
- create missing transitions, corners, damage states, directions, LODs, or modular connectors;
- simplify noisy detail at gameplay distance;
- add controlled variants to reduce obvious repetition;
- remove pack-specific branding, demo labels, or UI that is not licensed/needed.

Test adaptations beside existing hero and environment assets. A uniformly recolored pack can still clash in silhouette, scale, animation, and material behavior.

## Turn files into Godot objects

Create a wrapper or inherited scene when an asset represents a placeable/interactable concept. A typical 3D prop might be:

```text
Chest (Node3D or suitable body)
|-- ImportedModel
|-- PhysicsBody3D
|   `-- CollisionShape3D
|-- InteractionArea
|-- ItemSpawnMarker
|-- AudioStreamPlayer3D
`-- AnimationPlayer
```

A typical 2D actor/prop might be:

```text
Pickup (Area2D)
|-- Sprite2D or AnimatedSprite2D
|-- CollisionShape2D
|-- AnimationPlayer
|-- AudioStreamPlayer2D
`-- EffectMarker
```

These are patterns, not mandatory trees. Include only nodes needed by the concept.

- Keep imported model scenes as generated inputs; add gameplay children and overrides in wrapper/inherited scenes.
- Use external resources for shared materials, themes, curves, gradients, audio, stats, and configuration.
- Add collisions shaped for gameplay rather than tracing artwork/render meshes by default.
- Treat render, gameplay-collision, navigation, and camera-only visibility shells as related but distinct authored contracts. Simplification is expected, but preserve camera-relevant openings and silhouette boundaries; a broad box over a doorway, arch, gate, railing, or window needs an explicit reason and an open-hole negative test.
- Add navigation, sockets, markers, occluders, effect anchors, and animation events deliberately.
- Instance the wrapper scene in levels; do not repeatedly place raw models/sprites and rebuild their behavior elsewhere.
- For non-placeable textures, icons, fonts, and audio, reference them through the relevant material/theme/resource/component instead of inventing empty wrapper scenes.

## Integrate packs incrementally

1. Import one representative object or small set.
2. Configure materials/import and build its wrapper scene.
3. Inspect it with the actual camera, lighting, controls, and renderer.
4. Measure import/runtime cost and identify shared fixes.
5. Apply the proven process to the accepted subset of the pack.

Do not integrate the entire pack before discovering that its scale, rig, materials, or license is unsuitable.

## Reimport and update safety

- Keep source-to-runtime paths stable after scenes depend on them.
- Put project-specific changes outside generated imported content.
- Reimport after source changes and retest wrapper scenes, animation callbacks, material overrides, collision, and sockets.
- Review pack updates as third-party changes; do not overwrite local adaptations blindly.
- Remove replaced assets only after confirming no scene/resource/code references remain.

## Verification gate

Move an asset to `integrated` when paths/import settings/resources/scenes are complete. Move it to `verified` only after checking:

- representative gameplay framing and motion;
- lighting/material response or UI/background contrast;
- collision, interaction, navigation, animation, audio, and effects as applicable;
- render/collision/camera-proxy agreement at representative openings and occlusion-sensitive viewpoints;
- supported aspect ratios and target renderer/platform;
- performance at realistic instance counts;
- reimport stability and absence of missing dependencies;
- license/attribution record and remaining modification notes.

Use `scripts/asset_manifest.py` to validate provenance/status and `scripts/asset_audit.py` to expose missing coverage, duplicates, excessive files, and oversized textures.

For GLB/glTF intake, run the bundled structural audit before import:

```bash
python <skill-dir>/scripts/gltf_audit.py --project <project-dir> --asset res://path/to/model.glb --summary --json-output <report.json>
```

Set `--max-vertices`, `--max-triangles`, and `--max-external-mb` from the actual target budget when relevant. The audit verifies container/index/dependency structure and exposes geometry/material/rig signals; it cannot prove topology, UVs, deformation, scale, material appearance, collision, or animation quality. Inspect the Godot import, wrapper scene, turntable, and gameplay-camera result.
