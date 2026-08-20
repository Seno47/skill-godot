# 3D Production

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

## 3D visual completion gate

Inspect representative gameplay views and motion. Reject the pass if:

- blockout primitives remain where authored finish was promised;
- model scales, pivots, or texture densities visibly disagree;
- lighting flattens important forms or makes gameplay objects unreadable;
- materials only look coherent under one accidental angle;
- camera clipping/occlusion harms ordinary play;
- render meshes are used as expensive/unstable dynamic collision without reason;
- imported assets were changed in a way that reimport will erase.

Useful official references:

- [Godot 3D documentation](https://docs.godotengine.org/en/stable/tutorials/3d/)
- [Importing 3D scenes](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/)
- [Advanced 3D import settings](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/advanced_import_settings.html)
- [3D navigation overview](https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_introduction_3d.html)
