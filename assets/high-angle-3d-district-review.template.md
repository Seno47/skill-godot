# Fixed/High-angle 3D District Review

Use this builder-owned gate with rubric modifier `high-angle-3d-district-complete`. It supplements the production-art, applicable isometric/spatial, genre, performance and independent review packets. Complete it against the exact target build before asking the owner or independent reviewer to inspect the district.

## Candidate and declared budgets

- Build/revision/hash:
- Base + modifier rubric selector:
- Target platform, renderer, viewport range and performance budget:
- Camera projection, angle and permitted rotation:
- District plan / accepted art-direction anchor:
- Exact `WorldEnvironment`, key-light/fog/tone-map profile and shipping lighting phases:
- Raw capture and video root:
- Builder/context:

| Camera metric | Declared budget | Measured states/result | PASS/FAIL/NOT TESTED |
|---|---:|---|---|
| Follow half-life / 90% settle time | | | NOT TESTED |
| Look-ahead horizon and maximum lead | | | NOT TESTED |
| Inner safe-frame rectangle | | | NOT TESTED |
| Min/max orthographic size or FOV/distance | | | NOT TESTED |
| Maximum zoom rate and pressure hysteresis | | | NOT TESTED |
| Volume/rail blend and restoration time | | | NOT TESTED |
| Obstruction samples, layers and restoration | | | NOT TESTED |
| Shake/reduced-motion maximum | | | NOT TESTED |
| Frames outside safe frame by test state | | | NOT TESTED |

## Boundary ledger

Cover 100% of player-contactable boundary spans. A safety collider may sit behind a visible cause; it may not be the first explanation the player contacts.

| Boundary ID/span | Reachable approach | Visible urban/terrain cause | Collider alignment and opening negative test | Camera termination before void | Repetition risk | Raw artifact | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|
| | | | | | | | NOT TESTED |

- Contactable boundary coverage: / 100%
- Invisible/safety exceptions and reason:
- Open street/door/arch/gate negative cases:

## District hierarchy and functional zones

- Primary landmark/destination and required reacquisition points:
- Secondary anchors and the distinct decisions they support:
- Foreground/playable midground/skyline strategy:
- Block massing and height-band strategy:

| Zone | Gameplay function | Spatial/massing shape | Landmark/route relation | Cause -> response -> consequence evidence | Required negative space | Dressing cluster, not scatter | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|
| Entry/orientation | | | | | | | NOT TESTED |
| Resource/rescue branch | | | | | | | NOT TESTED |
| Risk/combat pocket | | | | | | | NOT TESTED |
| Connector/shortcut | | | | | | | NOT TESTED |
| Recovery/safe pocket | | | | | | | NOT TESTED |
| Objective/extraction | | | | | | | NOT TESTED |

Mark genuinely absent rows N/A with the signed brief rationale; do not relabel an empty area as a zone.

## View corridors and negative space

| Corridor/state | Player decision | Termination: landmark/turn/mass/elevation/continuation | Primary/secondary read | Dominant empty screen region and its function | Raw artifact | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|
| Start orientation | | | | | | NOT TESTED |
| Typical junction | | | | | | NOT TESTED |
| Landmark approach | | | | | | NOT TESTED |
| Extraction/objective approach | | | | | | NOT TESTED |

Fail a corridor that ends in map void, a repeated fence/building row, flat billboard, or atmosphere hiding unfinished space.

## Modular variation grammar and visible repetition

| Structural family/cluster | Massing variants | Facade variants | Roofline/silhouette variants | Surface variants | Identity/signage/decal variants | Story/damage cluster variants | Max identical visible run | Observed worst run | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---:|---:|---|
| | | | | | | | | | NOT TESTED |

- Families filling a full gameplay frame have at least three independent variation axes from different layers:
- Tint/rotation-only changes excluded from independent-axis count:
- Adjacent skyline/backdrop clones at similar size/rotation/roofline:
- Deterministic seed/resolved scene provenance when generated:
- Repetition overlay or annotated source scene/variant IDs:

Default warnings are `>=3` adjacent identical visible modules or `>=2` adjacent near-identical skyline masses. Any intentional exception needs raw-camera justification, believable endpoints/corners and functional rhythm.

## Architectural palette and material grammar

Do not pass this section from material coverage, distinct-hue counts, isolated swatches or editor previews. Use approximate visible screen area and raw target-build frames under the exact shipping lighting.

| Zone/profile | Function/story state | Construction/age drivers | Dominant family + visible-area band | Support family + band | Accent owner + maximum band | Rendered value/saturation/roughness envelope | Same-zone raw frame | Cross-zone raw frame | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | NOT TESTED |

| Building/style family | Facade material/slot | Roof material/slot | Trim/openings/signage | Preserved albedo/normal/ORM/detail | Weathering/damage masks and physical cause | Permitted story overrides | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|
| | | | | | | | NOT TESTED |

- Semantic assignment data (`zone`, `function`, `construction`, `age`, `story_state`, resolved profile/variant):
- Same-block/terrace/campus material continuity rule:
- Saturated-neighbor/checkerboard exclusion and observed worst run:
- Cross-zone transition cause (shared support family or explicit physical/story boundary):
- Dominant/support/accent approximate visible-area result under gameplay lighting:
- Texture/material-slot preservation check; whole-node flat overrides:
- Gameplay-camera detail proof for facade/roof/trim separation and localized grime/wear:
- Alternate shipping-lighting phases that materially change the palette:
- Exceptions and authored reason:

## Exact target-build visual state matrix

Use the ordinary HUD and final camera. A free-editor-camera image does not pass.

| State | Required read | Raw artifact | Builder observation | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|
| Entry/orientation | primary landmark and plausible district continuation | | | NOT TESTED |
| Typical street/block | massing, depth bands, facade rhythm, route | | | NOT TESTED |
| Boundary contact | visible cause before collision; no false opening | | | NOT TESTED |
| Open street/door/arch/gate negative | player/camera can use the authored opening without false collision/cutaway | | | NOT TESTED |
| View-corridor termination | landmark/turn/mass/elevation, not void/clones | | | NOT TESTED |
| Dense interaction/VFX | action/contact readable inside the composed district | | | NOT TESTED |
| Objective/extraction | destination hierarchy, approach and active state | | | NOT TESTED |
| Overview/max zoom | skyline repetition, boundary reveal and return framing | | | NOT TESTED |
| Repetition overlay | source scene/variant identity at gameplay camera | | | NOT TESTED |
| Same-zone palette/material cluster | coherent adjacency, dominant/support/accent hierarchy, no rainbow/checkerboard | | | NOT TESTED |
| Cross-zone palette transition | readable material/story change with a visible cause | | | NOT TESTED |
| Gameplay-size material detail | source texture/PBR response, facade/roof/trim split and localized weathering survive final lighting/filtering | | | NOT TESTED |

## Camera motion matrix

Preserve raw normal-speed video. Still images cannot pass this section.

| Transition | Follow/lead result | Safe-frame result | Zoom result | Volume/rail result | Obstruction/restoration result | Raw video/trace | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|
| Quiet -> accelerate | | | | | | | NOT TESTED |
| Stop -> reverse | | | | | | | NOT TESTED |
| Normal -> dense pressure -> quiet | | | | | | | NOT TESTED |
| Landmark/extraction volume enter -> exit | | | | | | | NOT TESTED |
| Volume edge/overlap | | | | | | | NOT TESTED |
| Single and multiple obstruction -> clear | | | | | | | NOT TESTED |
| Teleport/restart/reload | | | | | | | NOT TESTED |
| Reduced motion | | | | | | | NOT TESTED |

Reject raw-velocity wobble, overshoot, stop/reverse lag, zoom pumping, rail snap, volume-edge oscillation, route loss, open-hole false occlusion, x-ray shell fade, or incomplete restore.

## Negative-example rejection

- Perimeter fence as the dominant map boundary: PASS / FAIL / NOT TESTED
- Containers/cars/crates used as uniform density filler: PASS / FAIL / NOT TESTED
- Duplicated backdrop buildings at matching silhouette/scale/rotation: PASS / FAIL / NOT TESTED
- Prop scatter without zone function or story evidence: PASS / FAIL / NOT TESTED
- Dominant empty region without named gameplay/composition purpose: PASS / FAIL / NOT TESTED
- View corridor ending in void/billboard/fog/clones: PASS / FAIL / NOT TESTED
- Static beauty frame used instead of camera-motion proof: PASS / FAIL / NOT TESTED
- 100% material coverage or hue/variant count used as palette-quality proof: PASS / FAIL / NOT TESTED
- Opaque per-instance flood-fill/random hue cycling creates checkerboard/rainbow adjacency: PASS / FAIL / NOT TESTED
- Flat override erases texture/PBR response or facade/roof/trim structure: PASS / FAIL / NOT TESTED
- Accent colors have no semantic owner or dominate ordinary background mass: PASS / FAIL / NOT TESTED
- Same-zone/cross-zone review is missing under exact gameplay lighting: PASS / FAIL / NOT TESTED

## Builder-owned verdict

- Visible boundary and collision agreement: PASS / FAIL / NOT TESTED
- District hierarchy, depth and view corridors: PASS / FAIL / NOT TESTED
- Functional/story density and negative space: PASS / FAIL / NOT TESTED
- Modular variation and visible repetition: PASS / FAIL / NOT TESTED
- Architectural palette/material direction and lighting integration: PASS / FAIL / NOT TESTED
- High-angle camera comfort, framing and restoration: PASS / FAIL / NOT TESTED
- Overall `high_angle_3d_district_composition_evidence`: PASS / FAIL / NOT TESTED
- Blocking defects and disposition:
- Remaining evidence boundary:

A PASS says routine builder-owned district/camera acceptance is complete. It does not self-award the separate independent UX/art or human feel gates selected by the composite case.
