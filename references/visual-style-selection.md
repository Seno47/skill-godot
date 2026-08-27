# Visual Style Selection

Read this when a new game or production slice does not already have a fully fixed visual direction, when several materially different directions are plausible, or when the chosen art route must be justified before bulk production. This is a selection contract, not a catalogue of fashionable looks.

## Treat style as a layered production decision

Do not reduce art direction to one label such as `pixel art`, `low-poly`, `cozy`, `realistic`, `isometric`, or `2.5D`. Record the selected combination:

- spatial/presentation architecture: 2D, 3D, orthographic/isometric, 2.5D, or a deliberate hybrid;
- image construction: raster, vector, tiles, frame animation, cutout/skeletal, authored 3D, scan/PBR, voxel, procedural, or pre-rendered sources;
- shape and proportion language;
- palette, values, outline/edge treatment, materials, texture/texel density, lighting, and atmosphere;
- motion, animation, VFX, typography, icon, and UI language;
- source strategy: project-authored, sourced pack, generated, commissioned, or a controlled combination;
- gameplay camera/scale, target hardware, memory/download budget, supported locales, and content volume.

The user's explicit direction, references, and exclusions are authoritative. Do not replace an unusual request with an easier generic fantasy, low-poly, pixel, neon, cozy, or casual style. If the requested direction cannot be produced honestly with the available tools, rights, budget, or schedule, preserve its intent and surface the smallest viable substitution instead of silently choosing something convenient.

## Decide whether alternatives are needed

Use one of three paths and record it in `assets/art-direction-selection.template.md`:

1. **User-fixed direction.** Translate the supplied references and exclusions into a production contract. Do not force alternative pitches merely to satisfy a process.
2. **Constraint-determined direction.** When gameplay camera, existing assets, platform budget, or an established project language leaves one clearly viable route, record the rejected alternatives and the hard constraints briefly.
3. **Materially ambiguous direction.** Before bulk asset or level production, compare at least two serious directions, normally no more than four. Ask the user to choose when the difference is primarily taste, brand identity, paid cost, or a major scope tradeoff; otherwise choose from the recorded evidence and explain why.

An adjective pile is not an alternative. Each candidate needs a coherent production route and a fair representation of the same game content: the same hero/action, camera, objective or environment role, and representative UI scale. A moodboard can eliminate weak candidates, but the selected direction still needs an in-engine gameplay-size anchor.

## Compare candidates without hiding tradeoffs

Apply hard rejection criteria first. Reject a candidate that contradicts the user's direction, cannot express the core action readably, lacks usable rights, exceeds the target platform, requires unavailable tools, or cannot scale to the promised content.

For the remaining candidates, record evidence-backed `strong / workable / weak` judgments for:

- player, objective, hazard, route, and interaction readability at the real camera;
- semantic relationship to the player fantasy/core verb and distinctiveness from stock pack or generator defaults;
- availability and rights of a coherent hero, world, UI, animation, VFX, font, and audio-supporting family;
- consistency risk across the actual character, level, biome, item, and animation count;
- silhouette, animation, rigging, frame cleanup, VFX, shader, lighting, and variant workload;
- renderer, fill-rate, shadow, material, texture, VRAM/RAM, loading, and package-size cost;
- localization, accessibility, icon recognition, contrast, and responsive UI fit;
- import, wrapper, reimport, source-editability, maintenance, and repair risk;
- schedule, paid cost, generation retry risk, and the cost of changing direction later.

Do not mechanically sum these judgments and let a cheap available pack overrule user intent or a hard requirement. The matrix exists to expose the real decision, not to manufacture numerical certainty.

## Lock a gameplay-size style anchor

Before bulk production, the selected direction must have:

- one focal hero/actor/object at the ordinary gameplay scale;
- one representative environment composition rather than an isolated asset preview;
- one interaction/objective/hazard state that proves gameplay semantics;
- representative lighting/material/background response;
- enough UI, iconography, typography, motion, and VFX to expose cross-family mismatch when those layers are material.

Capture the selected anchor from the real Godot renderer and target camera. Review it against the selection contract and explicit rejection criteria. For a complete fixed-camera isometric game, the stronger early slice in `isometric-and-2-5d.md` still applies. For all complete games/slices, the later quiet/normal/dense/VFX/result production-art matrix remains required; the anchor approves a direction, not the finished game.

When later evidence invalidates the direction—unreadable dense action, unavailable animation states, unacceptable package cost, incoherent generation, or a failed independent review—stop multiplying it. Update the decision record, repair the anchor, or reopen selection. Color grading, bloom, fog, outlines, or a global shader cannot substitute for that decision.

## Family-specific production profiles

Use the closest profile below, then record project-specific deviations. A game may combine profiles only when one authoritative visual system explains the boundary.

### Pixel art

- Declare grid/cell size, palette policy, pixels-per-unit, integer scale/zoom, filtering, outline, light direction, pivot, and supported animation directions.
- Author or manually clean pixels, tiles, and frames. Downsampling painterly generation is not automatically pixel art.
- Inspect tile repetition, diagonal shimmer, subpixel camera motion, mixed pixel density, frame anchor drift, and UI/font scale.
- Reject mixed resolutions, soft resampling, arbitrary palette noise, inconsistent outlines, or high-detail source art reduced into mud.

### Vector, flat graphic, and UI-first 2D

- Declare geometry, stroke/fill, corner, optical-weight, negative-space, gradient, shadow, and icon rules.
- Keep scalable source vectors or reproducible design files where repair and localization benefit.
- Test silhouettes and icons at final size; a clean rectangle stack, generic symbols, default fonts, or one fashionable gradient is not identity.
- Reject inconsistent stroke weights, accidental raster blur, unrelated icon packs, decorative labels, and component-library sameness.

### Illustrated, hand-painted, storybook, collage, and ink/comic 2D

- Lock perspective, light direction, brush/edge language, value grouping, texture frequency, line weight, and foreground/background separation.
- Decide which layers must animate and whether frame-by-frame, cutout, deform, shader, camera, or limited animation can preserve the direction.
- Keep character identity, proportions, costume, palette, and light stable across poses and scenes; inspect alpha/matte edges against the real background.
- Reject beautiful isolated illustrations that cannot provide gameplay states, coherent animation, clean parallax layers, or readable action at final scale.

### Cutout, skeletal, paper, puppet, and limited-animation 2D

- Define joint construction, pivot/attachment rules, layer order, deformation limits, frame cadence, and deliberate material/paper depth.
- Inspect silhouette breaks, disconnected joints, texture stretching, z-order, foot/ground contact, loop seams, and action readability.
- Do not use limited animation as an excuse for a frozen production character; required idle, locomotion, and context states still need intentional motion.

### Pre-rendered, rotoscoped, or 3D-derived 2D

- Lock source camera, projection, lighting, frame cadence, facings, alpha, scale, and ground-contact pivot before rendering a family.
- Retain enough source information to reproduce missing directions/actions and keep lighting/material continuity.
- Reject perspective or cadence mismatches, baked shadows that contradict the world, oversized sheets, muddy reduction, and inconsistent render settings between actions.

### Stylized low-poly, hand-painted 3D, diorama, clay, and toy-like 3D

- Declare silhouette exaggeration, bevel/edge treatment, proportion, material/atlas strategy, color/value hierarchy, texture density, lighting, and controlled repetition.
- A low triangle count or CC0 pack is not an art direction. Re-author hero silhouettes, materials, landmarks, UI, and variation where the source family is recognizable or incomplete.
- Reject rounded primitive actors, repeated boxes, unmodified stock-pack collage, sparse modular rows, or flat debug VFX defended only as `low-poly` or `minimalist`.

### Toon and cel-shaded 3D

- Declare shadow-band count/thresholds, ramp ownership, outline source/width, normal treatment, specular policy, palette, and VFX/UI edge language.
- Test outlines and shadow bands at camera-distance, animation extremes, intersections, different light angles, transparent effects, and target renderers.
- Reject unstable outline thickness, noisy normals, band flicker, materials that use incompatible ramps, and post-process outlines that destroy route or contact readability.

### Voxel and block-based 3D

- Define voxel scale, shape vocabulary, palette/material rules, meshing/chunk policy, collision, destruction/editability, LOD, and animation style.
- Keep voxel scale and density intentional across characters, props, terrain, VFX, and UI; profile chunk rebuilds and overdraw.
- Reject arbitrary cubes called a style, mixed voxel resolutions without hierarchy, noisy surfaces, and generated volume with no landmark or route composition.

### Retro low-fi 3D (PS1/PS2-era inspired and related looks)

- Record the intended constraints: geometry density, texture resolution/filtering, palette/color depth, vertex/UV behavior, fog/draw distance, lighting, animation cadence, and UI typography.
- Distinguish deliberate emulation from accidental defects. Test readability and motion at the shipped resolution rather than only in enlarged stills.
- Reject generic low resolution, random jitter/dither, unreadable affine artifacts, modern effects that contradict the contract, and inconsistent fidelity between hero, world, UI, and VFX.

### Semi-realistic and photoreal PBR 3D

- Require a true mesh/material workflow with consistent real-world scale, texel density, UVs, map conventions, roughness/metal response, HDRI/lighting, LOD, collision, and animation quality.
- Budget texture resolution, shader features, shadows, skin/hair/transparency, VRAM, loading, and download size against the real platform.
- Prefer coherent scans/material libraries and a few exact hero sources over an eclectic asset collage. Generated reference images do not prove usable geometry.
- Treat realistic humans, hair, cloth, faces, bespoke creatures, cinematics, and large environment sets as high-risk production commitments requiring appropriate source tools and review; downgrade scope rather than faking the promise with mismatched approximations.

### Minimal, abstract, procedural, shader-led, and geometric styles

- Record why primitive or procedural form expresses the core rule, how hierarchy and semantic identity survive, and which shape/material/motion constraints make it deliberate.
- Capture dense gameplay, contacts, VFX, result, menu, and smallest identity sizes. Simplicity raises the importance of proportion, rhythm, motion, sound, and typography.
- Reject blockout geometry, generic neon, arbitrary particles, debug rectangles/cones/billboards, and default controls whose only defense is consistency or performance.

### Isometric, orthographic, 2.5D, and other hybrids

- Treat projection as architecture, not style. Select a primary simulation/render domain and separately select one of the visual families above.
- Record the presentation bridge: scale, perspective, pivot/contact, sorting/depth, lighting/shadow, effect origin/thickness, animation facing, and UI/world relationship.
- Reject painterly backdrops with primitive characters, 2D/3D perspective disagreement, detached effects, depth ambiguity, and styles that work only in an isolated source preview.

## Generated and mixed-family directions

Generation is a production route, not a visual style. Use `asset-generation.md` to lock one accepted reference family and preserve identity, proportions, palette, camera, materials, and motion across derivatives. Use `asset-sourcing.md` and `asset-integration.md` for external packs.

For any mixed route, name the primary family and the exact adaptation applied to each secondary source. Palette remapping alone cannot reconcile perspective, silhouette, texture density, animation cadence, material response, typography, or VFX. If the repair cost is not bounded and repeatable, reject the mix before it spreads.

## Required record

The builder-owned `art_direction_selection_evidence` gate passes only when the record contains:

- fixed/constraint-determined/ambiguous path and the authority for that path;
- selected layered contract and explicit exclusions;
- serious candidate comparison or a truthful reason alternatives were not applicable;
- hard rejects, production risks, asset/tool/rights route, and target budgets;
- raw gameplay-size style-anchor and representative-composition artifacts;
- the decision, decision owner, project revision/date, and triggers that would reopen it.

This gate prevents an agent from choosing an easy asset pack or trendy generator look by habit. It does not overrule the user's taste, require the user to art-direct routine implementation, or claim that a document can certify the final rendered game.
