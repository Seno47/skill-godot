# Fixed/High-angle 3D District Production

Use this for fixed, mostly fixed, orthographic, isometric-looking, or high-angle perspective 3D levels where the player reads a district, block, arena, settlement, industrial site, or extraction route from above. Also read the ordinary 3D, visual-validation, and applicable genre guides.

This contract exists because a technically traversable map can still read as an empty test arena bordered by repeated fences, containers, and backdrop clones. More prop instances do not create a district. The level needs authored massing, hierarchy, functional zones, controlled visibility, and a camera whose motion preserves those decisions.

For a complete game/slice where this condition materially applies, compose rubric modifier `high-angle-3d-district-complete` with the base genre/platform cases and instantiate `assets/high-angle-3d-district-review.template.md`.

## Lock the district contract before dressing

Start from the gameplay route and camera, then author a small district plan. Record:

- playable footprint, traversal loops, combat/interaction spaces, recovery space, objective/extraction and deliberate dead ends;
- one primary landmark or focal destination for each district read, secondary anchors for materially different junctions/zones, and the places from which each must be visible or reacquired;
- block masses, height bands, street widths, view corridors, street terminations, skyline layers, foreground framing and camera-facing facade families;
- every reachable boundary span and the visible reason it stops the player;
- functional/story zones and their cause-response-consequence evidence;
- structural, facade, roofline/cap, signage/decal, damage/occupation and dressing variation rules;
- camera follow, look-ahead, safe-frame, zoom, volume/rail, occlusion, restore and reduced-motion budgets.

Blockout may use primitives, but the production gate judges the exact target build. A serialized fence rectangle or hundreds of instanced crates remain a failed composition.

## Bound the world with visible urban form

The first barrier the player reads and contacts should have a visible, plausible cause from the gameplay camera. Use combinations of:

- continuous building mass, courtyard walls, retaining walls, embankments, rail cuts, canals, cliffs, collapsed spans, wrecked transit, dense rubble, locked gates, burned blocks, quarantine works, or other brief-specific structures;
- street bends, T-junctions, elevation changes, overpasses, underpasses and facade turns that end sightlines before the camera exposes map void;
- near-camera roof/canopy/foreground masses that frame the playable route while remaining cutaway-safe;
- skyline and distant low-detail mass behind the playable boundary, positioned to continue the district rather than duplicate the nearest building row;
- soft warning/recovery volumes only behind an already legible physical edge.

Do not use an invisible wall as the normal explanation for a reachable edge. A safety collider may sit slightly behind a visible barrier or close a tiny collision leak; record the exception. The boundary ledger must cover 100% of player-contactable boundary spans and pair each collider with its visible cause. Test diagonal approaches and camera-facing gaps: collision that extends across an apparent open street, doorway, arch, or gate fails.

Perspective occlusion is composition, not permission to hide unfinished space. From every supported camera position, the player should see an intentional termination—landmark, turn, facade mass, elevation break, or atmospheric/distant continuation—before the void. Fog, bloom, darkness, a billboard wall, or a fence repeated around the whole rectangle cannot be the only termination device.

For renderer optimization, use large opaque structural masses as real occluders when the view benefits, then measure. Godot occlusion culling is a performance system, not player-facing visibility logic. Keep static `OccluderInstance3D` shapes conservative, inspect the occlusion buffer, and do not let baked occluders erase open arches or moving routes. Split widely dispersed `MultiMesh` groups by spatial cluster so visibility range, frustum and LOD decisions remain useful.

## Compose a district, not a prop field

### Hierarchy and depth

For each required target-build frame, identify:

1. **Primary read:** the destination, threat, hero action, or landmark that wins first attention.
2. **Secondary read:** route choice, mechanism, resource, rescue target, or local anchor.
3. **Support:** facade rhythm, dressing, atmosphere and skyline that explain place without competing.

Use foreground, playable midground and background/skyline as intentional bands. Not every frame needs equal content in all three, but a complete capture matrix cannot be one flat floor with a backdrop row. Large block mass, setback, roofline and height changes establish the district before small props.

Treat long view corridors deliberately. Each important corridor must terminate in one of: a landmark/objective, a meaningful turn, a strong mass/elevation break, or a continuation that clearly belongs to the district. Record the termination and the decision it supports. Repeated identical facades at equal spacing and scale create a ruler, not perspective.

Negative space needs an authored job. Examples include maneuvering room, aim/readability space, a route junction, landmark breathing room, spawn safety, a future encounter footprint, or contrast before a dense story cluster. In the review, name the function of every dominant empty screen region. “We had no more props” and “performance” do not pass without a measured budget and an intentional composition.

### Functional zones and environmental storytelling

Decompose the route by player activity rather than by available asset category. A useful extraction/action district might contain:

- arrival/teaching and orientation;
- resource or rescue branch;
- high-risk combat pocket;
- traversal connector or shortcut;
- recovery/safe pocket;
- primary landmark/objective approach;
- extraction/defense space and its fallback route.

For every zone, record gameplay function, spatial shape, landmark relationship, threat/resource logic, and one short evidence chain:

- **cause:** what happened here;
- **response:** what people/factions attempted;
- **consequence:** what remains and how it changes play.

Example: an evacuation checkpoint can use a bus angled across one lane, a breached barricade at the playable opening, abandoned luggage clustered on the civilian side, emergency lighting/signage and a damaged service route. Twenty random crates and cars do not tell the same story. Prefer a few authored clusters with contact, orientation and ownership over uniform scatter.

Story dressing must preserve route widths, navmesh, combat telegraphs, pickups and silhouettes. If removing a prop cluster changes neither the read nor the story, it may be noise.

## Use modular kits without visible cloning

Reuse is necessary; obvious repetition is optional. Separate the kit into layers:

- **massing:** block footprint, setback, height, corner, arch/entrance and termination pieces;
- **facade:** bay rhythm, openings, storefront/industrial/residential function and floor grouping;
- **cap:** parapet, roof slope, water tanks, vents, damaged roofline and silhouette accents;
- **surface:** material family, restrained hue/value variation, grime/weathering and damage masks;
- **identity:** signs, numbers, awnings, decals, lighting and district/faction language;
- **story cluster:** vehicles, barriers, utilities, debris and human-use traces.

For any structural family that occupies a full gameplay frame, declare at least three independent variation axes from different layers above. Tint alone counts as one axis. A facade material swap does not change an identical skyline silhouette; a rotated container is still the same container if its visible face and cluster role are unchanged.

Define a variation grammar, not random transforms:

- compatible corner, end-cap, entrance and roofline combinations;
- weighted variants by district/zone function;
- adjacency exclusions and a project-owned maximum uninterrupted visible run for an identical module/variant;
- cluster archetypes with authored orientation and spacing ranges;
- deterministic seeds for generated dressing, with the resolved result saved or reproducible;
- reserved hero assets for landmark/objective beats rather than uniform distribution.

Default audit warnings—change only with a recorded visual reason—are three or more adjacent identical modules with the same visible silhouette/material treatment, or two adjacent skyline/backdrop masses at nearly the same screen size, rotation and roofline. Intentional row houses, barriers or industrial repetition may exceed this only when endpoints/corners, facade rhythm, use, wear and skyline variation make the repetition believable in raw gameplay frames.

Use imported assets through wrapper scenes. A useful Godot hierarchy is:

```text
DistrictChunk.tscn
├── Structure
│   ├── BuildingMass_*
│   ├── FacadeVariant_*
│   └── RooflineVariant_*
├── Gameplay
│   ├── StaticBody3D / CollisionShape3D
│   ├── NavigationRegion3D
│   └── Interactions
├── StoryClusters
├── ForegroundCutaway
├── CameraVolumes
└── AudioZones
```

Prefer `PackedScene` wrappers and typed `.tres` style/variant resources over editing imported cache files or scattering material overrides through gameplay code. An `@tool` assembler may place modules, but it must respect adjacency/run-length rules, preserve stable IDs, and save ordinary composition as inspectable scenes/resources. A generator report cannot replace the rendered repetition overlay.

## Build a comfortable high-angle action camera

Keep the camera rig scene-authored and independent from the moving player's transform. Follow the interpolated target, then apply bounded look-ahead, authored framing/volume overrides and obstruction handling in that order. Do not parent a smoothed camera directly under a jittering physics body and then add another lagging lerp.

Declare measurable values before final tuning:

- follow and lead half-life/settle time;
- velocity look-ahead horizon and maximum world/screen-space lead;
- inner safe-frame rectangle for player plus material target/objective;
- minimum/maximum orthographic `size` or perspective FOV/distance;
- maximum zoom rate and pressure enter/exit hysteresis;
- camera-volume blend time, priority and restoration time;
- obstruction probe shape/layers, sampled interest points and restore policy;
- maximum shake/impulse and reduced-motion result;
- teleport/respawn/snap policy and physics interpolation reset;
- permitted frames outside the safe frame in start, stop, reversal, hit, dense combat, objective approach and extraction cases.

Starting values are tuning hypotheses, not universal thresholds. A practical first pass is a 0.12–0.30 s follow half-life, a slower 0.20–0.50 s lead/zoom half-life, a 0.25–0.60 s velocity horizon, and an inner safe frame occupying roughly the central 60–75% of the viewport. Change them from target-build recordings, not by copying them blindly.

Use frame-rate-independent exponential smoothing. With physics interpolation enabled, sample the rendered target transform from `_process()`:

```gdscript
extends Node3D

@export var target: CharacterBody3D
@export var camera: Camera3D
@export var camera_offset := Vector3(10.0, 14.0, 10.0)
@export var focus_offset := Vector3(0.0, 1.0, 0.0)
@export_range(0.01, 1.0) var follow_half_life := 0.18
@export_range(0.01, 1.0) var lead_half_life := 0.30
@export_range(0.0, 1.0) var look_ahead_seconds := 0.40
@export_range(0.0, 20.0) var max_lead_distance := 4.0

var _focus := Vector3.ZERO
var _lead := Vector3.ZERO

func _alpha(delta: float, half_life: float) -> float:
    return 1.0 - pow(0.5, delta / maxf(half_life, 0.001))

func _process(delta: float) -> void:
    var rendered_target := target.get_global_transform_interpolated().origin
    var planar_velocity := target.velocity * Vector3(1.0, 0.0, 1.0)
    var desired_lead := (planar_velocity * look_ahead_seconds).limit_length(max_lead_distance)
    _lead = _lead.lerp(desired_lead, _alpha(delta, lead_half_life))
    var desired_focus := rendered_target + focus_offset + _lead
    _focus = _focus.lerp(desired_focus, _alpha(delta, follow_half_life))
    global_position = _focus + camera_offset
    look_at(_focus, Vector3.UP)
```

Initialize `_focus`, disable automatic interpolation on the manually controlled camera branch when appropriate, and call `reset_physics_interpolation()` after teleports/respawns. Test at an artificially low physics tick rate to expose jitter. Never use `lerp(current, target, speed * delta)` without clamping or a time-constant model.

### Safe framing, zoom and pressure

Use `Camera3D.unproject_position()` to project the player, current threat centroid and material objective into viewport coordinates. Compare them with an authored safe rectangle. Correct focus first; zoom only when the important group cannot fit within the permitted framing. Clamp focus/zoom rates and use hysteresis so one enemy crossing a threshold cannot pump the camera.

Pressure is a semantic signal, not raw enemy count. Derive it from relevant on-screen threats, objective phase, separation of interest targets or authored encounter state; low-pass it and require distinct enter/exit thresholds. Do not continuously zoom on every damage tick or spawn/despawn. Capture quiet-to-dense-to-quiet and prove the same baseline restores.

### Camera volumes and rails

Author exceptional framing as scenes, for example:

```text
CameraVolume.tscn (Area3D)
├── CollisionShape3D
├── FocusMarker3D
└── RailPath3D (optional)
```

Give the wrapper custom exported `camera_priority`, blend-in/out, focus weight, zoom/FOV, allowed offset and restore policy. On `body_entered`/`body_exited`, push/pop that profile through one camera director. Resolve overlaps deterministically by custom priority and recency; do not confuse the custom priority with `Area3D.priority`, which belongs to overlapping environment/physics effects. Blend onto a `Path3D` rail only as much as needed to reveal a landmark/extraction beat, preserve player control and safe framing, and restore the previous profile after exit, death, restart, pause and scene reload.

Hard snaps are limited to explicit cuts, teleports or respawns. A volume must not oscillate at its boundary; use padding/hysteresis or separate enter/exit shapes when necessary.

### Obstruction and cutaway

Camera collision and player/route visibility are separate. Use a shape cast or multiple rays from the desired camera position to several interest points (player feet/torso/head, interaction target and route sample), iteratively collect all blockers, then apply authored responses:

- move/zoom the camera within its framing budget;
- fade/cut away a tagged facade/roof tier;
- switch a precise camera-only proxy around openings;
- use a restrained silhouette fallback when the environment must remain visible.

Do not fade an entire single-mesh district shell into a white x-ray veil. Preserve open-hole negative cases and full material/visibility/shadow restoration. `SpringArm3D` is useful for camera collision shortening, but it cannot by itself prove that the player, target and route remain readable.

## Builder-owned fail-closed evidence

Before owner or independent review, capture the exact target build with the ordinary HUD and final camera:

1. entry/orientation and primary landmark reacquisition;
2. typical street/block with foreground, playable midground and skyline/background intent;
3. reachable boundary contact from the approach angle that most exposes gaps;
4. long view corridor and its termination;
5. densest normal combat/interaction/VFX state;
6. objective/extraction approach and active state;
7. overview/maximum zoom and the transition back;
8. at least one camera volume/rail entry, overlap or edge, exit and restoration;
9. quiet -> accelerate -> stop -> reverse -> dense pressure -> quiet camera motion at normal speed;
10. repetition overlay or annotated captures naming visible source scene/variant IDs.

Fill the template's ledgers and declare PASS/FAIL/NOT TESTED for every row. The builder must fail the gate when:

- a perimeter fence or one facade kit is the dominant boundary explanation across the map;
- duplicated containers/buildings replace block massing or skyline hierarchy;
- a large empty region has no gameplay/compositional function;
- props are uniformly scattered rather than forming functional/story clusters;
- repeated modules exceed the declared run/adjacency budget in the raw camera frame;
- the primary landmark disappears at required decisions with no secondary wayfinding anchor;
- a view corridor ends in map void, cloned backdrop rows or a flat billboard;
- colliders stop the player before the visible boundary or close a visible opening;
- a beautiful still hides camera lag, overshoot, pressure zoom pumping, volume snapping, occlusion loss or failed restoration;
- only prop counts, scene-tree validity, navmesh coverage, occlusion-culling statistics or editor free-camera screenshots are offered.

Do not increase density until the map passes. First fix massing, hierarchy, zone function, boundary causes, route termination and variation grammar; then add only the clusters that support them.

## Research and engine references

- [Godot Camera3D](https://docs.godotengine.org/en/stable/classes/class_camera3d.html): projection, frustum queries and world-to-screen `unproject_position()`.
- [Godot physics interpolation](https://docs.godotengine.org/en/stable/tutorials/physics/interpolation/using_physics_interpolation.html): physics-tick ownership, camera exceptions, low-tick testing and teleport resets.
- [Godot SpringArm3D](https://docs.godotengine.org/en/stable/classes/class_springarm3d.html): ray/shape camera collision and its limits.
- [Godot Area3D](https://docs.godotengine.org/en/stable/classes/class_area3d.html): authored camera-volume entry/exit detection.
- [Godot occlusion culling](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html) and [visibility ranges/HLOD](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html): measured rendering support, not composition substitutes.
- [The Level Design Book: composition](https://book.leveldesignbook.com/process/blockout/massing/composition), [environment art](https://book.leveldesignbook.com/process/env-art), and [modular kits](https://book.leveldesignbook.com/process/blockout/metrics/modular): massing, landmarks, hero props and modular production in a gameplay-first workflow.
- [Joel Burgess, Modular Level Design (GDC)](https://media.gdcvault.com/gdc2016/Presentations/Burgess_Joel_Modular%20Level%20Design.pdf): kit planning and iterative modular level production.
- [Muller et al., Procedural Modeling of Buildings](https://doi.org/10.1145/1141911.1141931): hierarchical mass, facade and detail rules rather than flat random variation.
- [Vinson, Design Guidelines for Landmarks to Support Navigation in Virtual Environments](https://arxiv.org/abs/cs/0304001): landmark design and placement for virtual wayfinding.
