# Visual Validation

Read this only when the task changes presentation, composition, UI, animation, effects, lighting, materials, or visual assets. A headless launch does not prove visual quality.

## Capture representative states

Use a real renderer and capture screenshots or short recordings at the intended viewport/aspect. Include the states relevant to the feature:

- spawn/idle and normal traversal;
- primary interaction/combat/action;
- failure/damage and success/transition when applicable;
- quiet and visually dense scenes;
- UI default, focus/hover, pressed, disabled, empty, loading, error, and overflow states that exist;
- pointer-open and keyboard/gamepad-open versions of dialogs whose initial focus differs by modality;
- localized icon-plus-label and icon-only buttons at representative short/long locales in narrow and wide layouts;
- scrollable UI at real overflow, including top/bottom positions and a visible scrollbar/grabber rather than an empty-state screenshot;
- target aspect/resolution extremes and busy gameplay behind UI;
- first-time effects/materials likely to expose stutter or shader issues.

Use consistent camera, resolution, renderer, quality preset, and scene state when comparing revisions.

For responsive UI or complete mobile/web builds, use a viewport matrix derived from the declared support range rather than only the reference aspect ratio. Include at least:

- the primary design/reference viewport;
- a near-square or short-height layout that stresses vertical composition;
- the narrowest supported portrait or equivalent extreme-narrow layout;
- a wide landscape layout when supported.

Choose actual platform minima when known. If a constrained browser/mobile brief has not supplied them, start from the canonical fallback matrix in `assets/capture-manifest.template.json`: extreme-narrow `336x629`, near-square `760x701`, short-height landscape `844x390`, and wide `1280x720`. Replace or add points when the declared orientation, embed size, safe area, or platform minimum differs; the fallback is not a claim of universal platform support. Capture the same important states at each matrix point so a good desktop shot cannot hide a broken compact layout.

## Inspect the rendered result

Compare against the user's brief and accepted references:

- composition, focal hierarchy, silhouette, spacing, scale, camera framing, and depth separation;
- palette/value structure, texture density, material response, lighting, shadows, and atmosphere;
- consistency across generated, sourced, and engine-native assets;
- UI hierarchy, theme, typography, contrast, focus, clipping, and localization/overflow;
- focus/hover/pressed outlines inside clipping containers, including whether expand-margin drawing is cropped or suggests a non-clickable hit area;
- scrollbar runtime width, contrast, gutter, grabber, and touch-drag result; theme properties without rendered overflow evidence are insufficient;
- intrinsic versus rendered aspect ratios for `TextureRect`, `Sprite2D`, icons, portraits, thumbnails, and other non-cover art, especially when a `Container` determines one axis;
- the center of the complete icon-plus-label visual group relative to its button/hit target, not just text alignment and the icon's individual rect; compare representative locales because text length can change the apparent drift;
- whether helper text, footers, legends, and secondary actions remain compositionally attached to the panel/flow they explain at every viewport;
- whether a tutorial card, pointer, or scrim intersects the highlighted target or required control in near-square and short-height layouts;
- animation timing, transitions, effects, feedback, and motion comfort;
- hover/focus motion geometry: compare the control's visual center and neighboring `Control` rects before/after; incidental layout shift is a defect even when each still looks individually plausible;
- seams, halos, missing textures, z-fighting, sorting, clipping, debug visuals, defaults, and placeholders.

Inspect motion in motion; a still cannot validate animation, camera comfort, effect overlap, or temporal feedback. Inspect assets inside the actual game, not only their source-tool preview.

## Iterate and report

Fix the most visible mismatch, recapture the same representative state, and compare again. Do not hide weak composition or incoherent assets with bloom, fog, vignette, grading, shake, or particles.

If no available tool can display the rendered game, complete structural/engine checks and state precisely that visual quality remains unverified. Do not call the result polished.

The building agent may capture and triage its own work, but it must not award near-perfect visual/UX scores from self-review alone. A complete game or vertical slice needs a screenshot/motion review by a person or genuinely independent evaluation context that did not author the layout. Provide the reviewer the brief and raw representative captures, not the builder's desired verdict. Record who/what reviewed it, which viewport/state matrix was covered, and the defects found or absence thereof.

At handoff, identify the states and resolutions inspected, the independent reviewer/context, and any visual state not reached.
