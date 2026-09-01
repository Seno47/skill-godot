# 3D Environment Integrity

Use this contract for dense 3D dressing, especially fixed/high-angle districts where the shipping camera exposes contacts, silhouettes and ground coverage. It closes a different question from gameplay collision: collision coverage proves that gameplay has physical boundaries; environment integrity proves that visible objects do not penetrate one another, belong to the surface they occupy, clear overhead structures, and cover the rendered ground without holes.

For `high-angle-3d-district-complete`, this is a builder-owned blocking gate. Instantiate `assets/resolved-scene-provenance.template.json`, both environment contract templates and `assets/environment-integrity-review.template.md`. When roads/sidewalks/intersections or street furniture exist, also use [road-and-streetscape-semantics.md](road-and-streetscape-semantics.md); geometry coverage cannot certify street topology or placement meaning. First copy `assets/godot-tests/resolved_scene_provenance_exporter.gd` into the project, adapt its runtime/tool inputs and export the dependency closure:

```bash
godot --headless --path . \
  --script res://tests/resolved_scene_provenance_exporter.gd -- \
  --root-scene res://scenes/world/OldClinicDistrict.tscn \
  --output reports/resolved-scene-provenance.json \
  --build-id old-clinic-map-008-v19 \
  --export-preset "Windows Desktop" \
  --tool-input environment_integrity_exporter=res://tests/environment_integrity_exporter.gd \
  --tool-input environment_coverage_exporter=res://tests/environment_coverage_exporter.gd \
  --tool-input streetscape_semantics_exporter=res://tests/streetscape_semantics_exporter.gd
```

Then independently recompute and, in the source workspace, verify every declared file hash. Link every applicable exact evidence contract so a passing manifest cannot belong to a different build/exporter:

```bash
python scripts/resolved_scene_provenance_audit.py \
  --manifest reports/resolved-scene-provenance.json \
  --project . \
  --evidence-contract reports/environment-integrity-contract.json \
  --evidence-contract reports/environment-coverage-contract.json \
  --evidence-contract reports/streetscape-semantics-contract.json \
  --json-output reports/resolved-scene-provenance-audit.json \
  --summary
```

After that, export the resolved target-scene geometry and run:

```bash
python scripts/environment_integrity_audit.py \
  --model reports/environment-integrity-contract.json \
  --json-output reports/environment-integrity-audit.json \
  --summary
```

The command must return PASS. Collision coverage, boundary coverage, navigation, origins inside legal polygons, or one overview screenshot cannot substitute for it.

The local integrity contract is schema v2. Migrate v1 by adding the contact measurement tolerance, strict pair rules, resolved contact-interface query/manifest, and measured fields to every intentional overlap, then re-export and rerun. Renaming the schema without regenerating resolved measurements is not a migration.

Local integrity is only the first half of the gate. Also instantiate `assets/environment-coverage-contract.template.json` and run the whole-map contract:

```bash
python scripts/environment_coverage_audit.py \
  --model reports/environment-coverage-contract.json \
  --json-output reports/environment-coverage-audit.json \
  --summary
```

The coverage contract is schema v2. Migrate v1 by re-exporting the complete visible physics-subject inventory: semantic class, `physics_role`, reciprocal collider IDs, exact expected class counts and evidence-backed non-solid classifications. Renaming an old report is not a migration. The audit prevents a curated set of good contacts, a one-way collider check or one permissive ground polygon from hiding defects elsewhere in the playable footprint.

## Bind evidence to the resolved dependency closure

A SHA-256 of only the root `.tscn` is not a candidate revision. Instantiated sub-scenes, external materials, meshes, scripts and imported source assets can change without modifying that root file. For `source_kind: resolved_target_scene`, record:

- the canonical `res://` root scene;
- direct and recursive paths returned by Godot `ResourceLoader.get_dependencies()` after import, resolving both plain paths and `UID::type::fallback_path` strings;
- production resources loaded indirectly at runtime through an explicit stable registry/`--runtime-dependency` ledger;
- sorted path, kind, byte count and SHA-256 for the root plus every discovered/runtime dependency;
- Godot version, exact export-preset selector, whole `export_presets.cfg` hash, `project.godot` hash, provenance-exporter hash and every geometry/evidence exporter hash;
- a closure digest recomputed from the canonical sorted records, plus the SHA-256 of the completed manifest itself.

Every environment/streetscape contract must use `revision_kind: resolved_dependency_closure_sha256` and repeat the same closure digest, manifest hash and export-preset selector/hash while naming its own hashed exporter. `resolved_scene_provenance_audit.py --evidence-contract ...` verifies those links. A legacy `scene_revision`, a root-only entry while discovered dependencies exist, missing runtime-loaded production resources, stale closure digest, unhashed exporter/preset or a contract referring to a different manifest fails closed.

The dependency set may safely be a documented superset (for example, include disabled external variants) but may not omit any resource that can participate in the exact resolved candidate. Resource paths assembled dynamically in scripts are not discoverable merely by walking serialized resource dependencies; enumerate them explicitly or export an equivalent project-owned runtime registry. For packed/exported-only evidence, an exported-project manifest is acceptable only when it gives equivalent canonical dependency/tool hashes and binds them to the exact PCK/ZIP/executable artifact hash; a source root hash is not an exported-build manifest.

When comparing candidates, preserve the prior manifest and pass it as `--baseline`. If the root scene hash stays constant but one nested dependency changes, the computed closure digest must change. The bundled v18/v19 regression fixture encodes exactly this case and rejects a v19 report that reuses the v18 digest.

## Author resolved occupancy, not origin checks

Have a project-owned exporter traverse the final instantiated target scene using a stable group/query and emit the scene path, dependency-closure digest, manifest/exporter hashes and resolved visible-prop count. Do not curate only the props already suspected of failing. Give every visible prop that can penetrate another prop one or more local occupancy boxes. Use multiple boxes for an L-shaped building, tower legs, a lamp head/shaft, a vehicle body, or geometry with a deliberate opening. A single oversized AABB creates false positives around empty holes; an origin test creates false negatives around every wide or rotated prop.

Also export every mount/damage/deformation mesh reachable through the declared `contact_interface_query`; `interface_geometry_ids` in an exemption must resolve against that manifest. A plausible-looking path string is not evidence that connector geometry exists.

Export the final `global_transform` as Godot basis columns plus origin and transform all eight box corners. The audit builds the transformed XZ convex footprint, preserves the transformed vertical range, and applies a separating-axis test plus Y penetration. This covers translation, rotation, non-uniform scale and parent transforms. For `MultiMeshInstance3D`, compose the node transform with every instance transform and emit a stable instance ID.

An intentional contact or authored mount needs an exact instance/volume pair exemption with:

- the checks being exempted (`occupancy` and/or `vertical_clearance`);
- a concrete physical reason;
- the contact mode, measured horizontal/Y penetration and XZ contact normal;
- any separate interface, mount, damage or deformation geometry IDs;
- a raw target-build close-up;
- a still-current overlap. Stale exemptions fail, and class-wide ignores are forbidden.

The exporter supplies measurements; the auditor recomputes them from the resolved volumes and rejects a mismatch. High-risk class pairs use `strict_contact_pair_rules`. For `vehicle` against `fence`, `barrier` or `cordon`, `touch`, `braced` and `seated` modes permit only the project epsilon for numerical contact—an exact reason cannot excuse visible render-shell penetration. A larger overlap needs `deformed_connector`, a bounded damaged-contact budget and named connector/deformation geometry that visually explains the interface. Preserve the close-up at gameplay lighting. This prevents `intentionally braced against bumper` from turning a 0.09–0.20 m intersection into a PASS.

Use Godot's [`PhysicsDirectSpaceState3D.get_rest_info()`](https://docs.godotengine.org/en/stable/classes/class_physicsdirectspacestate3d.html) when runtime contact point/normal evidence helps, but keep the render-volume separating-axis measurement because gameplay collision alone does not prove visible plausibility.

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

### Partition the footprint into semantic zones

Do not use one whole-map region that accepts road, sidewalk, grass, soil, concrete and fallback merely to reach 100% sample coverage. The whole-map coverage contract requires:

- one declared playable footprint with no uncovered or multiply owned sample cells;
- semantic surface families such as transport, pedestrian, nature, structural transition and fallback;
- primary zones whose expected top-surface classes belong to exactly one family;
- explicit transition zones for graded joins, or a hard-boundary rule with a visible physical/story cause;
- a maximum fallback/substrate exposure ratio per zone;
- every observed zone adjacency to match one exercised transition/cause rule.

This rejects mechanically valid but visually arbitrary rectangular or T-shaped patchwork. A transition band must be wide enough for the declared sampling grid and visible in the shipping camera; an adjacency ledger cannot legalize a missing mesh or an unexplained material cut.

### Check surface and object together

Semantic permission is not physical permission. A vehicle may be generally allowed on `road` and `concrete`, yet a raised curb passing through its support footprint is still impossible. Add `surface_object_pair_rules` for relationships such as:

- vehicle / curb or parking stop;
- vehicle / painted island, pole foundation or sidewalk lip;
- pole / road lane;
- facade prop / roof or planter edge.

The whole-map audit samples the object's support footprint, resolves the topmost render face, and caps the permitted ratio for the exact object-class/surface-class pair. Use ordinary occupancy volumes as well when the curb, pole or other surface feature has meaningful vertical mass.

## Survey the complete footprint with the shipping camera

Curated entry/dense/objective frames do not prove the spaces between them. Derive a deterministic grid over the declared playable footprint, move the actual shipping camera rig through authored survey positions, and export for every capture:

- the exact camera node and world position;
- the ground footprint visible through the final projection/angle;
- a unique raw target-build image;
- its tile/cell coverage in the contact sheet manifest.

Every required grid cell must be covered by at least one raw frame; the default required ratio is `1.0`. Preserve a contact sheet for fast review, but retain the individual full-resolution captures. A contact sheet assembled from duplicate, free-camera or mismatched-build images fails.

Use `Camera3D.project_ray_origin()` and `project_ray_normal()` at deterministic viewport sample points, or an equivalent project-owned projection method, to derive coverage. Do not estimate coverage only from camera focus positions. For multi-level maps, declare a footprint per relevant elevation or split the contract by layer.

## Prove collider/render parity in both directions

Known-prop collision checks are insufficient. The exporter must enumerate every resolved `StaticBody3D`/shape owner and every camera-visible physics subject in the production scene, including instantiated and generated children. The visible inventory is exporter-owned and exact by semantic class: buildings, fences, barrels, hydrants, vehicles, poles and any other visually solid obstruction cannot disappear from it merely because no collider points back to them. Record disabled state symmetrically with the authored visual variant.

For each enabled collider:

- map it to one or more exact visible render-shell IDs;
- compare sampled collider footprint/height with those shells;
- raster the playable footprint at the declared hero radius and vertical body interval;
- require every blocked hero-center sample to have visible mass explaining the obstruction;
- reject enabled-collider/hidden-shell and disabled-collider/visible-shell variant mismatches.

Then run the reverse proof for every `physics_role: solid_blocker` render shell:

- require one or more reciprocal collider IDs, with both sides naming each other;
- require the visible state to map to enabled hero-blocking collision and the hidden state to the disabled authored variant;
- sample the transformed render footprint/height and meet `minimum_collider_overlap_ratio` against the mapped colliders;
- compare the exact visible semantic-class counts with the exporter-owned expected inventory.

This second direction catches a visible barrel, fence section or facade that the player can walk through even when every existing collider has a valid visible shell. Collider-to-shell and shell-to-collider are separate assertions; neither implies the other.

Fire, smoke, sparks, mist, particle cards and similar child meshes are visual evidence but normally not occupancy. Classify them explicitly as `visual_effect_non_solid`, declare their semantic classes in `visual_effect_classes`, keep their collider list empty and attach a reason plus raw shipping-camera artifact. Other non-solid decoration uses `decorative_non_solid` with the same evidence rule. Non-solid subjects remain in the exact visible inventory and screenshots but are excluded from collider overlap, variant parity and hero-radius occupancy; a collider referencing them fails. Do not omit effects from traversal or pretend that an effect is a solid shell to make counts agree.

A duplicate traffic-light pole collider, old hidden wall or disabled visual variant therefore cannot remain as an invisible blocker merely because collision coverage is numerically complete. Overhead colliders outside the declared hero vertical interval still require render-shell parity but do not become false ground blockers. Camera-only proxies or deliberately invisible safety barriers need `blocks_hero: false` plus an exact reason/raw-artifact exemption; a hero-blocking collider can never use that exemption. Use multiple render-shell volumes for geometry with holes.

In Godot, enumerate shape owners from the resolved `CollisionObject3D` rather than assuming one `CollisionShape3D` child or matching names. Record `CollisionShape3D.disabled`, final transforms and shape-owner ownership. Seed render shells from final visible `VisualInstance3D` bounds/mesh geometry, not collision shapes.

## Prove visible-first contact along the whole perimeter

Collider/render-shell parity and a flood-fill with zero reachable safety-wall pockets still do not prove contact order at every point. A broad invisible wall may protrude in front of a truck, facade or cordon for a few meters while every grid cell remains unreachable from behind. Whenever a high-angle map keeps a safety-only blocker behind visible boundary art, instantiate `assets/visible-first-boundary-contract.template.json`, export it with a transient QA adapter through `assets/godot-tests/visible_first_boundary_probe.gd`, then run:

```bash
python <skill-dir>/scripts/visible_first_boundary_audit.py \
  --model reports/visible-first-boundary-contract.json \
  --json-output reports/visible-first-boundary-audit.json \
  --summary
```

Schema v2 has two independent layers. The adapter still declares the perimeter spans and ordered first-hit queries, but it may not declare the reachability grid. Author exactly one production-scene `production_boundary_reachability_region` with the required grid/query metadata, group the real hero body, enabled capsule shape and production starts as described in the exporter header, and let the exporter query the resolved `World3D` itself. The report must contain every grid cell, a nonempty unsafe fringe on the declared sides, the scene-owned safe polygon, actual ground and blocker masks, and an eight-neighbor fail-closed flood fill from the production starts. Grid cell size may not exceed the project ratio of the production hero radius. Hand-written `free_cells`, `blocked_cells`, `outside_cells`, a hard-coded rectangular boundary, an empty outside set or a grid too coarse to see a hero-width passage is not evidence.

Declare every enabled perimeter span, not just road corridors or the places already visible in curated captures. Deterministically sample each span from endpoint to endpoint with spacing no greater than the production hero diameter, point each query inward-to-outward, and preserve exact ordered hits. A production-size capsule sweep is preferred. A ray implementation passes only as a full-width bundle whose lateral gaps are no larger than the declared hero-radius budget; one center ray cannot represent a character body. The exporter-owned whole-body flood fill must independently prove that the actual production capsule reaches zero unsafe-fringe cells while expected in-map free cells remain connected.

Every probe must contact a collider mapped to an exact visible cause and render shell first. A safety-only collider may appear only behind that cause and beyond the declared clearance margin. The resolved manifest must enumerate every safety collider and visible mapping, every span/sample index must be exercised, and openings/exits must remain declared open rather than being silently treated as closed boundary. Maintain a baseline/current visible-limiter ledger: retain each visible house, vehicle cordon, wall, cliff or equivalent limiter, or name replacement visible causes and preserve before/fixed/current whole-body plus first-hit continuity proof. Deleting a limiter and calling the newly open off-map route a fix is a FAIL. Bind the trace, grid, limiter ledger, span close-ups and exporter to the same build and dependency-closure digest. Zero reachable pockets, `180/180 blocked`, a visible object name, or an export-preset exclusion does not substitute for first-hit ownership.

## Resolve production occluder aliases, not synthetic names

Synthetic obstruction fixtures can pass while the production collision and visual roots use different names. Export the exact production-scene collision-root set and maintain an inspectable mapping:

```text
production collision root -> stable aliases -> one or more production visual root IDs
```

Every expected collision root must be mapped, every target visual root must exist and be visible, aliases must be unique, and every mapping must have a production-scene trace proving the declared fade value and full restoration. A synthetic test scene, matching count, prefix heuristic or manually invoked fade method cannot replace resolved production names and real collision-driven dispatch.

Prefer stable groups or authored IDs for lookup. Human-readable aliases handle imported/root-name differences but must not become fuzzy substring matching.

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

Clearance does not prove support. When roads/streetscape exist, the schema-v6 streetscape layer separately enumerates every visible canopy/awning/support mesh from the exporter-owned scene traversal. Ground contact uses resolved support vertices against topmost render surfaces; facade/suspension contact uses resolved support vertices against named mount-mesh triangles and recomputes 3D gaps. A scalar adapter value is not evidence. A floating awning can pass every overhead-clearance rule and must still fail the support-contact gate.

## Raw target-build close-up matrix

The deterministic report and visual evidence are one gate, not alternatives. Preserve exact shipping-build close-ups at the final camera, lighting and viewport for:

1. transformed prop-to-prop occupancy;
2. semantic surface ownership;
3. ground coverage/seams;
4. vertical clearance;
5. an ordinary environment-integrity overview.
6. a complete shipping-camera tiled-survey contact sheet with zero uncovered cells;
7. bidirectional solid-render-shell/collider inventory, overlap and hero-radius raster overlays;
8. production occluder alias fade/restoration motion;
9. high-risk topmost-surface/object-pair contacts.
10. the whole-perimeter visible-first contact sheet, exporter-owned production-capsule grid/contact sheet and exact detected-span close-ups;
11. the visible-limiter baseline/current continuity ledger and replacement close-ups where applicable;
12. every strict intentional-contact pair, including the undeformed-clear or authored-deformation interface state.
13. representative non-solid fire/smoke/particle classes in the same target-build visual state, with their exclusion from physics recorded.

For every defect class detected during the iteration, keep a representative before frame, the fixed after frame, and the clean rerun row. Do not crop away the contact context. If no defect was detected in a class, still capture its highest-risk representative state.

The gate fails when any applicable audit has an error, a visible prop is missing required proxies, a visible solid blocker lacks reciprocal enabled hero collision, a collider lacks visible shell/raster support, a non-solid effect is omitted or participates in occupancy, one semantic zone accepts incompatible families, fallback exceeds its zone budget, any playable/survey/perimeter sample is uncovered, an observed adjacency lacks a transition/cause, the production capsule reaches an unsafe-fringe cell, a limiter disappears without mapped visible replacement continuity, a safety wall is contacted before its mapped visible cause, visible-to-safety clearance is too small, a disabled/hidden variant is asymmetric, a production occluder root or trace is missing, a surface/object rule fails, a detected class lacks before/fixed/rerun evidence, an exemption is vague/stale, a strict contact exceeds its undeformed/deformed budget or lacks a plausible interface, or the raw build still shows fusion, pass-through solids, penetration, floating contact, abrupt patchwork, roadway nature props, invisible blockers or exposed substrate.

## Engine references

- [Godot `Transform3D`](https://docs.godotengine.org/en/stable/classes/class_transform3d.html) defines the basis-plus-origin transform used to resolve local points into world space.
- [Godot `AABB`](https://docs.godotengine.org/en/stable/classes/class_aabb.html) documents transformed bounds and their role in fast overlap work; this contract decomposes complex props instead of trusting one coarse bound.
- [Godot `VisualInstance3D.get_aabb()`](https://docs.godotengine.org/en/stable/classes/class_visualinstance3d.html) exposes local visual bounds that can seed authored proxies.
- [Godot `MeshDataTool`](https://docs.godotengine.org/en/stable/classes/class_meshdatatool.html) exposes mesh vertices and triangular faces for render-ground sampling.
- [Godot ray-casting guide](https://docs.godotengine.org/en/stable/tutorials/physics/ray-casting.html) explains direct-space physics queries and global coordinates. These are useful supplemental runtime checks, but physics hits are not render-surface coverage proof.
- [Godot `PhysicsDirectSpaceState3D`](https://docs.godotengine.org/en/stable/classes/class_physicsdirectspacestate3d.html) and [`PhysicsShapeQueryParameters3D`](https://docs.godotengine.org/en/stable/classes/class_physicsshapequeryparameters3d.html) cover runtime shape queries when testing gameplay clearance in addition to the render-integrity contract.
- [Godot `CollisionObject3D`](https://docs.godotengine.org/en/stable/classes/class_collisionobject3d.html) exposes shape-owner enumeration needed to audit every resolved collider instead of only named child nodes.
- [Godot groups](https://docs.godotengine.org/en/stable/tutorials/scripting/groups.html) provide stable production registries for visible props and camera occluders.
- [Godot `Camera3D`](https://docs.godotengine.org/en/stable/classes/class_camera3d.html) provides projection rays and frustum utilities used to derive deterministic shipping-camera survey coverage.
- [Godot `ResourceLoader.get_dependencies()`](https://docs.godotengine.org/en/stable/classes/class_resourceloader.html#class-resourceloader-method-get-dependencies) exposes direct resource dependencies and documents both plain-path and UID/fallback-path result forms used by the recursive exporter.
- [Godot `FileAccess.get_sha256()`](https://docs.godotengine.org/en/stable/classes/class_fileaccess.html#class-fileaccess-method-get-sha256) hashes source inputs in the editor workspace and returns an empty string on failure, which the exporter treats as blocking.
- [Godot `ProjectSettings.globalize_path()`](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html#class-projectsettings-method-globalize-path) explains source-workspace path resolution and its exported-project limitation; this is why exact packed-build provenance needs an exported-project manifest/artifact hash rather than assuming source paths survive unchanged in a PCK.
