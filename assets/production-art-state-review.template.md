# Production Art State Review

Use this builder-owned gate for a complete game or production vertical slice. It exists to catch obvious art, contact, depth, VFX, and composition defects before an independent reviewer or user sees the build.

## Art contract

- Build/artifact:
- Builder/context:
- Primary rendering/spatial architecture:
- Character/environment/UI asset families:
- Shape, material, lighting, VFX, and motion direction:
- Deliberate primitive/minimalist exceptions and gameplay-size justification:
- Raw target-build capture folder:

Serialization in `.tscn` does not make a shape production art. `BoxMesh`, `SphereMesh`, `CylinderMesh`, CSG, flat quads, billboards, cones, shader rectangles, and primitive particles remain blockout/debug candidates unless the recorded art direction needs them and the final-size state matrix proves a coherent result.

## Required target-build state matrix

Capture the ordinary production camera and support-range viewport. Do not stage only an empty opening frame.

| State ID | Required content | Raw artifact | Builder observation | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|
| `quiet` | spawn/idle, environment and HUD at their least busy | | | NOT TESTED |
| `normal_gameplay` | representative traversal/core loop with ordinary effects | | | NOT TESTED |
| `dense_interaction` | maximum ordinary actor/prop/contact/depth complexity | | | NOT TESTED |
| `vfx_peak` | strongest required effect at contact, overlap, or action peak | | | NOT TESTED |
| `result` | success/failure/transition state with production feedback | | | NOT TESTED |

## Builder-owned inspection

Reject the baseline when any representative state shows:

- actors, victims, enemies, props, railings, weapons, hoses, pickups, or effects intersecting without an intentional readable contact;
- depth/sorting/pivots that make the action topology ambiguous;
- water, fire, smoke, sparks, trails, impacts, or shaders reading as debug rectangles, columns, cones, flat quads, or coarse billboard stains;
- primitive-rounded characters against a painterly/realistic background, or any other camera-visible asset-family mismatch;
- broken poses, detached action props, incoherent locomotion speed, or effects that do not originate/follow the action;
- sparse repeated modules without the structural detail, landmarks, variation, or rhythm promised by the direction;
- empty prompt/HUD panels, placeholder text, default controls, debug markers, or presentation that exists only to fill space;
- post-processing used to hide weak silhouettes, materials, VFX, or composition.

Link the separate `production-character-motion` recording when characters are expected to move. Still frames are necessary for overlap/contact diagnosis but cannot pass motion quality.

## Final verdict

- Quiet and normal art integration: NOT TESTED
- Dense contact/depth readability: NOT TESTED
- VFX shape, origin, timing, and material quality: NOT TESTED
- Asset-family coherence and authored detail: NOT TESTED
- Builder-owned production art integrity verdict: NOT TESTED
- Objective defects found and disposition:
- Remaining limitations:
