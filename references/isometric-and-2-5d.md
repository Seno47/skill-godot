# Isometric and 2.5D Production

Use this for isometric, dimetric, orthographic, or mixed 2D/3D gameplay. Also read the ordinary 2D or 3D production guide for the chosen rendering architecture.

## Choose the spatial architecture before building content

Do not use “2.5D” as an implementation decision. Choose one primary spatial model and record it in a short project-owned spatial contract. Copy `assets/isometric-spatial-contract.template.md` when the project does not already document these decisions.

| Architecture | Prefer when | Primary Godot structure | Main risks |
| --- | --- | --- | --- |
| 2D diamond/dimetric | Fixed viewing angle, sprite or pixel-art production, grid-authored levels, modest elevation | `Node2D`, `TileMapLayer`, `CharacterBody2D`, `Camera2D` | picking elevated cells, draw order, tall sprites, multi-floor navigation |
| Orthographic 3D | True elevation, camera rotation, dynamic lighting/shadows, 3D animation or physics | `Node3D`, `GridMap` or authored modular scenes, `CharacterBody3D`, orthographic `Camera3D` | asset/physics scale, occlusion, navigation baking, draw-call and shadow budgets |
| Hybrid | A specific benefit requires mixing domains, such as 2D character art in a 3D navigable world | A clear authoritative world plus a presentation bridge | duplicate transforms, mismatched scale, sorting across render domains, input/picking ambiguity |

For hybrid work, name the authoritative simulation space. Convert into presentation space at one boundary instead of letting gameplay systems alternate between screen, canvas, grid, and 3D coordinates.

Do not silently change architecture after a representative slice exists. A change between these models affects assets, collisions, navigation, camera, sorting, tools, and save data; surface the migration and its cost to the user.

## Block bulk authoring on a rendered art slice

For a fixed-camera isometric/orthographic complete game, pass an early gameplay-size art gate before authoring the level count. One representative rendered slice must show the hero, one mechanism in both relevant states, the beacon/objective, structural and dressing decor, final-direction lighting/material response, and the gameplay HUD/tutorial treatment together. Review the raw target-camera frame, not isolated source assets, editor thumbnails, or an asset-count report.

Reject the slice if the character is visually absorbed by the floor, the mechanism/objective cannot be distinguished at normal zoom, the scene reads as sparse repeated rows, or decoration has no deliberate relationship to route and interaction readability. Asset import success, palette consistency, and a valid scene graph cannot pass this gate. Record the independent verdict with `assets/isometric-complete-review.template.md`; do not multiply an unapproved slice into many levels.

If the production hero is expected to move, it must also pass the separate builder-owned `assets/production-character-motion.template.md` contract before release. Readability screenshots and hero masks can pass while a skeleton remains frozen in bind/T-pose, so require raw target-build idle, locomotion, and brief-required action motion plus real dispatch and attachment evidence; do not delegate that baseline defect search to the independent art reviewer or user.

## Define the spatial contract

Record at least:

- logical axes and cell coordinate type, normally `Vector3i(x, y, elevation)` for layered 2D grids;
- tile width/height, world-unit scale, origin, elevation step, and whether a 2:1 diamond is intentional;
- the authoritative `grid_to_world` and `world_to_grid`/picking implementation;
- sprite/model pivot convention and the ground-contact point used for sorting;
- visual footprint versus occupied gameplay cells;
- collision, walkability, navigation links, and height-transition rules;
- camera angle, rotation policy, zoom limits, and input-relative direction mapping;
- roof/wall occlusion behavior and the multi-level draw-order strategy.

Keep projection and picking math in one focused component. Do not repeat subtly different formulas in the player, map, editor tool, AI, and cursor code. `assets/godot-components/isometric_projection.gd` is a starting resource for a fixed-angle 2D diamond grid; adapt it when the project uses staggered, hexagonal, rotated, or non-grid geometry.

## 2D isometric composition

Compose persistent layers explicitly, for example:

- ground and floor `TileMapLayer` scenes;
- collision/walkability metadata or companion layers;
- decals and below-actor effects;
- actors and interactive scene instances;
- foreground/occluder and roof layers;
- above-actor effects and world-space labels;
- a scene-authored camera rig and screen-space UI.

Use `y_sort_enabled` only where the ground-contact point is a valid depth model. Set each sprite's sorting origin/pivot at its foot or contact point, not at the texture center. Tall art may extend above its cell without changing its gameplay footprint.

Flat Y-sort is insufficient when bridges, balconies, tunnels, or stacked floors can share projected Y. Use explicit floor bands, local sort groups, authored `z_index` ranges, or separate subtrees/canvases. Document transitions between bands. Do not invent one global arithmetic sort key and assume it handles every overlap topology.

Use separate roof/wall occluder scenes when visibility changes independently from collision. Fade, cut away, outline, or hide occluders based on an authored volume or line-of-sight rule; never make essential interaction targets unreadable behind ordinary scenery.

## Orthographic 3D composition

Use a deliberate orthographic `Camera3D`; store angle, orthographic size, near/far range, limits, zoom behavior, and optional rotation steps in a camera-rig scene. Keep meshes, collision, navigation, animation, effects, and audio in world units with a single scale convention.

Use modular authored scenes or a `GridMap` only when their editing and metadata workflow fits the project. A visual grid does not require grid-locked simulation. Conversely, grid tactics still need explicit cell ownership even if the level is assembled from freeform 3D scenes.

Pick the world with a camera ray and resolve the hit to the authoritative cell/interaction target. Do not approximate 3D picking with 2D projection math. For billboards or 2D-looking characters in 3D, verify pivot, shadow receiver/caster behavior, animation facing, outline thickness, and depth-buffer interaction at every permitted camera rotation.

## Projection and picking

For a conventional fixed-angle diamond grid, a common center projection is:

```text
screen_x = origin_x + (cell_x - cell_y) * tile_width / 2
screen_y = origin_y + (cell_x + cell_y) * tile_height / 2 - elevation * elevation_step
```

This formula is a convention, not proof that the art, collision, or camera uses the same projection. Validate it against authored tile centers and pivots.

A screen position alone cannot always determine elevation because stacked cells may overlap. Resolve picking by one deliberate method:

- test candidate elevations from front/top to back/bottom against occupied-cell data;
- query an authored collision/interaction shape;
- use a height map or floor band selected by the current cursor context;
- raycast in 3D.

Specify edge ownership for diamond boundaries so adjacent cells do not flicker under a stationary pointer. Use the same mapper for hover, click, placement preview, AI/debug overlays, and editor tools.

## Movement, input, and navigation

Simulate movement in logical grid or world axes, not screen diagonals. Convert input intentionally:

- fixed-angle 2D may map screen directions into logical axes;
- a rotatable camera must rotate movement intent with the camera or present a clearly world-locked control scheme;
- path-following animation should derive facing from the logical/world segment, then map to the available sprite/model directions.

For 2D grids, `AStarGrid2D` works for single-plane occupancy; stacked floors, stairs, ladders, drops, and bridges usually need explicit graph links or a project-owned navigation adapter. For orthographic 3D, bake/configure navigation for the actual agent radius, height, slope, step, and link rules.

Keep walkability separate from appearance. Test routes through narrow passages, around tall props, across every height-transition type, and after dynamic obstacles change. Save stable logical IDs/cells rather than viewport-dependent screen coordinates.

## Asset contract

Before producing a tile set or sprite family, define:

- source tile dimensions, atlas padding, filtering, mipmap, and pixel-snap policy;
- tile center, ground-contact pivot, and vertical overhang allowance;
- occupied cell footprint and interaction/collision footprint;
- supported facings and whether camera rotation requires additional directions;
- height increments and transition pieces for walls, cliffs, stairs, and roofs;
- normal/depth/height maps or 3D shadow requirements when lighting is part of the style.

A 2:1 tile ratio is common, not mandatory. Do not force existing dimetric art into 2:1 by scaling individual assets. Inspect repeated tiles as a map, animated sprites while crossing, and large props from the gameplay camera.

## Camera and readability

Test the smallest and largest supported viewport, zoom extremes, every allowed camera rotation, dense intersections, and the highest supported elevation. Keep the active cell, character contact point, path preview, and interaction affordances readable without relying only on color.

For a fixed camera, declare a gameplay-size readability budget before final review. For the quiet floor, densest representative decor/mechanism state, height transition, and route-changing/occlusion stress state, capture:

- one raw target-build screenshot;
- one hero-only silhouette mask from the exact same camera and frame;
- the declared minimum screen-space character size;
- at least one mean character/background separation threshold and one local-edge separation threshold;
- an independent reading of the hero silhouette, actionable route, mechanism state, and objective.

Run `scripts/isometric_readability_audit.py --require-thresholds` to measure the same-frame mask. The report is regression evidence, not an art critic: a number cannot approve a generic white hero, a noisy silhouette, a misleading route, or a composition that only works with tutorial highlighting. Thresholds are project-owned, must be recorded before final evaluation, and must not be relaxed after failure without rationale and a full state re-review.

Review visual density as composition rather than asset quantity. At gameplay scale, capture the start/teaching area, a typical puzzle, the densest mechanism/decor area, the highest elevation transition, and the objective/result state. Check focal hierarchy, purposeful foreground/midground/background structure, landmarks, negative-space rhythm, route continuity, controlled repetition, and HUD/world competition. Sparse tile rows are acceptable only when their negative space serves navigation and the independent reviewer can state that purpose.

For pixel art, choose integer-compatible asset scale and camera zoom; inspect motion for shimmer at diagonal speeds. For smooth art, avoid snapping that causes visible stepping. Camera smoothing must not make cursor-to-cell picking lag behind the rendered world.

## Performance priorities

Measure the target build. Common hotspots include:

- too many individually updating tile/prop nodes instead of tile layers, chunks, or batched visual instances;
- transparent overdraw from tall sprites, roof fades, particles, and full-screen effects;
- per-frame resorting or rebuilding navigation for mostly static worlds;
- 3D real-time shadows, transparent billboards, excessive materials, and unbounded orthographic view distance;
- rebuilding projection/path previews when neither cursor cell nor path state changed.

Chunk or stream only when world size, editor performance, loading, or target hardware justifies it. Preserve authored chunk boundaries and deterministic coordinates.

## Required validation for affected systems

Validate in addition to ordinary engine, gameplay, and visual checks:

1. **Projection round-trip:** representative negative, positive, origin, edge, and elevated cells map to world/screen and back consistently.
2. **Picking:** centers, edges, corners, occupied tall cells, and overlapping elevations select the intended target without flicker.
3. **Depth crossing:** actors pass in front of and behind tall props, walls, each other, and floor transitions without popping.
4. **Navigation:** reachable routes, blocked routes, narrow cells, dynamic blockers, and every height transition obey the spatial contract.
5. **Collision:** visual foot/contact points and gameplay shapes agree at diagonal approaches and elevation boundaries.
6. **Camera:** zoom, limits, aspect extremes, smoothing, and each allowed rotation preserve input mapping and readability.
7. **Occlusion:** roofs/walls reveal the actor and restore correctly during entry, exit, pause, reload, and scene transition.
8. **Persistence:** saved cell/floor/object identities restore to the same logical position independently of viewport size.
9. **Early art slice:** hero, mechanism states, objective, decor, lighting, and UI pass independent rendered review before bulk level authoring.
10. **Production character motion:** when the hero is expected to animate, builder-owned evidence rejects bind/rest/T-pose, missing state playback, test-only dispatch, and detached attachments in the target build.
11. **Character/route readability:** same-frame screenshot/mask reports meet the declared size, mean-separation, and edge-separation thresholds in quiet, dense, height, and route-changing states, while raw review confirms silhouette and route meaning.
12. **Onboarding state machine:** the shipping first-use flow makes the player perform every brief-required transition, including movement, pickup, context interaction, mechanism change, route traversal, height/lift, objective delivery, and recovery where applicable; feedback is distinct and overlays never cover the target.
13. **Composition and duration:** the fixed-camera capture matrix rejects sparse/default-looking presentation, and the declared game duration is supported by authored puzzle/permutation counts plus uncoached playtest evidence.

Copy/adapt these deterministic probes into the project test suite:

- `assets/godot-tests/isometric_projection_probe.gd` for mapper round-trips;
- `assets/godot-tests/isometric_navigation_probe.gd` for path endpoints, adjacency, walkability, and height transitions.

The probes validate project contracts, not visual depth. Keep rendered crossing captures or a deterministic visual fixture for sorting, occlusion, and camera review.

For the complete fixed-camera case, use `assets/isometric-complete-review.template.md` together with `assets/content-duration-contract.template.md`. A short polished slice can be delivered truthfully as a slice; it cannot pass as a multi-hour complete game.

Useful official references:

- [Using TileMaps](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilemaps.html)
- [Y-sorting](https://docs.godotengine.org/en/stable/tutorials/2d/2d_sprite_animation.html#y-sorting)
- [AStarGrid2D](https://docs.godotengine.org/en/stable/classes/class_astargrid2d.html)
- [Ray-casting](https://docs.godotengine.org/en/stable/tutorials/physics/ray-casting.html)
- [Orthogonal camera projection](https://docs.godotengine.org/en/stable/classes/class_camera3d.html)
