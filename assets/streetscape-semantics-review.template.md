# High-angle Road and Streetscape Semantics Review

Use with `references/road-and-streetscape-semantics.md`. This is a builder-owned blocking review layered after resolved provenance, environment integrity and whole-map coverage.

## Exact candidate

- Build ID / exact exported artifact:
- Godot version / renderer:
- Production scene and shipping camera:
- Resolved dependency-closure digest:
- Manifest path + SHA-256:
- Streetscape exporter path + SHA-256:
- Selected export preset + SHA-256:
- Contract JSON / audit JSON:
- Contract schema (must be v2) / migration source if applicable:
- Road profile: scale, traffic convention, stylization, hero radius:
- Raw capture root:
- Prior provenance/environment-integrity/environment-coverage results:

## Export coverage

| Resolved class | Expected | Exported | Unexplained omissions | PASS/FAIL/NOT TESTED |
|---|---:|---:|---|---|
| Semantic surface regions | | | | NOT TESTED |
| Lanes / junctions / approaches | | | | NOT TESTED |
| Sidewalk nodes / crossings | | | | NOT TESTED |
| Junction-side continuity runs / band samples | | | | NOT TESTED |
| Visible road details near crossings | | | | NOT TESTED |
| Full-footprint placed objects | | | | NOT TESTED |
| Visible buildings / material slots | | | | NOT TESTED |
| Street furniture with profiles | | | | NOT TESTED |
| Incident closures | | | | NOT TESTED |
| Boundary raster cells / causes | | | | NOT TESTED |
| Shipping-camera junction captures | | | | NOT TESTED |

## Road and junction topology

| Junction / approach | Inbound/outbound lanes | Legal movement | Divider continuity | Stop-line order/orientation | Crossing-to-sidewalk connection | Parking exclusion | Raw artifact | Verdict |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | NOT TESTED |

- Orphan lane/node/approach IDs:
- Lane samples outside travel/intersection surfaces:
- Disconnected or floating markings:
- Crosswalks ending outside clear pedestrian routes:
- Signals/signs without exact movement ownership:

## Sidewalk/curb junction continuity

| Junction / approach / side | Role: left/right return or T-opposite | Clear band width | Center + edge samples | Terrain/fallback/unowned samples | Bounded ramp/cutout contract | Raw artifact | Verdict |
|---|---|---:|---:|---:|---|---|---|
| | | | | | | | NOT TESTED |

- Every declared approach has both return roles or an exact sidewalk-absence record:
- Every T-junction opposite side remains continuous without a false road-mouth gap:
- Transition exceptions are bounded polygons with permitted surfaces, not prose-only waivers:
- Smallest detectable inner-corner hole / sample spacing:

## Crosswalk priority over road details

| Detail | Resolved full footprint | Crosswalk forbidden | Minimum / measured clearance | Crossing marking remains continuous | Raw close-up | Verdict |
|---|---|---|---|---|---|---|
| Storm drain / cover / repair bed / trench | | | | | | NOT TESTED |

- Expected / exported visible road-detail count:
- Road-detail profile cannot use closure exemption to cut a crossing:
- Integrated in-crossing detail, if any, is authored as part of the crossing surface:

## Full-footprint forbidden-surface audit

| Object | Class/profile | Full transformed footprint | Allowed ratio | Forbidden road/intersection/crosswalk/sidewalk ratio | Closure ID | Raw contact artifact | Verdict |
|---|---|---|---:|---:|---|---|---|
| | | | | | | | NOT TESTED |

- Building mass/support in road or sidewalk:
- Hydrant/pole/furniture in travel or pedestrian clear path:
- Vehicle/wreck/tanker/truck/sign obstruction without closure:
- Origin-only or broad-surface shortcuts rejected:

## Visible facade/roof/trim completeness

| Building | Zone/function/story profile | Visible area | Surface-slot roles | Default/unpainted area | Materialized area ratio | Upper/side/rear/roof raw state | Verdict |
|---|---|---:|---|---:|---:|---|---|
| | | | | | | | NOT TESTED |

- Every camera-visible surface slot exported:
- Effective material source recorded per slot:
- Required facade/roof/trim roles present:
- Node-wide override did not hide missing/default surfaces:
- Numeric completeness and rendered art-direction review both pass:

## Street furniture

| Object | Surface | Curb setback | Junction clearance | Approach | Forward/orientation error | Functional/story owner | Raw artifact | Verdict |
|---|---|---:|---:|---|---:|---|---|---|
| | | | | | | | | NOT TESTED |

- Hydrants remain in declared furnishing/frontage zones:
- Signals control the correct approach and face oncoming traffic/movement:
- Signs/poles are not camera-facing decoration detached from road semantics:
- Damaged/fallen exceptions are exact and visually legible:

## Incident closures

| Closure | Cause/cue objects | Closed graph connections | Alternate open path | Navigation/AI parity | Raw overview/close-up | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | NOT TESTED |

- Wreck/tanker/truck/barricade footprints without closure:
- `intentional`, genre/theme, or collision coverage used as a substitute:

## Visible boundary and safety-wall reachability

| Boundary cause | Visible cells | Safety cells | Maximum contact distance | Reachable safety-contact/pocket cells | Opening negative | Raw raster/target-build state | Verdict |
|---|---:|---:|---:|---:|---|---|---|
| | | | | | | | NOT TESTED |

- Production hero-radius shape and layers used:
- Every start partition flood-filled:
- Every safety cell owned exactly once:
- Cars/props can be walked around into a hidden-wall pocket:
- Visible barrier seals the route while declared openings remain open:

## Deterministic shipping-camera road/junction survey

| Capture | Build/camera match | Junctions | Approaches | Key surfaces/objects | Full-resolution artifact | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | NOT TESTED |

- Required junctions covered / total:
- Required approaches covered / total:
- Uncovered road cells or junction states:
- Curated beauty/free-camera frames rejected:

## Exact target-build candidate states

| State | Raw artifact | Build match | Observation | Verdict |
|---|---|---|---|---|
| `road_graph_and_markings` | | | | NOT TESTED |
| `junction_sidewalk_curb_continuity` | | | | NOT TESTED |
| `crosswalk_road_detail_priority` | | | | NOT TESTED |
| `building_road_setback` | | | | NOT TESTED |
| `facade_material_completeness` | | | | NOT TESTED |
| `street_furniture_placement` | | | | NOT TESTED |
| `incident_closure_or_clear_route` | | | | NOT TESTED |
| `visible_boundary_reachability` | | | | NOT TESTED |
| `road_junction_overview` | | | | NOT TESTED |

## Detected defect provenance

Every audit- or survey-detected class needs an exact sequence. If no class was found, state that explicitly; do not invent a before frame.

| Defect class | Before build/raw | Fixed build/raw | Candidate clean rerun/raw | Audit result | Verdict |
|---|---|---|---|---|---|
| | | | | | NOT TESTED |

## Negative regressions

- Older provenance/integrity/coverage gates PASS but road semantics fail: PASS / FAIL / NOT TESTED
- Cars are named as a boundary while a reachable pocket touches the safety wall: PASS / FAIL / NOT TESTED
- Building root is legal but full support/mass occupies road/sidewalk: PASS / FAIL / NOT TESTED
- Building material coverage is nominally complete but a visible slot is default/unpainted or a required role is absent: PASS / FAIL / NOT TESTED
- Lane dividers/stop/crosswalk/parking marks do not form a coherent junction approach: PASS / FAIL / NOT TESTED
- Road-mouth inner corner or T-opposite sidewalk exposes terrain/fallback because the slab/band stops short: PASS / FAIL / NOT TESTED
- Storm drain/repair/cover footprint fragments crosswalk markings: PASS / FAIL / NOT TESTED
- Hydrant/signal/sign/pole violates its surface, setback, approach or orientation profile: PASS / FAIL / NOT TESTED
- Incident prop blocks road/sidewalk without graph closure, cue ownership and alternate path: PASS / FAIL / NOT TESTED
- Selected screenshots leave junctions/approaches uncovered: PASS / FAIL / NOT TESTED

## Builder verdict

- Deterministic audit status / error count:
- Junction sidewalk/curb band continuity:
- Crosswalk/road-detail priority:
- Raw review status:
- Blocking defects:
- Final gate: PASS / FAIL / NOT TESTED
- Exact rerun command:
