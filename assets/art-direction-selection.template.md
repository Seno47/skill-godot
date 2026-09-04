# Art Direction Selection Contract

Complete this builder-owned record before bulk asset, character, environment, or level production for a new complete game or production slice.

## Decision context

- Project / build:
- Decision revision and date:
- Decision owner/context:
- User-fixed references, requirements, and exclusions:
- Core player fantasy / verb:
- Primary camera and ordinary gameplay scale:
- Target platform, renderer, viewport, performance, memory, and package-size constraints:
- Planned content volume: characters, environments/biomes, props, UI/icons, animations, and VFX:
- Available authoring/generation/source tools and paid-cost boundary:

## Selection path

Choose one and explain the evidence:

- [ ] **User-fixed:** the user supplied a materially complete direction; alternatives would override authorship.
- [ ] **Constraint-determined:** project/platform/existing-art constraints leave one clearly viable route.
- [ ] **Materially ambiguous:** two or more serious directions must be compared; user choice is required when taste, identity, paid cost, or scope is the deciding factor.

Rationale:

## Layered visual contract

- Spatial/presentation architecture:
- Image/asset construction route:
- Shape, silhouette, and proportion language:
- Palette, value, saturation, and contrast hierarchy:
- Outline/edge, texture/texel, material, and surface-detail language:
- Lighting, shadow, atmosphere, and time logic:
- Motion, animation, camera, and VFX character:
- Typography, icon, menu, and gameplay-UI language:
- UI anchor record: core-play, secondary surface, component states and reference-to-runtime comparison from `ui-design-anchor.template.md`:
- Primary asset family and adaptation rules for secondary sources:
- Explicit visual and production exclusions:

## Candidate comparison

Use the same hero/action, camera, objective/environment role, and representative UI scale. Add or remove candidates only when the decision needs them. `Strong / workable / weak` judgments expose tradeoffs; they do not override hard rejects or user authorship.

| Criterion | Candidate A | Candidate B | Candidate C | Candidate D |
|---|---|---|---|---|
| Short direction and production route | | | | |
| User/reference fit | | | | |
| Gameplay-scale readability | | | | |
| Core-verb/identity relationship | | | | |
| Distinctiveness / stock-pack or generator-default risk | | | | |
| Coherent asset availability and rights | | | | |
| Consistency at declared content volume | | | | |
| Animation, rig/frame cleanup, VFX, and variant burden | | | | |
| Renderer/performance/memory/package-size fit | | | | |
| Localization, accessibility, icon, and UI fit | | | | |
| Import, editability, reimport, repair, and maintenance risk | | | | |
| Schedule, paid cost, and retry risk | | | | |
| Hard rejection or unresolved choice | | | | |

If alternatives are not applicable, record why rather than inventing weak candidates:

## Selected style family/profile

- Closest profile(s) from `references/visual-style-selection.md`:
- Project-specific rules and deviations:
- Why this direction wins without violating user intent or a hard constraint:
- Asset sourcing/generation/authoring route:
- Known production risks and bounded mitigation:
- Conditions that reopen selection:

## Pre-bulk gameplay-size evidence

The selected anchor is rendered in Godot at the target camera. Source previews or isolated turntables are supporting evidence only.

| State | Required content | Raw artifact | Builder observation | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|
| `style_anchor` | focal hero/actor/object at ordinary gameplay size | | | NOT TESTED |
| `representative_composition` | hero plus environment, interaction/objective/hazard, lighting/material response, and material UI/VFX layers | | | NOT TESTED |

Check explicitly:

- focal hierarchy, silhouette, contact, route/objective/hazard meaning;
- consistency of perspective, proportions, palette, edge/outline, texture density, material and lighting response;
- required animation/VFX/UI family feasibility rather than a beautiful isolated still;
- performance, memory/loading, and package-size plausibility for the declared content count;
- absence of raw blockout, default UI, pack collage, generated-family drift, or fashionable treatment used as a substitute for identity.

## Decision

- Selected direction:
- User decision required and resolved, if applicable:
- Rejected directions and concrete reason:
- Bulk production authorized from this anchor: NO
- Builder-owned `art_direction_selection_evidence`: NOT TESTED
- Remaining limitation:

Do not change `Bulk production authorized` to `YES` or pass the gate until the contract, rationale, raw style anchor, and representative composition are all present and no material choice remains unresolved.
