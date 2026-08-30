# 3D Production

For fixed/high-angle districts, arenas, settlements, urban/extraction routes, or cameras that use pressure zoom and authored volumes/rails, also read [high-angle-3d-districts.md](high-angle-3d-districts.md). Its visible-boundary, district-composition, modular-variation and camera-motion contract is stricter than the general guidance here.

Use this for 3D gameplay/world work. Also read the UI guide for screen-space interfaces.

## Establish the 3D space

Derive these from the brief and project:

- scale convention, gravity/up axis, and target movement speeds;
- perspective or orthographic camera, field of view/size, framing, clipping, and camera collision;
- renderer and target hardware constraints;
- material model, texture density, lighting model, environment, fog, and shadow budget;
- authored, modular, generated, or streamed world structure.

Use consistent scale from model source through import, collision, navigation, camera, physics, and audio attenuation. Do not solve every mismatch with per-instance scaling.

## Compose native scenes

Typical reusable scenes combine a semantic root with authored children:

- `CharacterBody3D`, `RigidBody3D`, `StaticBody3D`, `AnimatableBody3D`, or `Area3D` chosen for the actual physics contract;
- imported model scene or `MeshInstance3D` presentation;
- simple gameplay collision shapes;
- `AnimationPlayer`/`AnimationTree`, skeleton attachments, markers, interaction volumes, audio, particles, decals, and effect sockets;
- focused behavior/configuration at the scene root;
- optional LOD/visibility helpers appropriate to the project version.

Keep these nodes visible and editable. Do not make a player, prop, vehicle, or level exist only as a runtime-built tree unless it is genuinely generated.

## Model/import workflow

- Prefer glTF 2.0/GLB for exchange unless the project has a proven alternative pipeline.
- Preserve source modeling files when the team uses them, with export paths and naming that avoid accidental duplicates.
- Treat the imported scene as generated. Add project behavior through an inherited or wrapper scene.
- Inspect advanced import settings when collision generation, animation clips, material extraction, LODs, lightmap UVs, skeletons, or per-node filtering matter.
- Use external materials when Godot-side shading must survive reimport.
- Verify orientation, transform application, pivot, normals/tangents, UVs, skin weights, rest pose, and animation loop boundaries.

For a static environment, separate or classify render meshes, gameplay collision, navigation sources, occluders, and lightmap contributors. The highest-detail render mesh is rarely the right collision mesh.

## Geometry strategy

- Use primitives/CSG for blockout, collision, deliberate minimalist style, or fast spatial iteration.
- Replace blockout geometry when the requested finish depends on authored silhouettes, bevels, topology, UVs, or surface detail.
- Build modular kits with consistent dimensions, pivots, snapping, material slots, and transition pieces.
- Use scene instances for repeated semantic objects. Use `MultiMeshInstance3D` for very large repeated visual sets that do not need individual node behavior.
- Use procedural meshes only when generation is part of the design or provides a clear authoring advantage. Cache or serialize results when humans need to edit them.

Scene authorship and production art are separate claims. Saving a `BoxMesh`, `CylinderMesh`, `SphereMesh`, CSG object, shader quad, or procedural particle emitter in `.tscn` makes it editable; it does not prove a final silhouette, material, detail, or effect. For a claimed-finished game, document any deliberate primitive/minimalist language and judge it in dense target-build gameplay against the characters, background, lighting, and VFX. Unjustified rounded primitive actors, repeated box vehicles/rooms, rectangular spray, flat cone/quad flames, and coarse billboard smoke remain blockout/debug art.

## Materials, lighting, and environment

- Create a small material language before making dozens of unique materials.
- Share external `StandardMaterial3D`, shader, gradient, curve, and environment resources where consistency matters.
- Balance albedo values, roughness, metallic response, normal strength, and texture density under the actual game lighting.
- Establish `WorldEnvironment`, sky/background, exposure/tonemapping, ambient contribution, fog, and color adjustment intentionally.
- Place key/fill/environment lighting to support form and gameplay readability. Use baked, dynamic, or mixed lighting according to scene mutability and target platform.
- Budget shadows, light ranges, transparency, particles, screen-space effects, and shader complexity; test on the intended renderer.

Post-processing is a finishing layer. Do not use bloom, fog, SSAO, outlines, or grading to conceal weak composition or mismatched materials.

## Camera and spatial readability

- Make a camera rig scene when follow, orbit, aim, shoulder switching, collision, rails, shake, or transitions need coordinated behavior.
- Keep camera input separate from actor simulation where practical.
- Verify sightlines, occlusion, scale cues, depth separation, horizon, focal hierarchy, and motion comfort.
- Use orthographic cameras deliberately; adjust asset shapes and depth cues to match, rather than treating them as perspective cameras with no convergence.
- Test near walls, tight interiors, vertical changes, large effects, and target aspect ratios.

For a player-controlled character with an independently orbiting perspective camera, define the locomotion reference frame explicitly. Unless the brief deliberately calls for tank, actor-relative, rail-relative, or fixed world-axis controls, project the active gameplay camera's forward/right directions onto the movement plane and derive movement from that basis. A correct result must keep `forward` visually forward after camera yaw, not merely at the spawn angle. Prove it after at least 45° and 90° yaw on a flat deterministic fixture; record world-axis control as a conscious exception rather than an implementation default.

Treat an orbit camera as an input and recovery contract, not just a `Camera3D` node:

- exercise mouse horizontal and vertical orbit plus right-stick horizontal and vertical orbit separately, with intentional sensitivity, deadzone, inversion, and pitch limits;
- provide zoom and recenter for a freely orbiting exploration/action camera unless the brief explicitly excludes them; verify recenter against the actor's current facing, not the original world direction;
- validate the collision solution, commonly a `SpringArm3D` or equivalent, when clear, behind a wall, in a corner, near vertical/overhead geometry, and after leaving the obstruction; the camera should shorten and restore without entering geometry or snapping through the player;
- after pause, menu entry, focus loss, device change, and return to gameplay, restore the intended mouse mode/capture exactly once, discard stale look delta, and prove the first click/motion does not rotate or fire unexpectedly.
- prove captured mouse motion through the production fixture with its real full-screen HUD visible. Because GUI handling precedes `_unhandled_input()`, a covering `Control` can consume `InputEventMouseMotion`; inject a real event through `Input.parse_input_event()` and assert both yaw and pitch rather than calling a look method directly. Route passive HUD motion intentionally and gate earlier-stage look handling by active gameplay/modal state so menus still block camera motion.

Camera collision and player visibility are separate systems and require separate evidence. A `SpringArm3D` shortening correctly proves only that the camera avoids selected physics geometry; it does not prove that the character's render shell is visible from the resulting camera, that multiple occluders are handled, or that simplified camera proxy volumes respect visible openings.

For third-person player visibility:

- sample rays or equivalent visibility checks from the desired unobstructed camera position toward several authored character heights/regions, such as feet, torso, shoulders, and head; one center ray is too fragile;
- iterate past the first hit and collect every relevant occluder between camera and player. A nearer faded object must not hide a second opaque object behind it;
- distinguish render geometry, gameplay collision, and camera-only visibility/collision proxies by authored groups/layers/metadata. Simplified shells are valid, but openings that matter to the camera—doors, arches, gates, railings—must agree closely enough to avoid false positives;
- author cutaway/fade policy by semantic strength or scope rather than applying one room-wide fade to everything. Preserve route walls/floors that provide orientation while resolving the actual camera-player blockers;
- treat large, high-detail, or single-mesh room shells as a distinct high-structure case. A nonzero fade and a visible player silhouette do not pass if the shell becomes a bright veil/grid or still destroys route contrast. Prefer semantically split shells where practical; otherwise author a stronger shell tier and verify the exact highest/elevation or previously reported failure view with matched final-camera captures;
- use a restrained player silhouette/depth fallback when cutaway cannot safely preserve both player and route. It must not turn normal play into permanent x-ray vision;
- snapshot and fully restore every mutated visual state when clear: visibility, per-instance transparency, material/shader parameters, render layers, shadows, and any shared-resource override. Test repeated blocked/clear cycles and scene/reset transitions for leaked state;
- include an explicit negative case through the open center of an authored doorway/gate and a positive multi-occluder case. Test more than one real route location because one tuned room is not a visibility system.

For a complete third-person/free-orbit slice, adapt `assets/godot-tests/third_person_controller_probe.gd`, `assets/godot-tests/third_person_hud_mouse_probe.gd`, and `assets/godot-tests/third_person_visibility_probe.gd` to project fixtures using the production rig, real HUD, and occlusion system, then complete the rendered/target-build matrix in `assets/third-person-3d-review.template.md`. Deterministic probes supplement rather than replace hands-on camera comfort/sensitivity, silhouette quality, route readability, and capture recovery.

## Physics and navigation

- Choose simple primitives/convex shapes for moving bodies. Use concave/trimesh collision only where appropriate for static geometry.
- Configure collision layers and masks by gameplay role.
- Validate slopes, steps, ledges, tunneling risk, moving platforms, scale, and center of mass as applicable.
- Bake/configure navigation for actual agent radius, height, slope, step, and movement model. Test narrow gaps and dynamic obstacles.
- Keep visual detail out of navigation and collision unless it changes gameplay.

## Animation and effects

- Preserve named animation clips and a known rest/reset pose during import.
- Use `AnimationTree` when blending/state transitions justify it; avoid complex graphs for a handful of direct clips.
- Attach weapons/effects through stable skeleton or marker sockets.
- Keep gameplay events explicit and test animation-driven callbacks after reimport.
- Inspect particles, trails, decals, transparency sorting, and shader effects from the gameplay camera, not only in isolation.

## Treat production character motion as a release contract

When a focal production character is expected to stand, move, or perform visible actions, animation is not optional polish. Fill `assets/production-character-motion.template.md` and pass it as builder-owned routine QA before requesting independent or user preference feedback. A clean import, valid skeleton, readable silhouette, successful navigation trace, or attractive still cannot pass a character that remains frozen in its bind/rest/T-pose.

Define the smallest brief-required state set. A moving character normally needs idle and locomotion plus the context actions that ordinary play visibly attributes to the character, such as pickup, interact, attack, lift use, damage, or success. An intentionally static, hovering, board-piece, or deliberately limited-animation actor may use a smaller contract, but record that art-direction decision instead of silently omitting motion.

For imported or retargeted skeletal motion:

- drive the production mesh and `Skeleton3D`, not only the source animation-library mannequin or editor preview rig;
- verify the retarget profile/root, rest orientation, scale, named clips, loop boundaries, and required root-motion policy;
- hide or remove the source mannequin/preview mesh from the shipping scene;
- sample stable non-root bones or pose features across time for idle and locomotion, because an in-place clip may leave the root transform unchanged;
- exercise actions through real gameplay events/state transitions, not only direct `AnimationPlayer.play()` calls in a test;
- attach carried props, weapons, lanterns, effects, or markers through `BoneAttachment3D`/authored sockets and prove their world transforms follow representative animated poses;
- test interruption, restart, pause, and scene transition so a one-shot action cannot leave a stale/frozen pose.

Keep a deterministic project-owned contract for clip/state presence, time-varying production poses, real dispatch, source-preview visibility, and attachment following. Then capture a short raw target-build recording at the real gameplay camera covering idle, locomotion, and required context actions, plus a contact sheet when it helps compare poses. Inspect normal-speed motion for bind/T-pose leakage, frozen tracks, duplicate mannequins, loop pops, foot sliding, contact mismatch, detached attachments, retarget distortion, and movement-speed disagreement. A contact sheet alone cannot prove playback or state dispatch; an automated pose delta alone cannot judge motion quality.

The builder must autonomously fix objective failures in this contract. Final human feedback about weight, personality, exaggeration, or taste is useful but optional unless the brief makes it an acceptance requirement; it is not a substitute for baseline QA and must not make the user responsible for discovering a frozen production character.

## 3D visual completion gate

Inspect representative gameplay views and motion. Fill `assets/production-art-state-review.template.md` for complete games/slices and include quiet, normal gameplay, dense interaction/contact, peak VFX, and result states from the same release-like build. Reject the pass if:

- blockout primitives remain where authored finish was promised;
- primitive/debug-looking character, vehicle, environment, water, fire, smoke, impact, or trail shapes are defended only by scene serialization, materials, particles, or shaders rather than a coherent gameplay-size art direction;
- dense interaction reveals actor/prop/effect intersections, broken contact/depth, detached action effects, asset-family mismatch, empty placeholder panels, or sparse repeated modules that the quiet opening hid;
- model scales, pivots, or texture densities visibly disagree;
- lighting flattens important forms or makes gameplay objects unreadable;
- materials only look coherent under one accidental angle;
- camera clipping/occlusion harms ordinary play;
- camera collision passes but the player remains hidden, a second occluder is ignored, open-hole proxy geometry causes false cutaway, or blocked state leaks after clearing;
- a faded high-structure/single-mesh shell leaves a bright grid/veil across the exact reported or highest-elevation route view, even if the player silhouette remains visible;
- movement direction stops matching the camera after ordinary orbit, a declared camera input axis is missing, or pause/re-entry leaves capture/look in the wrong state;
- mouse-look was proved only by a direct method call or a fixture without the production HUD, so real GUI event consumption can still suppress yaw/pitch;
- a production character expected to move stays in bind/rest/T-pose, lacks required idle/locomotion/context states, dispatches them only in a test path, shows a source mannequin, freezes after interruption, or leaves required attachments behind;
- persistent HUD or bright world geometry blocks ordinary route sightlines from the real gameplay camera;
- render meshes are used as expensive/unstable dynamic collision without reason;
- imported assets were changed in a way that reimport will erase.

Useful official references:

- [Godot 3D documentation](https://docs.godotengine.org/en/stable/tutorials/3d/)
- [Importing 3D scenes](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/)
- [Advanced 3D import settings](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/advanced_import_settings.html)
- [3D navigation overview](https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_introduction_3d.html)
