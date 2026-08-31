# Road and streetscape semantics for high-angle 3D

Use this guide with [high-angle-3d-districts.md](high-angle-3d-districts.md) and [3d-environment-integrity.md](3d-environment-integrity.md) when a fixed/high-angle district contains roads, intersections, sidewalks, crossings, parking, vehicles, hydrants, signals, signs, poles, or visible vehicle/structure boundaries. Instantiate `assets/streetscape-semantics-contract.template.json` and `assets/streetscape-semantics-review.template.md`, export the exact resolved production scene, then run:

```bash
python <skill-dir>/scripts/streetscape_semantics_audit.py \
  --model <project>/reports/streetscape-semantics-contract.json \
  --json-output <project>/reports/streetscape-semantics-audit.json \
  --summary
```

This is a separate builder-owned blocking gate. Passing dependency provenance, collision, environment integrity, whole-map surface coverage, navigation, or a curated screenshot does not prove that roads behave and read as roads. The streetscape report must use the same `build_id`, resolved dependency-closure manifest, selected export preset and exporter hashes as the other candidate reports. Add the streetscape exporter to the provenance manifest toolchain inputs and link this contract through `resolved_scene_provenance_audit.py --evidence-contract`.

## Calibrate a project road profile, not a legal claim

Real street guidance supplies useful relationships, but one country's dimension table is not a universal game scale. Declare the game's unit scale, hero radius, camera, degree of stylization, traffic convention, road hierarchy, sidewalk/furnishing/frontage classes, curb/junction budgets and any deliberately ruined or improvised condition. Then keep those relationships internally coherent.

The semantic model follows durable principles from authoritative guidance:

- the pedestrian route remains continuous through a crossing;
- furniture and utilities do not consume the clear pedestrian route;
- a hydrant, pole, signal or sign belongs to an authored curb/furnishing/median location rather than an arbitrary travel lane;
- a crosswalk connects intended sidewalk endpoints;
- lane, stop-line, crossing and signal geometry is associated with a particular junction approach and movement.

These rules are informed by the [U.S. Access Board Public Right-of-Way Accessibility Guidelines](https://www.access-board.gov/prowag/), the [FHWA MUTCD 11th Edition](https://mutcd.fhwa.dot.gov/pdfs/11th_Edition/mutcd11thedition.pdf), and [NACTO crosswalk guidance](https://nacto.org/publication/urban-street-design-guide/intersection-design-elements/crosswalks-and-crossings/). They are production-design evidence, not certification that a fictional or real-world road is legally compliant.

## Export the final semantic scene

Do not hand-type a simplified JSON that disagrees with the map. Copy/adapt `assets/godot-tests/streetscape_semantics_exporter.gd`; it instantiates the exact production `PackedScene`, then injects a project-owned adapter script as a transient QA node. The adapter must never be serialized in or referenced by the production scene. Record it as a provenance `toolchain_input`, not a production dependency. A Godot-owned exporter must wait for scene/physics setup, resolve final `global_transform` values, and emit:

- every semantic render surface polygon: travel lane, parking lane/bay, intersection, crosswalk, sidewalk clear path, curb, furnishing/buffer zone, frontage, median/island, closure treatment and project-specific variants;
- lane, junction, legal-movement, approach, sidewalk and crossing graphs;
- full transformed support footprints for buildings, vehicles, wrecks, tanks/trucks, furniture and visible boundary causes;
- every camera-visible building mesh surface, effective material and approximate visible area;
- resolved anchor/forward vectors and approach association for street furniture;
- hero-radius occupancy cells, visible blocker cells and safety-only collision cells;
- exact shipping-camera junction coverage and raw candidate state paths.

Use stable groups or typed resources such as `RoadSemanticProfile`, `RoadSegmentProfile`, `StreetFurnitureProfile`, `BuildingStyle`, and `IncidentClosure`. Scene metadata may supplement them, but strings scattered across scripts are not the source of truth. `ResourceLoader.get_dependencies()` can enumerate resource dependencies; the existing provenance exporter must recursively hash them and explicit runtime loads. A root scene hash alone remains invalid.

The exporter itself is evidence-shaping code. Hash it in `toolchain_inputs`. If an `@tool` road assembler or material resolver changes the emitted scene, hash that script too. A stale report generated from a different build fails even if every number looks plausible.

## Road, junction, pedestrian, and marking topology

Represent roads as a graph plus render-space surfaces, not as decorative stripes:

```text
RoadNetwork3D
├── SurfaceRegions
├── LaneGraph
│   ├── LaneSegment_*
│   ├── Junction_*
│   └── Approach_*
├── PedestrianGraph
│   ├── SidewalkSegment_*
│   └── Crosswalk_*
├── Markings
├── StreetFurniture
└── IncidentClosures
```

Every lane endpoint must resolve to a declared node and remain on a permitted travel/intersection surface. Every junction lists its inbound/outbound lanes and legal movements. Every approach references actual inbound lanes and a direction into one junction. Closed lanes remain in the graph with explicit status and closure ownership; do not delete their semantics while leaving their visuals.

Every crosswalk connects two known sidewalk nodes, belongs to the relevant junction/approaches, and lies on crossing/intersection render surfaces. A stripe texture floating across an unrelated curb or ending in a prop cluster fails. Stop lines are approach-specific, approximately perpendicular to travel, upstream of the crossing/junction, and supported by the project's traffic convention. Signals/signs point at the movement they control. Parking bays/dividers must not continue through junction or crosswalk space.

Check lane-divider chains for endpoint continuity and surface ownership. Do not accept a high material-coverage percentage when road markings stop randomly, duplicate, cross each other at T-junctions, or describe impossible movements. Raw target-build junction frames must show the relationship at gameplay size.

## Full-footprint placement, not origin legality

Sample the transformed full footprint of every building, vehicle and furniture item against semantic render surfaces. Project profiles declare allowed classes, forbidden classes and maximum ratios. Default fail-closed relationships include:

- building support/mass: never in travel lane, intersection, crosswalk or sidewalk clear path;
- facade steps, awnings and supports: remain in frontage/apron or have an explicit designed projection that preserves clearance;
- hydrants, poles, lights, utility cabinets and ordinary signs: furnishing/median/frontage profile, never in the travel lane or clear pedestrian route;
- parked vehicles: parking/travel profile but not junction/crosswalk/sidewalk;
- trees/rocks/bushes: their environment-integrity surface profile still applies in addition to streetscape rules;
- wrecks, tankers, trucks and barricades: may block a road only through an `IncidentClosure` that changes topology, provides an alternate route, owns the visual cues and passes the raw review.

An object's origin on concrete does not excuse a building volume over the carriageway, a hydrant in a lane, a lamp through a car, or a tanker swallowing the crossing. Broad `road_or_sidewalk` classes are too permissive: use the narrow semantic class actually intended.

## Facade/roof/trim completeness

Opaque material assignment on each building node is not facade completeness. Export every camera-visible `MeshInstance3D` surface slot, its effective material, semantic role and approximate visible area. Godot's `MeshInstance3D.get_active_material(surface)` resolves node-wide override, surface override or mesh material; record which source supplied it. A node-wide `material_override` can make every slot non-null while erasing facade/roof/trim structure, so it does not pass by itself.

Each building style profile declares:

- required visible roles such as facade, roof and trim/openings;
- forbidden/default/unpainted material IDs;
- permitted zone, function, construction and story states;
- minimum materialized visible-area ratio, normally 1.0 for final candidate surfaces;
- raw gameplay-lighting frames that expose upper floors, side/rear faces and roofs visible from the shipping camera.

The sum of listed visible surface areas must account for the building's exported visible area. Missing upper floors, one default-white facade, an unpainted rear wall, or a roof that inherited a placeholder material fails even if 74/74 building roots have overrides. This numeric contract establishes completeness; the district palette/material review still judges coherence, texture preservation and atmosphere.

## Street-furniture placement and orientation

Give each class a profile with permitted surfaces and project-scaled budgets:

- minimum/maximum curb setback;
- minimum junction clearance;
- required approach association and maximum distance to its lanes;
- orientation mode (`with_travel`, `face_oncoming`, or deliberately orientation-free) and tolerance;
- exact exceptions for damaged, fallen or story-specific pieces.

Measure from final transformed geometry. A traffic signal placed near a junction is not enough: it must belong to the correct approach and face the traffic/movement it addresses. A sign rotated toward the camera instead of the road fails. A hydrant in a travel lane fails even if vehicles are disabled in gameplay. Do not add random poles/signs for density; every item needs a functional or story owner.

## Authored incident closures

When a wreck, tanker, truck, barricade, collapsed sign or emergency structure occupies a lane, junction or sidewalk, require one closure record containing:

- physical/story cause and raw close-up;
- exact blocked lane/sidewalk connections;
- those connections marked closed in the graph;
- at least one contiguous open alternate route or an explicit terminal/no-route objective state;
- visual cue object IDs and route warning/wayfinding;
- navigation, AI and camera behavior consistent with the same closure.

`intentional_overlap`, `post-apocalypse`, or `the player can go around somehow` is not a closure contract. A dramatic wreck without updated topology is still an accidental obstruction.

## Visible-boundary contact and reachable pockets

The environment coverage gate proves that colliders have visible mass. It does not prove that the mass actually prevents the player from reaching the invisible safety wall behind it. Export a hero-radius raster from the exact production scene:

- walkable/open cells;
- nonwalkable surface cells;
- visible blocker cells;
- safety-only blocker cells;
- starting cells for every reachable partition;
- each visible boundary cause and the safety cells it is meant to precede.

Flood-fill from player starts. A reachable cell adjacent to a safety-only wall is a FAIL by default: it is a playable pocket/contact against an invisible boundary. Every safety cell must be owned by exactly one visible cause and lie within the declared contact distance behind it. Two cars described as a boundary fail when the hero can walk around/between them and reach the wall. A visible building, continuous wall, cliff or dense authored closure may pass when its transformed footprint actually seals the route and the opening negative case remains open.

Use the production hero shape/radius when generating cells. In Godot, query `World3D.direct_space_state` with `PhysicsShapeQueryParameters3D` and `intersect_shape()` or an equivalent project-owned deterministic driver. Do not substitute a point ray for the character footprint.

Then run the separate whole-perimeter visible-first layer from [3d-environment-integrity.md](3d-environment-integrity.md). Flood-fill answers whether a pocket is reachable; it does not answer which collider is contacted first at every continuous boundary position. The visible-first contract must cover all declared spans, including non-road edges, and reject even one sample where the safety-only wall precedes the mapped visible cause. Raw close-ups, traces and the streetscape/environment reports must share one build and resolved dependency-closure digest.

## Shipping-camera road survey and defect provenance

Tile-survey the complete road/junction footprint with the shipping camera, final lighting, ordinary HUD and target build. Every junction and approach appears in at least one declared full-resolution capture. The candidate packet must include:

- road graph, lanes, dividers, stop lines, crossings and parking;
- building-to-road/sidewalk setbacks;
- upper/lower facade, roof and trim material completeness;
- hydrants, signals, signs, poles and junction approaches;
- incident closure or intentionally clear-route states;
- visible-boundary cause plus raster overlay;
- representative junction overview and the densest obstruction state.

For every defect class discovered by audit or visual survey, preserve exact `before`, `fixed`, and clean `rerun` raw states with build IDs. A clean project with no discovered class records that fact and still supplies the candidate state matrix. Curated beauty frames cannot cover an unobserved junction.

## Fail-closed examples

Reject the candidate when any of these are true:

- provenance, environment integrity and coverage PASS, but cars leave a reachable pocket against a safety wall;
- flood-fill reports zero reachable pockets, but one whole-perimeter ray/capsule sample contacts a safety-only wall before visible geometry;
- a building origin is in its parcel while its transformed support footprint occupies road/sidewalk;
- every building node has a material but a visible floor/facade/roof/trim slot is default or unpainted;
- dividers, stop lines, crossing stripes or parking marks do not form a connected approach/junction topology;
- a hydrant, pole, signal or sign uses the wrong semantic surface, setback, approach or orientation;
- a wreck/tanker/truck/sign blocks a junction or sidewalk without a topology-changing authored closure and alternate route;
- the deterministic audit PASS is claimed without a complete shipping-camera road survey, or screenshots look plausible without a clean audit rerun.

The supplied `tests/fixtures/streetscape-semantics-old-clinic-negative.json` deliberately preserves PASS labels for the older provenance/environment gates while containing these failures. It must remain rejected by `streetscape_semantics_audit.py`.
