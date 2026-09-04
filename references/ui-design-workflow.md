# Design the Interface Around Play

Use for a new game UI, a substantial visual redesign, or a repeated template-looking result. For a focused control fix, preserve the existing system and verify only the affected states. Use `assets/ui-design-anchor.template.md` as one compact record alongside the art direction; it is not another final certification.

## Begin with the decision, not a panel collection

Write the primary player verb and the information needed immediately before and after it. Place the action/object first, then critical state, then the next decision. Move rare information to contextual or expanded views. Define a spatial grammar: what belongs to the world, what belongs next to an object, and what stays on the screen edge.

Examples are alternatives, not prescribed layouts:

- A clicker can center the worked object, show change on that object, collect gains near it, and keep the next useful improvement within reach. The world should visibly develop with progression.
- An idle workshop can show workstations and their states in the scene; selecting a station opens its relevant controls. Currency and rate remain concise. Do not surround every station with a permanent text card.
- A tactical game may legitimately need tables, repeated rows and labeled controls for comparison. Remove unnecessary ornament; retain the information that makes decisions possible.
- An action HUD can group frequently checked health/ammunition by gaze distance while long-term progression lives outside the combat screen.

A rectangle, flat icon, default-font family, centered title or clean minimal composition is not a defect by itself. The defect is interchangeable hierarchy, poor proportion, inaccessible meaning or a component pattern unrelated to play. Likewise, irregular frames, gradients, nine-patches and generated illustration do not automatically add craft.

## Select a visual target

Preserve a user-approved reference. If direction is open, inspect a small set of legally viewable references relevant to the actual platform, camera and interaction. Record which principle each supplies: hierarchy, typography, materials, motion or information placement. Do not copy protected assets or mix unrelated visual languages.

Choose one controlling direction. Compare two genuinely different compositions when layout/identity is still ambiguous; recoloring the same panel stack is not an alternative. The agent should choose reversible details and present only meaningful taste decisions. Do not require a user choice for every component.

Construct an original layered design anchor with realistic localized content:

1. Ordinary gameplay/core action, including meaningful progress and its next choice.
2. One consequential secondary surface, usually upgrades, result, inventory or settings.
3. A small component sheet: primary/secondary action, resource indicator, icon-plus-label, slider/toggle if present, and their pressed/focus/disabled states.

Use a source canvas, Godot scene or generated illustration with separate native text/control layers. A beautiful flattened screen is supporting concept art only. Use real numeric extremes and short/long locale content before investing in detailed art.

## Translate the anchor into a reusable family

Lock type roles, spacing rhythm, silhouettes, optical icon weight, surface/background contrast, layering and motion character. Each value needs a design purpose; a large token spreadsheet is unnecessary.

Choose the right production mechanism per component: native `Theme`/`StyleBoxFlat` for restrained geometric controls, `StyleBoxTexture`/nine-patch for material borders, authored vector/raster artwork for distinctive silhouettes. Use proper localized labels, accessible names and stable hit targets. Build one reusable `.tscn` per meaningful widget family, not a new scene for every label.

Implement the anchor before spreading the family. Compare source and Godot capture at the same state, viewport and locale using the region/overlay workflow in `ui-reference-integration.md`. Review hierarchy, visual weight, spacing and state clarity before pixel details. Test the minimum supported viewport as a composition, not a scaled desktop screenshot.

## Review in play, then expand

Use normal and crowded/repeated states, not only an empty menu. Ask without coaching: what is interactive, what changes on action, where is the next decision, and what can safely be ignored? A reviewer may understand a screen after study yet fail its first glance.

Compare against the anchor and a small calibrated example set. Record concrete mismatches and fixes. A coherent conventional UI is a positive control; a custom ornamental dashboard with obscure controls is a negative control. These protect against both generic output and unnecessary decoration.

`assets/ui-calibration/` includes original schematic positive/negative controls and a reviewer task for first-read hierarchy/action comprehension. They are not production artwork or proof that an evaluator can judge every art style. Present them under neutral IDs; preserve mistakes before revealing the explanatory key.

One shared raw packet can support art selection, menu, HUD and cross-surface reviews. Preserve separate verdicts but do not ask several reviewers to fill duplicate forms. Reopen the anchor only when a real failure invalidates it; do not restart art direction for minor spacing fixes.

The existing `art_direction_selection_evidence` gate includes this early UI anchor for games with material UI. Its scope is pre-production feasibility and coherence. Later target-build craft/UX reviews still judge the delivered game.
