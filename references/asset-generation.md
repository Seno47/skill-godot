# Asset Generation and Editing

Read this before generating or substantially editing source art. Generated output must pass the same artistic, technical, rights, integration, and visual checks as sourced assets.

## Select an actual production route

Inspect the tools available in the current environment and choose by artifact type:

- raster image generation/editing for concepts, backgrounds, portraits, textures, decals, icons, and suitable sprite source art;
- vector or design tools for scalable icons, UI shapes, logos, and clean graphic systems;
- pixel-art tools for exact grids, palettes, manual frame cleanup, and tile work;
- Blender or another 3D-capable tool for meshes, UVs, rigs, animation, baking, and GLB export;
- audio recording/editing/composition tools for SFX, ambience, music, or voice; generative audio is opt-in rather than a default production shortcut, as defined in [audio-vfx-fonts.md](audio-vfx-fonts.md);
- Godot scenes/resources for particles, shaders, trails, procedural materials, and engine-native effects.

Do not pretend a missing capability exists. A raster image is not a rigged model, a turntable is not geometry, a concept sheet is not a usable sprite sheet, and descriptive text is not an asset file.

## Lock a style anchor

Before bulk generation:

1. Convert the art direction into an asset-specific brief with dimensions/view, gameplay scale, background/transparency, palette, materials, lighting, required variants, and rejection criteria.
2. Create one representative hero asset or small coherent set.
3. Inspect the actual files at full size and in a representative Godot composition.
4. Correct the prompt/reference/source workflow until the anchor is accepted.
5. Derive related assets from accepted references, palettes, materials, proportions, and camera assumptions.

Do not independently generate dozens of assets and attempt to unify them afterward with color grading.

## Structure generation/edit requests

Give the generation tool concrete production constraints rather than a pile of style adjectives:

```text
role and subject
required view/camera and composition
accepted style anchor and family traits
palette, materials, lighting, and detail hierarchy
dimensions, transparency/background, tiling/grid, or model requirements
required variants and elements that must remain consistent
explicit exclusions and technical rejection criteria
```

For edits, distinguish immutable elements from requested changes. Reference accepted source images/models directly when the tool supports them. Keep the number of references small enough that each has a clear purpose.

## Preserve provenance and reproducibility

Record the tool/service, model or tool version when available, generation/edit date, source references, significant prompt/settings, ownership/terms status, and manual modifications. Store sensitive prompts or private source references only when appropriate for the project.

Keep editable source files when they materially improve future consistency or repair. Keep only useful accepted generations in the project; rejected explorations belong in a bounded work area, not `res://`.

For every visual asset, record its intended final gameplay use—not only source pixels: world meters/height/length, displayed sprite or icon pixels, texture tile scale, background crop behavior, camera distance, or another concrete scale contract. Use `scripts/asset_manifest.py add --gameplay-use ...`; this prevents an attractive source image/model from being integrated at arbitrary scale.

## Control paid generation and retries

External generation can spend money or consume limited credits. Before the first paid call, state the provider/tool, bounded purpose, estimated per-item and total cost, and ask for explicit user authorization. A previous approval covers only the recorded budget and scope; material expansion needs new authority.

- Record actual cost with `--cost-cents` and any durable provider task/sidecar path with `--job-record` in the asset manifest.
- For asynchronous providers, persist the task ID and completed stage immediately after submission, before polling. A timeout or a job parked near completion is not proof of failure.
- Query or resume the recorded task first. Do not submit a duplicate paid job unless the provider confirms terminal failure or the user authorizes a deliberate new attempt.
- Keep provider job records and generation references outside runtime-loaded asset folders when the game does not need them. Keep only accepted optimized runtime outputs under `res://` paths used by the game.
- Parallelize independent generations only after the style anchor and budget are accepted. Dependent reference/pose/model/rig stages stay ordered so a bad upstream result does not multiply cost.

## Raster and 2D assets

- Generate at a resolution and viewpoint appropriate for final framing and cleanup.
- Inspect alpha edges against light and dark game backgrounds; remove halos, dirty transparency, unintended shadows, and clipped pixels.
- Normalize canvas size, padding, pivot, pixels-per-unit, palette, outline, light direction, and texture/detail density.
- For pixel art, enforce an exact grid and limited palette during cleanup. Downsampling arbitrary painted output does not automatically become coherent pixel art.
- For tiles, verify edge compatibility, corners, transitions, collision intent, and visible repetition in a filled test map.
- For seamless textures, inspect repeated grids and normal/roughness companions under representative lighting.
- For icons/UI, remove accidental text and inconsistent perspective; test at final pixel size, not only zoomed in.

When transparency is needed, do not trust a prompt that merely asks for “transparent background”: generators may bake a checkerboard, halo, or fake shadow. Prefer a uniform matte color distinct from the subject but reasonably close to the expected game environment, remove it with a real alpha/matting tool, and inspect a QA composite on contrasting light, dark, and representative game colors. Preserve a non-matted source when downstream image-to-3D or other tooling expects the original background.

Very small final sprites/icons should not be judged at the generator's large source resolution. Use bold forms that survive reduction, generate a coherent kit/grid when economical, slice deterministically, and review every cell at its actual display size. Downsampling a detailed 1K image to 32–64 px often creates mud rather than production pixel art.

### Sprite sheets and animation

Never accept a generated sheet based on appearance alone. Verify:

- exact cell dimensions and frame count;
- stable pivot, proportions, costume/details, palette, and light direction;
- complete silhouettes with no cross-cell contamination;
- intentional frame order, timing, anticipation, impact, and loop seam;
- separation of directions/actions required by gameplay.

Split and repair frames with deterministic tools or manual editing. Configure the final animation in Godot scenes/resources and inspect it in motion.

For video-derived sprites, keep the pipeline explicit: accepted character/style reference -> action pose -> motion source -> extracted frames -> measured loop trim for cyclic actions -> alpha cleanup -> Godot animation. Reuse the same accepted reference across actions; limit image-to-image chaining because identity and proportions drift with every generation. Keep source cadence in mind, drive playback from elapsed time, and restart an animation only when the gameplay state actually changes.

Run the bundled deterministic checks before motion review:

```bash
python <skill-dir>/scripts/sprite_audit.py --project <project-dir> --image res://path/to/sprite.png --summary --json-output <report.json>
python <skill-dir>/scripts/sprite_audit.py --project <project-dir> --sheet res://path/to/sheet.png=8x4 --max-anchor-drift 2 --summary --json-output <report.json>
```

The alpha-bounds anchor heuristic catches blank frames, non-divisible grids, clipped padding, and obvious pivot drift. It cannot judge identity, drawing quality, frame order, timing, or cross-frame style; inspect a contact sheet and the animation in motion.

## 3D assets

- Use image generation for concept/reference sheets, texture source, decals, and look development—not as proof that a model exists.
- Use a true 3D workflow for geometry. Inspect topology, normals/tangents, UVs, material slots, pivots, scale, rig, skinning, blend shapes, and animation clips.
- Apply a consistent unit/orientation/naming convention and export through the project's chosen format, normally GLB/glTF.
- Generate or author collision, navigation, LOD, sockets, and lightmap data according to gameplay rather than blindly copying render detail.
- Render turntables and representative gameplay-camera views, then inspect the imported Godot result; source-tool previews are insufficient.
- For AI-generated meshes, expect topology, UV, symmetry, texture, rigging, and license cleanup. Reject outputs whose repair cost exceeds targeted modeling or a suitable sourced asset.

## Variants and controlled reuse

Create variation by changing controlled dimensions—palette, material, wear, accessories, silhouette modules, decals, animation timing, or size—while preserving the accepted family traits. Reuse external materials, palettes, gradients, rigs, skeleton profiles, and modular kits where appropriate.

Do not produce “variation” by adding arbitrary noise, hue shifts, accessories, or incompatible levels of detail.

## Acceptance before integration

An output becomes `accepted` only after:

- the actual file has been inspected;
- it fits the art direction alongside existing assets;
- technical defects are repairable within scope;
- generation/tool terms and source-reference rights are acceptable for the intended use;
- its role and required variants are clear.
- its final gameplay size/use, paid cost when applicable, and resumable job record are preserved.

Then move it through [asset-integration.md](asset-integration.md). Mark it `verified` only after rendered in the real game.
