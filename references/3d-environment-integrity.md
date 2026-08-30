# 3D Environment Integrity

Use this contract for dense 3D dressing, especially fixed/high-angle districts where the shipping camera exposes contacts, silhouettes and ground coverage. It closes a different question from gameplay collision: collision coverage proves that gameplay has physical boundaries; environment integrity proves that visible objects do not penetrate one another, belong to the surface they occupy, clear overhead structures, and cover the rendered ground without holes.

For `high-angle-3d-district-complete`, this is a builder-owned blocking gate. Instantiate `assets/environment-integrity-contract.template.json` and `assets/environment-integrity-review.template.md`, export the resolved target-scene geometry, then run:

```bash
python scripts/environment_integrity_audit.py \
  --model reports/environment-integrity-contract.json \
  --json-output reports/environment-integrity-audit.json \
  --summary
```

The command must return PASS. Collision coverage, boundary coverage, navigation, origins inside legal polygons, or one overview screenshot cannot substitute for it.

## Author resolved occupancy, not origin checks

Have a project-owned exporter traverse the final instantiated target scene using a stable group/query and emit the scene path, scene revision/hash, exporter path and resolved visible-prop count. Do not curate only the props already suspected of failing. Give every visible prop that can penetrate another prop one or more local occupancy boxes. Use multiple boxes for an L-shaped building, tower legs, a lamp head/shaft, a vehicle body, or geometry with a deliberate opening. A single oversized AABB creates false positives around empty holes; an origin test creates false negatives around every wide or rotated prop.

Export the final `global_transform` as Godot basis columns plus origin and transform all eight box corners. The audit builds the transformed XZ convex footprint, preserves the transformed vertical range, and applies a separating-axis test plus Y penetration. This covers translation, rotation, non-uniform scale and parent transforms. For `MultiMeshInstance3D`, compose the node transform with every instance transform and emit a stable instance ID.

An intentional contact or authored mount needs an exact instance/volume pair exemption with:

- the checks being exempted (`occupancy` and/or `vertical_clearance`);
- a concrete physical reason;
- a raw target-build close-up;
- a still-current overlap. Stale exemptions fail, and class-wide ignores are forbidden.

If a visible instance genuinely does not participate in occupancy, `occupancy_required: false` also needs its own reason and raw artifact. A bare opt-out is a contract error.

Collision shapes may seed QA proxies when they fit the rendered shell, but render and collision shells must be compared. Do not silently treat a simplified gameplay collider as the visible footprint.

## Prove semantic surface ownership over the full support footprint

Define surface ownership by semantic class, for example:

- `nature_tree`, `nature_rock`, `nature_bush` -> authored `grass` or `soil`;
- `vehicle` -> `road`, parking pad or authored wreck bed;
- road debris -> an explicitly permitted road/debris class, not the nature rule;
- facade furniture -> sidewalk, facade apron or named foundation surface.

Each applicable instance exports a support polygon in local XZ plus its support Y. Transform and sample both the boundary and interior; the audit resolves the transformed support-plane height at every sample, including tilted or scaled parents. Every sample must hit an allowed topmost render surface within the declared height tolerance. The origin being legal is not enough: a tree canopy/trunk bed, rock, bush or vehicle whose full footprint crosses a curb still fails. Every class listed in `surface_ownership_rules` is enforced even if an instance attempts to opt out.

Choose `max_surface_sample_step` below the smallest illegal incursion worth detecting. Record that budget in world units; do not tune it after seeing a failure merely to skip the offending strip.

## Audit visible ground independently from collision

Export triangles from the actual visible ground meshes after final transforms, with stable `surface_class` and `material_id`. The contract deliberately requires `render_ground_source: "mesh_faces"`; a broad `StaticBody3D`, navigation plane, hidden floor, or catch-all collider cannot prove that road/sidewalk/soil meshes meet without gaps.

Author polygons for camera-visible road, sidewalk, plaza and terrain regions. Sample each region and fail when:

- no render triangle covers a sample;
- the topmost visible triangle is an excluded substrate or fallback material;
- the visible surface class is not allowed for that region.

Use a sample step smaller than the smallest seam the shipping camera can reveal. Deterministic sampling finds holes; raw target-build close-ups remain required because z-fighting, shader displacement, decals, transparency, LOD and filtering can create defects outside this geometry model.

Godot export sketch:

```gdscript
func emit_mesh_faces(mesh_instance: MeshInstance3D) -> Array[Dictionary]:
    var result: Array[Dictionary] = []
    var mesh := mesh_instance.mesh
    for surface in mesh.get_surface_count():
        var tool := MeshDataTool.new()
        tool.create_from_surface(mesh, surface)
        for face in tool.get_face_count():
            var vertices: Array[Vector3] = []
            for corner in 3:
                var local := tool.get_vertex(tool.get_face_vertex(face, corner))
                vertices.append(mesh_instance.global_transform * local)
            result.append({"vertices": vertices})
    return result
```

If a ground system cannot be read through `MeshDataTool`, export equivalent final render triangles from `ArrayMesh.surface_get_arrays()` or the source terrain data. Record the derivation and do not fall back to physics geometry without declaring the gate NOT TESTED.

## Check vertical clearance separately

Horizontal overlap can be correct when one object passes above another. Define class-pair clearance rules for signs, wires, lamp arms, bridges, awnings, pipes, towers and adjacent facade volumes. When the transformed XZ footprints overlap, require:

```text
upper.min_y - lower.max_y >= minimum_gap
```

Use the actual clearance needed by the lower object, its animation and the shipping camera read. A wire touching a tank, a sign entering a facade, a lamp shaft through a car or a tower frame entering a roof fails even when every prop has a correct collider.

## Raw target-build close-up matrix

The deterministic report and visual evidence are one gate, not alternatives. Preserve exact shipping-build close-ups at the final camera, lighting and viewport for:

1. transformed prop-to-prop occupancy;
2. semantic surface ownership;
3. ground coverage/seams;
4. vertical clearance;
5. an ordinary environment-integrity overview.

For every defect class detected during the iteration, keep a representative before frame, the fixed after frame, and the clean rerun row. Do not crop away the contact context. If no defect was detected in a class, still capture its highest-risk representative state.

The gate fails when the audit has an error, a visible prop is missing required proxies, a surface rule is unexercised, a detected class lacks before/fixed/rerun evidence, an exemption is vague or stale, or the raw build still shows fusion, penetration, floating contact, roadway nature props, or exposed substrate.

## Engine references

- [Godot `Transform3D`](https://docs.godotengine.org/en/stable/classes/class_transform3d.html) defines the basis-plus-origin transform used to resolve local points into world space.
- [Godot `AABB`](https://docs.godotengine.org/en/stable/classes/class_aabb.html) documents transformed bounds and their role in fast overlap work; this contract decomposes complex props instead of trusting one coarse bound.
- [Godot `VisualInstance3D.get_aabb()`](https://docs.godotengine.org/en/stable/classes/class_visualinstance3d.html) exposes local visual bounds that can seed authored proxies.
- [Godot `MeshDataTool`](https://docs.godotengine.org/en/stable/classes/class_meshdatatool.html) exposes mesh vertices and triangular faces for render-ground sampling.
- [Godot ray-casting guide](https://docs.godotengine.org/en/stable/tutorials/physics/ray-casting.html) explains direct-space physics queries and global coordinates. These are useful supplemental runtime checks, but physics hits are not render-surface coverage proof.
- [Godot `PhysicsDirectSpaceState3D`](https://docs.godotengine.org/en/stable/classes/class_physicsdirectspacestate3d.html) and [`PhysicsShapeQueryParameters3D`](https://docs.godotengine.org/en/stable/classes/class_physicsshapequeryparameters3d.html) cover runtime shape queries when testing gameplay clearance in addition to the render-integrity contract.
