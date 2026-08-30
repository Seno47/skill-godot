# High-angle 3D Environment Integrity Review

Use this builder-owned review with `references/3d-environment-integrity.md`. It supplements collision, boundary, navigation, district composition and independent visual review; none of those substitutes for it.

## Candidate and provenance

- Build/revision/hash:
- Composite rubric selector:
- Exact target executable/export:
- Target camera, viewport, renderer and lighting:
- Resolved scene/exporter revision:
- Resolved visible-prop group/query and skipped-node ledger:
- Contract JSON:
- Audit JSON/stdout:
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

## Transformed prop-to-prop occupancy

| Pair/class | Full transformed volumes | Horizontal/Y penetration | Intentional? exact exemption + reason | Before raw close-up | Fixed raw close-up | Clean rerun | PASS/FAIL/NOT TESTED |
|---|---|---:|---|---|---|---|---|
| | | | | | | | NOT TESTED |

- Complex/open shapes decomposed instead of one coarse AABB:
- MultiMesh per-instance transforms resolved:
- Render/collision shell differences recorded:
- Any non-participating visible instance has an exact reason and raw-artifact exemption:
- Stale or class-wide exemptions present:

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
| `semantic_surface_ownership` | | | | NOT TESTED |
| `render_ground_coverage_and_seams` | | | | NOT TESTED |
| `vertical_clearance` | | | | NOT TESTED |
| `detected_class_closeups_and_resolution` | | | | NOT TESTED |
| `environment_integrity_overview` | | | | NOT TESTED |

## Regression-negative rejection

- Collision coverage is complete but a visible sign/facade, wire/tank, tower/building or lamp/car penetration remains: PASS / FAIL / NOT TESTED
- Every prop origin is legal but a tree/rock/bush support footprint crosses road/sidewalk: PASS / FAIL / NOT TESTED
- Broad floor collider is complete but visible triangular ground gaps expose substrate: PASS / FAIL / NOT TESTED
- Intentional-overlap exemption lacks an exact pair, physical reason and raw artifact: PASS / FAIL / NOT TESTED
- Audit PASS is claimed without raw target-build close-ups, or screenshots PASS without a clean audit rerun: PASS / FAIL / NOT TESTED

## Builder-owned verdict

- Deterministic environment-integrity audit: PASS / FAIL / NOT TESTED
- Transformed full-footprint occupancy: PASS / FAIL / NOT TESTED
- Semantic surface ownership: PASS / FAIL / NOT TESTED
- Visible render-ground coverage/seams: PASS / FAIL / NOT TESTED
- Vertical clearance: PASS / FAIL / NOT TESTED
- Detected-class before/fixed/rerun packet: PASS / FAIL / NOT TESTED
- Overall `high_angle_environment_integrity_evidence`: PASS / FAIL / NOT TESTED
- Blocking defects and disposition:
- Remaining evidence boundary:

A PASS requires zero audit errors plus the complete raw matrix. `164/164` prop collision, `180/180` boundary samples, collider alignment, navigation and scene validity are supporting context only and cannot rescue a visible-integrity FAIL.
