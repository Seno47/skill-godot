# High-angle 3D Environment Integrity Review

Use this builder-owned review with `references/3d-environment-integrity.md`. It supplements collision, boundary, navigation, district composition and independent visual review; none of those substitutes for it.

## Candidate and provenance

- Build/revision/hash:
- Composite rubric selector:
- Exact target executable/export:
- Target camera, viewport, renderer and lighting:
- Resolved root scene SHA-256 (diagnostic only):
- Resolved dependency-closure digest (candidate revision):
- Dependency manifest path + SHA-256:
- Provenance exporter path + SHA-256:
- Geometry/coverage exporter paths + SHA-256:
- Export preset selector + `export_presets.cfg` SHA-256:
- Godot version + `project.godot` SHA-256:
- Recursive `ResourceLoader` dependencies / explicit runtime dependencies:
- Filesystem or exported-project manifest verification result:
- Baseline comparison when nested dependencies changed:
- Resolved visible-prop group/query and skipped-node ledger:
- Contract JSON:
- Local contract schema (must be v2) / migration source if applicable:
- Audit JSON/stdout:
- Whole-map coverage contract JSON:
- Whole-map coverage audit JSON/stdout:
- Raw capture root:
- Builder/context:

| Coverage | Expected | Resolved/result | PASS/FAIL/NOT TESTED |
|---|---:|---:|---|
| Visible prop instances requiring occupancy | | | NOT TESTED |
| Local occupancy volumes transformed by final `global_transform` | | | NOT TESTED |
| Props requiring semantic support footprints | | | NOT TESTED |
| Actual visible ground mesh triangles | | | NOT TESTED |
| Surface sample step / smallest illegal incursion | | | NOT TESTED |
| Ground sample step / smallest visible seam | | | NOT TESTED |
| Collision coverage (context only) | | | NOT TESTED |
| Boundary coverage (context only) | | | NOT TESTED |
| Playable surface-zone cells | | | NOT TESTED |
| Shipping-camera survey cells/captures | | | NOT TESTED |
| All enabled static colliders / visible shells | | | NOT TESTED |
| Production occluder collision roots / alias traces | | | NOT TESTED |
| Root + recursive/runtime dependency entries | | | NOT TESTED |
| Toolchain inputs (preset/project/provenance + evidence exporters) | | | NOT TESTED |

## Resolved dependency-closure provenance

| Input class | Canonical paths/records | Count | Hash verification | PASS/FAIL/NOT TESTED |
|---|---|---:|---|---|
| Root scene | | 1 | | NOT TESTED |
| Direct/recursive `ResourceLoader` dependencies | | | | NOT TESTED |
| Runtime-loaded production dependencies | | | | NOT TESTED |
| Provenance and evidence exporters | | | | NOT TESTED |
| Project settings and selected export preset | | | | NOT TESTED |

- Root SHA-256:
- Computed closure digest:
- Manifest SHA-256:
- Both evidence contracts match build/root/closure/manifest/exporter/preset:
- Root unchanged but nested dependency changed comparison (if applicable):
- Equivalent exported-project manifest + exact artifact hash (only when source-workspace verification is unavailable):

## Transformed prop-to-prop occupancy

| Pair/class | Full transformed volumes | Horizontal/Y penetration | Contact mode + XZ normal | Interface/mount/deformation geometry | Before raw close-up | Fixed raw close-up | Clean rerun | PASS/FAIL/NOT TESTED |
|---|---|---:|---|---|---|---|---|---|
| | | | | | | | | NOT TESTED |

- Complex/open shapes decomposed instead of one coarse AABB:
- MultiMesh per-instance transforms resolved:
- Render/collision shell differences recorded:
- Any non-participating visible instance has an exact reason and raw-artifact exemption:
- Stale or class-wide exemptions present:
- Vehicle↔fence/barrier/cordon undeformed penetration stays within epsilon:
- Larger intentional penetration has bounded `deformed_connector` mode and visible interface geometry:
- Exported penetration/contact normal matches the auditor's resolved measurement:

## Semantic prop-to-surface ownership

| Prop class/instance | Allowed visible surface classes | Full support footprint samples | Wrong/missing surface samples | Before raw close-up | Fixed raw close-up | Clean rerun | PASS/FAIL/NOT TESTED |
|---|---|---:|---:|---|---|---|---|
| Nature tree/rock/bush | grass/soil or authored equivalent | | | | | | NOT TESTED |
| Vehicle | road/parking/wreck bed | | | | | | NOT TESTED |
| Road debris | declared road/debris surface | | | | | | NOT TESTED |
| Facade furniture | sidewalk/apron/foundation | | | | | | NOT TESTED |

- Origin-only placement checks rejected:
- Every applicable semantic class has an authored rule:
- Full footprints remain inside their owned surfaces in edge/curb cases:

## Visible ground coverage and seams

`render_ground_source` must be `mesh_faces`. A broad floor collider, navigation plane or hidden catch-all floor is not evidence here.

| Camera-visible region | Allowed top surfaces | Excluded substrate/fallback | Mesh sample count | Gap/wrong-top samples | Before raw close-up | Fixed raw close-up | Clean rerun | PASS/FAIL/NOT TESTED |
|---|---|---|---:|---:|---|---|---|---|
| | | | | | | | | NOT TESTED |

- Actual final render triangles and transforms exported:
- Triangular boundaries, T-junctions, decals/terrain joins and elevation changes sampled:
- Shader/LOD/transparency risks not modeled by triangles reviewed visually:

## Whole-map semantic surface topology

| Zone | Role: primary/transition | Expected family/classes | Fallback classes + maximum ratio | Measured fallback | Adjacent zones | Authored transition/cause | Raw artifact | PASS/FAIL/NOT TESTED |
|---|---|---|---|---:|---|---|---|---|
| | | | | | | | | NOT TESTED |

- Playable footprint cells owned by exactly one zone: / total
- Uncovered or multiply owned cells:
- Observed adjacency pairs / declared exercised rules:
- Broad region accepting incompatible semantic families rejected:
- Rectangular/T-shaped patchwork and abrupt joins reviewed at shipping scale:

## Deterministic shipping-camera tiled survey

| Survey tile/capture | Shipping camera node/position | Derived visible footprint | Covered cells | Raw full-resolution artifact | Contact-sheet position | PASS/FAIL/NOT TESTED |
|---|---|---|---:|---|---|---|
| | | | | | | NOT TESTED |

- Required survey cells:
- Covered cells:
- Uncovered cells (must be zero):
- Coverage ratio / required ratio:
- Duplicate/free-camera/mismatched-build artifacts:

## All enabled static colliders versus visible shells

| Collider ID/source | Enabled | Variant | Mapped visible shell IDs | Footprint/height overlap ratio | Hero-radius invisible samples | Raw overlay | PASS/FAIL/NOT TESTED |
|---|---|---|---|---:|---:|---|---|
| | | | | | | | NOT TESTED |

- Enabled static colliders enumerated / expected:
- Visible render shells enumerated / expected:
- Total hero-radius blocked samples:
- Invisible blocked samples (must be zero unless exact boundary exemption):
- Disabled collider/hidden render variant symmetry:

## Production-scene occluder alias coverage

| Production collision root | Stable aliases | Resolved visual root IDs | Observed fade | Observed restore | Raw production-scene trace | PASS/FAIL/NOT TESTED |
|---|---|---|---:|---:|---|---|
| | | | | | | NOT TESTED |

- Expected collision roots / mapped roots:
- Synthetic-only cases rejected:
- Missing/ambiguous/fuzzy aliases:

## Topmost surface/object-pair relationships

| Object class/instance | Topmost surface class | Maximum permitted footprint ratio | Measured ratio | Physical rule | Raw contact artifact | PASS/FAIL/NOT TESTED |
|---|---|---:|---:|---|---|---|
| Vehicle / curb | | 0 | | | | NOT TESTED |
| Vehicle / pole or parking stop | | | | | | NOT TESTED |
| Pole / road lane | | | | | | NOT TESTED |

## Vertical clearance

| Upper/lower classes and instances | XZ overlap | Required gap | Measured gap | Before raw close-up | Fixed raw close-up | Clean rerun | PASS/FAIL/NOT TESTED |
|---|---:|---:|---:|---|---|---|---|
| Sign / facade or route | | | | | | | NOT TESTED |
| Wire / tank, vehicle or facade | | | | | | | NOT TESTED |
| Pole/lamp/pipe / vehicle | | | | | | | NOT TESTED |
| Tower/awning/bridge / building or route | | | | | | | NOT TESTED |

## Exact target-build raw state matrix

Use the shipping camera, ordinary HUD, final lighting and final visible assets. Preserve one before/fixed/rerun sequence for every defect class discovered during production.

| Required state | Raw artifact | Build match | Builder observation | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|
| `transformed_prop_occupancy` | | | | NOT TESTED |
| `intentional_contact_plausibility` | | | | NOT TESTED |
| `semantic_surface_ownership` | | | | NOT TESTED |
| `render_ground_coverage_and_seams` | | | | NOT TESTED |
| `vertical_clearance` | | | | NOT TESTED |
| `detected_class_closeups_and_resolution` | | | | NOT TESTED |
| `environment_integrity_overview` | | | | NOT TESTED |
| `surface_zone_topology` | | | | NOT TESTED |
| `shipping_camera_tiled_survey` | | | | NOT TESTED |
| `all_static_collider_visible_shell` | | | | NOT TESTED |
| `production_occluder_aliases` | | | | NOT TESTED |
| `surface_object_pair_relationships` | | | | NOT TESTED |
| `resolved_dependency_closure_provenance` | | | | NOT TESTED |

## Regression-negative rejection

- Collision coverage is complete but a visible sign/facade, wire/tank, tower/building or lamp/car penetration remains: PASS / FAIL / NOT TESTED
- Every prop origin is legal but a tree/rock/bush support footprint crosses road/sidewalk: PASS / FAIL / NOT TESTED
- Broad floor collider is complete but visible triangular ground gaps expose substrate: PASS / FAIL / NOT TESTED
- Intentional-overlap exemption lacks an exact pair, physical reason and raw artifact: PASS / FAIL / NOT TESTED
- Vehicle/barrier exemption has persuasive prose but exceeds undeformed penetration epsilon or lacks deformed connector geometry: PASS / FAIL / NOT TESTED
- Audit PASS is claimed without raw target-build close-ups, or screenshots PASS without a clean audit rerun: PASS / FAIL / NOT TESTED
- One broad ground region accepts incompatible surface families or hides excess fallback exposure: PASS / FAIL / NOT TESTED
- Curated raw states leave playable survey cells uncovered: PASS / FAIL / NOT TESTED
- Enabled static collider lacks corresponding visible shell/hero-radius silhouette: PASS / FAIL / NOT TESTED
- Production occluder fixture passes but a resolved collision root lacks an alias/visual mapping or restoration trace: PASS / FAIL / NOT TESTED
- Surface class is mechanically allowed but its topmost face physically fuses with a vehicle/pole/curb pair: PASS / FAIL / NOT TESTED
- Root `.tscn` SHA is unchanged while a nested instantiated scene changes, but the candidate reuses the prior closure digest: PASS / FAIL / NOT TESTED
- `resolved_target_scene` supplies only `scene_revision`/root hash or omits a discovered/runtime dependency, exporter or preset input: PASS / FAIL / NOT TESTED

## Builder-owned verdict

- Deterministic environment-integrity audit: PASS / FAIL / NOT TESTED
- Transformed full-footprint occupancy: PASS / FAIL / NOT TESTED
- Strict intentional-contact plausibility: PASS / FAIL / NOT TESTED
- Semantic surface ownership: PASS / FAIL / NOT TESTED
- Visible render-ground coverage/seams: PASS / FAIL / NOT TESTED
- Vertical clearance: PASS / FAIL / NOT TESTED
- Detected-class before/fixed/rerun packet: PASS / FAIL / NOT TESTED
- Whole-map semantic zones, fallback and adjacency: PASS / FAIL / NOT TESTED
- Zero-gap shipping-camera tiled survey: PASS / FAIL / NOT TESTED
- All-enabled collider/render-shell hero-radius parity: PASS / FAIL / NOT TESTED
- Production occluder aliases and fade/restoration: PASS / FAIL / NOT TESTED
- Topmost surface/object-pair constraints: PASS / FAIL / NOT TESTED
- Resolved dependency-closure provenance and contract linkage: PASS / FAIL / NOT TESTED
- Overall `high_angle_environment_integrity_evidence`: PASS / FAIL / NOT TESTED
- Blocking defects and disposition:
- Remaining evidence boundary:

A PASS requires zero audit errors plus the complete raw matrix. `164/164` prop collision, `180/180` boundary samples, collider alignment, navigation and scene validity are supporting context only and cannot rescue a visible-integrity FAIL.
