# Road and streetscape semantics for high-angle 3D

Use this guide with [high-angle-3d-districts.md](high-angle-3d-districts.md) and [3d-environment-integrity.md](3d-environment-integrity.md) when a fixed/high-angle district contains roads, intersections, sidewalks, crossings, parking, vehicles, hydrants, signals, signs, poles, or visible vehicle/structure boundaries. Instantiate `assets/streetscape-semantics-contract.template.json` and `assets/streetscape-semantics-review.template.md`, export the exact resolved production scene, then run:

```bash
python <skill-dir>/scripts/streetscape_semantics_audit.py \
  --model <project>/reports/streetscape-semantics-contract.json \
  --json-output <project>/reports/streetscape-semantics-audit.json \
  --summary
```

This is a separate builder-owned blocking gate. Passing dependency provenance, collision, environment integrity, whole-map surface coverage, navigation, or a curated screenshot does not prove that roads behave and read as roads. The streetscape report must use the same `build_id`, resolved dependency-closure manifest, selected export preset and exporter hashes as the other candidate reports. Add the streetscape exporter to the provenance manifest toolchain inputs and link this contract through `resolved_scene_provenance_audit.py --evidence-contract`.

Contract schema v6 is fail-closed. A v5 report is not sufficient evidence: re-export the exact resolved scene with source-owned facade/roof/openings/trim roles, MSAA-resolved mutually exclusive role masks and two opposed diagonal shipping-camera views per visible building, while preserving all schema-v5 road-end, marking, placement, source-role and vertex-contact evidence. Do not relabel an old report as v6 or carry forward adapter-declared roles, a single favorable gable, overlapping anti-aliased masks, normal-only facade masks, generic cap meshes, surrogate road-end planes or scalar mount gaps.

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
- every declared approach-side/T-side continuity band from a stable `junction_continuity_query`, plus an exact absence ledger;
- every visible drain, cover, trench and repair footprint from a stable `road_detail_query`, including non-colliding decals/beds;
- an exporter-owned traversal of every visible `MeshInstance3D`/`MultiMeshInstance3D`, with exact node path, mesh resource, real surface count, effective material and material source for every surface; the adapter classifies this manifest but cannot omit entries;
- full transformed support footprints for buildings, vehicles, wrecks, tanks/trucks, every street-furniture subclass, canopy/awning/support structures and visible boundary causes;
- every camera-visible building mesh surface bound to its real mesh instance and surface index, or to a resolved shader-mask subregion when one surface intentionally contains several roles;
- target-build gameplay-lighting frames plus one disjoint source-role/surface-ID mask for every facade, roof, opening/window and trim role actually present in the source mesh or atlas;
- every visible marking mesh as a resolved chain of mesh-surface vertex segments associated with exact lanes;
- every lane endpoint on a boundary node, its semantic termination, typed continuation/cap/closure footprint, exporter-resolved render-triangle topmost samples and marking endpoint/continuation measurement;
- every visible ground-, facade- or suspension-supported canopy/awning/support contact, including exact support vertices and mount-mesh triangle points for mounted/suspended structures;
- resolved anchor/forward vectors and approach association for street furniture;
- hero-radius occupancy cells, visible blocker cells and safety-only collision cells;
- exact shipping-camera junction coverage and raw candidate state paths.

Before trusting a copied or adapted exporter, run its engine-backed mesh-API fixture with the same Godot version used by the project:

```bash
godot --headless --path <project-dir> \
  --script res://tests/streetscape_semantics_exporter.gd -- \
  --self-test-primitive-mesh true
```

The bundled fixture creates real `PlaneMesh` and `BoxMesh` instances, traverses their visible triangles through the production collector, and requires both triangle sets. `PrimitiveMesh` geometry must be read with `PrimitiveMesh.get_mesh_arrays()`; reserve `surface_get_primitive_type()` and `surface_get_arrays()` for non-`PrimitiveMesh` meshes. Hash the exact exporter after this PASS. A source scan, a successful adapter import, or an `ArrayMesh`-only scene does not prove compatibility with built-in road, ground, cap, or block meshes. A crash before contract generation is a blocking exporter failure, not `NOT TESTED` evidence and not permission to reuse a stale report.

Use stable groups or typed resources such as `RoadSemanticProfile`, `RoadSegmentProfile`, `StreetFurnitureProfile`, `BuildingStyle`, and `IncidentClosure`. Scene metadata may supplement them, but strings scattered across scripts are not the source of truth. `ResourceLoader.get_dependencies()` can enumerate resource dependencies; the existing provenance exporter must recursively hash them and explicit runtime loads. A root scene hash alone remains invalid.

The exporter itself is evidence-shaping code. Hash it in `toolchain_inputs`. If an `@tool` road assembler or material resolver changes the emitted scene, hash that script too. A stale report generated from a different build fails even if every number looks plausible. Exporter failure is fail-closed: a nested traversal/classification/role collector that calls `_fail()` must halt the run before any output write or `[PASS]`. An error printed before a later success marker is still a failed evidence run.

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

### Resolve every boundary road endpoint

Every boundary-kind node incident to a lane needs exactly one `lane_boundary_termination` with `termination_kind`: `continued_offmap`, `turn`, `cul_de_sac`, or `physical_closure`. Bind it to all incident lanes, exact render-surface regions, one exporter-owned `resolved_typed_termination_geometry` footprint/profile, exact resolved mesh IDs, actual marking mesh chains and a raw shipping-camera close-up.

- `continued_offmap` proves an `offmap_corridor`: travel surface, sidewalk, curb and applicable marking meshes all continue beyond the boundary by the declared distance. Preserve exporter-owned top-surface samples for every required class. A road rectangle ending exactly at the node, a sidewalk/curb that stops early, or a building whose full transformed footprint enters the continuation corridor fails.
- `turn` names the resolved continuation lanes and must read as a turn in the close-up.
- `cul_de_sac` provides a typed bulb/hammerhead turnaround with authored road top surface rather than an exposed mesh edge.
- `physical_closure` names one explicit `road_end_policy`: `vehicle_cordon`, `facade_end`, `barrier_end`, `gate_end`, `debris_end`, or `terrain_end`. Its typed profile must match that policy and its exact cap meshes must belong to the visible cause objects. A common RoadNetwork mesh is not closure provenance. A full-width sidewalk/curb slab painted across a travel lane is not a road cap.

Road-end policy determines the geometry, not just the label:

- **Vehicle cordon:** the real road substrate remains topmost and continuous before, between and beyond the visible vehicles. Do not place a dark rectangle, asphalt bed, debug plane or generic closure patch under/around the vehicles. Markings may continue under the vehicle cause only when the policy explicitly says so; otherwise resolved marking segments stop before the cause.
- **Facade/terrain end:** the road substrate and markings stop before the actual facade/terrain mass. The at-cause topmost sample must resolve to that real mass, not to road or a covering patch. A building may terminate the street only when the lane does not enter its full footprint and the facade treatment explains the stop.
- **Barrier/gate/debris end:** preserve the authored road before and, when the road logically continues, beyond the visible cause. The cause itself provides the closure; a separate overlay/cap plane does not.

Every physical closure supplies query Y bounds, sample X/Z points for its required phases and an explicit marking policy. The exporter traverses the exact visible `MeshInstance3D`/`MultiMeshInstance3D` triangles, excludes separately-audited road-marking detail from the substrate query, overwrites adapter-supplied base/topmost/covering/coplanar mesh IDs and fails when a sample hits no visible render triangle. Multiple coplanar top meshes fail as ambiguous/z-fighting closure geometry. `termination_overlay_mesh_ids` must be empty. The auditor samples the actual mesh-derived marking segments against the closure footprint, so a marking hidden beneath a patch or cap fails even when its endpoint distance looks plausible.

No boundary endpoint or continued corridor may intersect a building footprint. Export each dashed/continuous marking mesh chain and its actual world-space segment endpoints. The auditor derives stop/continuation distance from those mesh vertices; an adapter-supplied `marking_stop_distance` is not evidence. Stop/divider/parking markings must end within the closure/turn budget or continue through an off-map corridor as appropriate, never run beneath a cap, into a facade, across closure art, or disappear at an arbitrary cut.

Every crosswalk connects two known sidewalk nodes, belongs to the relevant junction/approaches, and lies on crossing/intersection render surfaces. A stripe texture floating across an unrelated curb or ending in a prop cluster fails. Stop lines are approach-specific, approximately perpendicular to travel, upstream of the crossing/junction, and supported by the project's traffic convention. Signals/signs point at the movement they control. Parking bays/dividers must not continue through junction or crosswalk space.

Check lane-divider chains for endpoint continuity and surface ownership. Do not accept a high material-coverage percentage when road markings stop randomly, duplicate, cross each other at T-junctions, or describe impossible movements. Raw target-build junction frames must show the relationship at gameplay size.

### Close every sidewalk/curb junction band

A connected pedestrian graph can still hide a visible square hole beside the road mouth. For every declared approach, export separate left- and right-return center paths plus the clear band width. For every T-junction, also export the uninterrupted opposite-side sidewalk run; do not invent a full-width opening across the side that has no road. `streetscape_semantics_audit.py` samples the center and both band edges at the declared maximum spacing. Every sample must land on the authored top-surface family (`sidewalk_clear`, curb/return, crossing or a project equivalent), never bare terrain, fallback, substrate, carriageway or an unowned cell.

An approach side without pedestrian circulation needs an exact absence record, reason and raw state. A curb ramp, blended transition or deliberate cutout is not a blanket exception: declare its bounded polygon, permitted top-surface classes and raw close-up. The exception applies only inside that polygon. A prose note such as `sidewalk ends here` cannot legalize a 0.72 m corner void or a false 9.6 m T-side gap.

This game-scale contract follows the durable continuity relationship in the U.S. Access Board's [PROWAG scoping requirements](https://www.access-board.gov/prowag/scoping.html) and [technical requirements](https://www.access-board.gov/prowag/technical.html): pedestrian access routes, crossings and curb transitions form a connected route. It is not a claim that fictional dimensions meet a jurisdiction's accessibility law.

### Give crosswalk markings priority over road details

Export every visible storm drain, utility cover, repair bed, trench, inset grate and similar road-detail footprint—not only physics obstacles. Mark its placement profile `road_detail: true`, forbid crosswalk surfaces, set a project-scaled minimum crosswalk clearance and declare the exact expected count. The audit rejects an omitted detail manifest, a footprint that touches the protected crossing band, or a profile that allows a closure to cut the zebra. If the art direction genuinely needs an integrated cover inside a crossing, author one coherent crossing asset/material treatment and represent it as the crossing's own surface rather than layering a brown repair rectangle over the stripes.

The [FHWA MUTCD 11th Edition, Part 3](https://highways.dot.gov/media/111806) defines crosswalk markings as a deliberate marking system. In this workflow, that motivates a visual-priority contract: incidental road furniture must not fragment the crossing's readable pattern. It does not impose U.S. marking dimensions on the game.

## Full-footprint placement, not origin legality

Sample the transformed full footprint of every building, vehicle and furniture item against semantic render surfaces. Project profiles declare allowed classes, forbidden classes and maximum ratios. Default fail-closed relationships include:

- building support/mass: never in travel lane, intersection, crosswalk or sidewalk clear path;
- facade steps, awnings and supports: remain in frontage/apron or have an explicit designed projection that preserves clearance;
- hydrants, poles, lights, utility cabinets and ordinary signs: furnishing/median/frontage profile, never in travel lanes, intersections, crosswalks or the clear pedestrian route;
- parked vehicles: parking/travel profile but not junction/crosswalk/sidewalk;
- trees, stumps, rocks and bushes: grass/soil/landscape profile only; their complete footprints explicitly forbid travel lanes, intersections, crosswalks and the clear sidewalk band in addition to the environment-integrity surface profile;
- wrecks, tankers, trucks and barricades: may block a road only through an `IncidentClosure` that changes topology, provides an alternate route, owns the visual cues and passes the raw review.

An object's origin on concrete does not excuse a building volume over the carriageway, a hydrant in a lane, a lamp through a car, or a tanker swallowing the crossing. Broad `road_or_sidewalk` classes are too permissive: use the narrow semantic class actually intended.

### Make the visible-class inventory complete

Do not let a project adapter decide which visible objects are convenient to export. The provided exporter traverses every visible mesh before the adapter result is written. Classify every manifest entry exactly once as building, street furniture, support structure, road surface, boundary structure or an exact excluded/other class with a reason. Declare exact scope counts plus counts for each visible street-furniture and support subclass. Both directions are checked: every `street_furniture` placed object needs a resolved visible mesh, and every mesh classified as furniture needs a furniture placement profile.

Include ordinary street lights, work lights, utility poles, hydrants, signals, signs, cabinets and non-colliding visible pieces. A query/group that simply omits an inconvenient subclass fails even when all exported objects are legal.

## Facade/roof/trim completeness

Opaque material assignment on each building node is not facade completeness. Export every camera-visible `MeshInstance3D` surface slot, its effective material, semantic role and approximate visible area. Godot's `MeshInstance3D.get_active_material(surface)` resolves node-wide override, surface override or mesh material; record which source supplied it. A node-wide `material_override` can make every slot non-null while erasing facade/roof/trim structure, so it does not pass by itself.

Each building first declares an exporter-owned source-role inventory. Put every contributing production `MeshInstance3D` in `streetscape_building_source_roles`; author `streetscape_building_object_id` and `streetscape_source_roles` metadata with the exact surface indices and, for atlas roles, source texture, UV channel and authored UV-mask IDs. The bundled exporter replaces the adapter's top-level `resolved_building_source_role_manifest` from those scene-owned records. The adapter's per-building inventory must match it exactly. The inventory identifies the roles actually present in the imported mesh/atlas—facade, roof, openings/doors/windows and trim—and binds every role to either a dedicated mesh surface or a specific source texture, UV channel and authored UV mask. A present source role may not be made optional because one camera angle hides it. World-normal classification can separate facade from roof; it cannot prove windows, doors or trim that originate in an albedo atlas.

Each building style profile then declares:

- required visible roles such as facade, roof and trim/openings;
- forbidden/default/unpainted material IDs;
- permitted zone, function, construction and story states;
- minimum materialized visible-area ratio, normally 1.0 for final candidate surfaces;
- raw gameplay-lighting frames that expose upper floors, side/rear faces and roofs visible from the shipping camera.
- project-owned rendered value/chroma envelopes, minimum within-role value/chroma variation, maximum dominant-color ratio and positive perceptual-separation (`DeltaE`) budgets. Facade-to-openings and facade-to-trim pairs are mandatory when those roles exist;
- a whole-building mask value-variation and dominant-color budget that rejects flat flood fills even when separate solid colors technically satisfy role counts.

Each visible-slot record must name the exporter-owned mesh instance, real `surface_index`, effective material ID/source, authored role provenance and area derivation. Several semantic roles may share one mesh surface only through distinct resolved shader-mask subregions with mask-derived areas. IDs such as `material_id--facade/--roof/--trim` and 70/20/10 percentages created by the evidence adapter fail when they do not map to real surfaces or masks. A node-wide `material_override` is recorded as such and cannot silently masquerade as separate surface materials.

The sum of listed visible areas must account for the building's exported surfaces, but structural accounting is not the visual verdict. Render the exact target build under shipping `WorldEnvironment`, lights, fog and tone mapping. For every visible building, capture two distinct diagonal shipping-camera views whose normalized XZ directions satisfy the declared negative dot-product budget. Render one source-role ID pass for facade, roof, openings and trim, resolve MSAA, then threshold it once into mutually exclusive binary masks. Record the normalization method/threshold and cap cross-role overlap—normally at zero. Edge pixels must not be counted simultaneously as wall and window merely because anti-aliasing softened both masks.

Choose the paired view with the largest openings pixel count (or trim, then facade only when the source truly has no openings/trim) as the diagnostic view. That selected view still has to meet the role pixel minimum and facade-to-detail `DeltaE` budget; the opposite view remains evidence against angle-specific omissions. Save both raw frames and hashed masks and run the pixel audit inside `streetscape_semantics_audit.py`. It verifies hashes, source texture/UV or mesh-surface ownership, exact pair coverage, opposed directions, max-detail view selection, mutually exclusive normalized masks, visible-pixel minima, value/chroma envelopes, within-role variation, dominant-color ratios and required role-to-role `DeltaE`. Facade+roof normal masks or one favorable gable cannot certify a source atlas that contains windows/doors/trim. Missing upper floors, gray/default faces, monochrome/flood-filled openings, a flood-filled wall or collapsed role separation therefore fails even if every material resource is non-null.

## Street-furniture placement and orientation

Give each class a profile with permitted surfaces and project-scaled budgets:

- minimum/maximum curb setback;
- minimum junction clearance;
- required approach association and maximum distance to its lanes;
- orientation mode (`with_travel`, `face_oncoming`, or deliberately orientation-free) and tolerance;
- exact exceptions for damaged, fallen or story-specific pieces.

Measure from final transformed geometry. A traffic signal placed near a junction is not enough: it must belong to the correct approach and face the traffic/movement it addresses. A sign rotated toward the camera instead of the road fails. A hydrant in a travel lane fails even if vehicles are disabled in gameplay. Do not add random poles/signs for density; every item needs a functional or story owner.

## Ground and mount support for awnings/canopies

Classify every visible canopy, awning, shelter and structural support from the exporter-owned mesh inventory. Give each one an explicit support mode:

- `ground_supported`: resolved lowest visible vertices and multiple support samples must meet topmost render ground within the project gap budget;
- `facade_mounted`: exact mount mesh IDs and measured contact gap prove the attachment;
- `suspended`: exact suspension/mount mesh IDs and measured contact prove the authored suspension.

The measurement source must be resolved mesh vertices against render surfaces, not the object origin, a collision floor or a prose statement. For facade-mounted or suspended structures, name existing resolved mount meshes and preserve multiple support-vertex to mount-triangle point pairs; the auditor recomputes each 3D distance and the aggregate gap. An adapter constant such as `measured_mount_gap: 0` cannot pass without those points. Preserve a gameplay-lighting close-up. A post, awning or canopy floating above the sidewalk or facade fails even if it has no semantic placement error.

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

Use the production hero shape/radius when generating cells. In Godot, query `World3D.direct_space_state` with `PhysicsShapeQueryParameters3D` and `intersect_shape()` or an equivalent project-owned deterministic driver. Do not substitute a point ray for the character footprint, and do not let the adapter supply the cell classification. The separate visible-first schema-v2 exporter owns the complete production-capsule grid and requires a nonempty unsafe fringe.

Then run the separate whole-perimeter visible-first layer from [3d-environment-integrity.md](3d-environment-integrity.md). Flood-fill answers whether a pocket is reachable; it does not answer which collider is contacted first at every continuous boundary position. The visible-first contract must cover all declared spans, including non-road edges, and reject even one sample where the safety-only wall precedes the mapped visible cause. Raw close-ups, traces and the streetscape/environment reports must share one build and resolved dependency-closure digest.

## Shipping-camera road survey and defect provenance

Tile-survey the complete road/junction footprint with the shipping camera, final lighting, ordinary HUD and target build. Every junction and approach appears in at least one declared full-resolution capture. The candidate packet must include:

- road graph, lanes, dividers, stop lines, crossings and parking;
- every approach-side sidewalk/curb return and any T-side continuous run at gameplay size;
- crosswalks together with nearby drains, repairs, covers and other road details;
- building-to-road/sidewalk setbacks;
- upper/lower facade, roof and trim material completeness;
- exporter-owned marking mesh endpoints and typed road termination geometry;
- two opposed diagonal source-role views per building, the declared max-openings selection, MSAA-normalized exclusive masks and measured facade/roof/openings/trim value, chroma, variation, dominant-color ratio and separation;
- hydrants, signals, signs, poles and junction approaches;
- every declared lane-boundary termination and every resolved vertex-to-ground/mount canopy/awning/support contact;
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
- facade/roof/trim roles or percentage areas are synthesized without a real mesh surface index or shader-mask source;
- resource parameters look valid but target-build facade pixels miss the locked value/chroma envelope or required role separation;
- dividers, stop lines, crossing stripes or parking marks do not form a connected approach/junction topology;
- a declared road-mouth corner or T-side run exposes terrain/fallback because the sidewalk/curb band stops short;
- a storm drain, repair bed or utility detail cuts through crosswalk markings or was omitted from the resolved detail count;
- a hydrant, pole, signal or sign uses the wrong semantic surface, setback, approach or orientation;
- the exporter-owned visible mesh inventory has an unclassified/omitted lamp, work light, utility pole or support subclass;
- a boundary road endpoint has no resolved continuation/turn/cul-de-sac/physical closure, ends in a bare rectangular cut, runs markings into the edge, or lies inside a building footprint;
- a termination cites a common road mesh as cap provenance, overlays a full-width sidewalk slab on the lane, lets actual marking mesh vertices continue beneath its cap, omits off-map sidewalk/curb/markings, or lets a building footprint enter the continued corridor;
- a vehicle cordon uses a dark/surrogate bed or closure patch, the authored road does not continue between/beyond vehicles, or markings remain hidden under a stop-before-cause cap;
- a facade/terrain termination keeps the road or markings under/through the actual mass instead of stopping before it;
- a tree, stump, rock, bush, hydrant, lamp, pole or signal profile permits a travel lane, intersection, crosswalk or clear sidewalk footprint;
- an exporter collector fails but the run still writes a contract or prints `[PASS]`;
- the exact exporter has not passed its `PlaneMesh`/`BoxMesh` engine fixture, or it calls surface-only extraction APIs on `PrimitiveMesh` and crashes before auditing the resolved scene;
- source facade/roof/openings/trim roles are omitted, inferred only from world normals, lack texture/UV or mesh-surface provenance, collapse below their visible-pixel/DeltaE budgets, or trip the role/building flood-fill detector;
- only one favorable facade angle is captured, the selected paired view does not maximize openings visibility, or normalized role masks overlap after MSAA resolution;
- a visible awning/canopy/support lacks resolved ground/mount contact, names no real mount mesh/triangle, supplies only a scalar gap, or exceeds the support-gap budget;
- a wreck/tanker/truck/sign blocks a junction or sidewalk without a topology-changing authored closure and alternate route;
- the deterministic audit PASS is claimed without a complete shipping-camera road survey, or screenshots look plausible without a clean audit rerun.

The supplied `tests/fixtures/streetscape-semantics-old-clinic-negative.json` deliberately preserves PASS labels for the older provenance/environment gates while containing these failures. It must remain rejected by `streetscape_semantics_audit.py`.
