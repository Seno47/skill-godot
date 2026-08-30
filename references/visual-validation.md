# Visual Validation

Read this only when the task changes presentation, composition, UI, animation, effects, lighting, materials, or visual assets. A headless launch does not prove visual quality.

## Capture representative states

Use a real renderer and capture screenshots or short recordings at the intended viewport/aspect. Include the states relevant to the feature:

- spawn/idle and normal traversal;
- for a new complete game or production slice, the selected pre-bulk `style_anchor` and `representative_composition` from the real Godot camera, linked to the art-direction selection record; user-fixed directions still need the anchor even when alternatives are not applicable;
- complete-game app/export icon at actual smallest/representative platform sizes plus the main-menu mark at runtime size, supplied raw for blind semantic review;
- complete-game main menu default plus a supported interaction state, supplied raw for independent wordmark/copy/composition review;
- complete-game settings with real slider/switch/check/option/focus states and the text-heaviest result/map/upgrade/progression surface; functional native/default widget art is not a finished visual state;
- primary interaction/combat/action;
- material aim/trajectory/route/placement/intent telegraphs at ordinary, multi-contact or changed-direction, invalid/blocked, and dense states;
- failure/damage and success/transition when applicable;
- quiet and visually dense scenes;
- for every complete game or production slice, the same release-like build's quiet, normal gameplay, densest ordinary interaction/contact, peak VFX, and success/failure/result states; do not approve production art from an empty opening frame;
- UI default, focus/hover, pressed, disabled, empty, loading, error, and overflow states that exist;
- complete-game gameplay HUD as annotated `hud_quiet`, `hud_normal`, `hud_dense`, and `hud_vfx_peak` raw frames, with persistent/contextual text inventory and representative locale stress;
- pointer-open and keyboard/gamepad-open versions of dialogs whose initial focus differs by modality;
- localized icon-plus-label and icon-only buttons at representative short/long locales in narrow and wide layouts;
- scrollable UI at real overflow, including top/bottom positions and a visible scrollbar/grabber rather than an empty-state screenshot;
- target aspect/resolution extremes and busy gameplay behind UI;
- the real start camera and representative route/corner/elevation views for long emissive meshes, ceiling strips, beams, rails, cables, and other perspective-sensitive geometry;
- matched third-person blocked/clear captures at multiple route locations, including one multi-occluder stack, one open doorway/gate center, one cutaway-strength comparison, one silhouette fallback, the fully restored state, and the exact reported/highest-structure elevation view rather than only an easier generic room;
- for fixed-camera isometric/orthographic work, the early art slice and matched gameplay-size quiet, dense, height-transition, and route-changing captures; pair each character-readability frame with a hero-only mask from the exact same camera/frame;
- for fixed/high-angle 3D districts, raw target-build entry/landmark, typical block, reachable boundary contact, long-corridor termination, dense interaction, objective/extraction, overview/max-zoom and visible-repetition-overlay frames plus normal-speed follow/look-ahead/zoom/camera-volume/obstruction/restoration video;
- for every production character expected to move, a short raw target-build recording at the gameplay camera covering idle, locomotion, and brief-required context actions; include a gameplay-size pose/contact sheet and attachment-follow state when useful, but do not treat stills as motion proof;
- first-time effects/materials likely to expose stutter or shader issues.

Use consistent camera, resolution, renderer, quality preset, and scene state when comparing revisions.

For a deterministic delivery/proof recording, initialize the camera and scripted state before the first captured frame, drive progression through a project-owned test/presentation path, and keep visible behavior advancing across the whole 15–20 second clip. Watch it back from start to finish. Reject dead opening time, stale/repeated single-frame motion, hidden inputs, a camera that settles only after the clip begins, or a montage that omits the core cause-and-effect. A proof clip summarizes a verified build; it does not replace the raw state captures or acceptance owners below.

Prefer the intended hardware renderer for final motion evidence. If the environment falls back to a software Vulkan/rendering device, record it explicitly: still captures may remain useful for limited diagnosis, but do not silently treat degraded, incorrect, or impractically slow motion as target-hardware proof.

When an approved UI screenshot/mockup is the target, follow [ui-reference-integration.md](ui-reference-integration.md): capture the same state and dimensions, create side-by-side/overlay/diff artifacts with `scripts/image_compare.py`, and review named regions. Do not convert a global pixel metric into a parity verdict without inspecting the raw captures and recorded deviations.

For responsive UI or complete mobile/web builds, use a viewport matrix derived from the declared support range rather than only the reference aspect ratio. Include at least:

- the primary design/reference viewport;
- a near-square or short-height layout that stresses vertical composition;
- the narrowest supported portrait or equivalent extreme-narrow layout;
- a wide landscape layout when supported.

Choose actual platform minima when known. If a constrained browser/mobile brief has not supplied them, start from the canonical fallback matrix in `assets/capture-manifest.template.json`: extreme-narrow `336x629`, near-square `760x701`, short-height landscape `844x390`, and wide `1280x720`. Replace or add points when the declared orientation, embed size, safe area, or platform minimum differs; the fallback is not a claim of universal platform support. Capture the same important states at each matrix point so a good desktop shot cannot hide a broken compact layout.

## Inspect the rendered result

Compare against the user's brief and accepted references:

- composition, focal hierarchy, silhouette, spacing, scale, camera framing, and depth separation;
- whether the chosen layered direction preserves explicit user references/exclusions and remains viable for the declared content, animation/VFX, target performance/size, UI/localization/accessibility, rights, cost, and maintenance constraints; an available pack, fashionable label, or generator default is not a rationale;
- whether the app icon/main-menu mark communicates a game-specific subject or core-loop relationship before the intended meaning is explained; palette consistency and tidy primitive geometry alone are insufficient;
- whether the main menu title is an authored wordmark/typographic composition at runtime size, every non-navigation phrase has a real purpose, and the whole screen avoids the generic badge/kicker + huge default-font title + accent rule + premise tagline + identical rectangle-stack fingerprint;
- whether menu, settings, result, map/selector, upgrade/shop, and progression surfaces use one authored interface family and communicate through hierarchy, icons, meters, state art, spatial grouping and visible change rather than native/default sliders/checkbuttons or repeated labeled rectangles;
- whether the same exact candidate's main menu, pause/runtime modal, settings, ordinary play/HUD, result/failure, and text-heaviest secondary surface survive one cross-surface review; `authored`, `custom`, equal rectangles, and shared colors cannot substitute for hierarchy, optical family consistency, and craft;
- palette/value structure, texture density, material response, lighting, shadows, and atmosphere;
- consistency across generated, sourced, and engine-native assets;
- UI hierarchy, theme, typography, contrast, focus, clipping, and localization/overflow;
- focus/hover/pressed outlines inside clipping containers, including whether expand-margin drawing is cropped or suggests a non-clickable hit area;
- scrollbar runtime width, contrast, gutter, grabber, and touch-drag result; theme properties without rendered overflow evidence are insufficient;
- intrinsic versus rendered aspect ratios for `TextureRect`, `Sprite2D`, icons, portraits, thumbnails, and other non-cover art, especially when a `Container` determines one axis;
- source/viewBox versus final visible-alpha bounds, alpha/visual centroid, internal padding, baseline, small-size filtering/halo, and relative visible weight across critical icon families; mathematical node centers do not prove optical alignment;
- the center of the complete icon-plus-label visual group relative to its button/hit target, not just text alignment and the icon's individual rect; compare representative locales because text length can change the apparent drift;
- whether helper text, footers, legends, and secondary actions remain compositionally attached to the panel/flow they explain at every viewport;
- whether a tutorial card, pointer, or scrim intersects the highlighted target or required control in near-square and short-height layouts;
- persistent 3D HUD screen-space occupancy against the project's recorded top/bottom/side and central-sightline budget; inspect opaque/translucent backplates over real play rather than only each `Control` rect;
- gameplay HUD simultaneous reading load: count independent headings/captions/values/prompts/objective zones, annotate their screen area and gaze transfers from the action focus, remove text duplicated by icon/meter/position, and verify critical state plus immediate objective in a brief uncoached glance during normal/dense action;
- icon-first telemetry quality: one authored icon family at final size, non-color differentiation, accessible names/tooltips/first-use labels for ambiguous symbols, and progressive disclosure after learning; reject emoji, arbitrary Unicode, default editor icons, unexplained symbols, and unrelated packs as production shortcuts;
- perspective projection of long, thin, emissive world geometry from the actual gameplay camera: reject bright bands that cross the route, hide targets, collapse depth, or dominate exposure/bloom even when the mesh placement looks harmless in the editor's free camera;
- player visibility from the resulting camera, not merely camera collision: compare several character heights/regions, verify every simultaneous occluder is resolved, keep the route/environment readable, and confirm that open holes remain clear without false cutaway;
- high-structure cutaway quality at the exact failure/elevation framing: compare route/target contrast and retained spatial cues, not only transparency values, faded-object counts, or silhouette presence. Reject a white veil/grid or route-filling shell even when technically transparent;
- blocked-to-clear restoration of all affected render state. Look for lingering transparency, hidden meshes, missing shadows, shader parameters, render-layer changes, or a silhouette that stays enabled after the obstruction is gone;
- fixed-camera isometric character separation at actual gameplay size: review the silhouette and local edge against the quiet floor, dominant/lightest background values, dense decor, mechanism state, elevation transition, and route-changing stress state. Use `scripts/isometric_readability_audit.py` with predeclared project thresholds, but reject a semantically generic or route-obscuring result even when the measurements pass;
- fixed-camera density and composition: compare start/teaching, typical puzzle, densest decor/mechanism, highest elevation, and objective/result frames for focal hierarchy, foreground/midground/background structure, landmarks, purposeful negative space, route rhythm, controlled repetition, and HUD/world competition. Asset count and import success do not excuse sparse rows or a default-looking hero;
- fixed/high-angle 3D district composition: verify that every reachable boundary reads as urban/terrain structure before collision, major view corridors terminate in a landmark/turn/mass/elevation rather than void/fog/clones, large empty regions have named gameplay/composition functions, zone dressing forms cause-response-consequence clusters rather than uniform scatter, and repeated screen-filling families vary across massing/facade/roofline/surface/identity/story layers. A fence rectangle, rotated containers, duplicated skyline row, prop count or occlusion-culling statistic is a FAIL, not density evidence;
- high-angle camera motion: inspect accelerate/stop/reverse, quiet-dense-quiet pressure, volume/rail enter/edge/overlap/exit, obstruction/clear and teleport/reload at normal speed against declared safe-frame, settle, lead, zoom-rate/hysteresis and restore budgets. A polished still cannot pass lag, overshoot, raw-velocity wobble, zoom pumping, rail snap, open-hole false occlusion or incomplete restoration;
- production character motion at normal speed: reject bind/rest/T-pose leakage, a frozen first frame, missing idle/locomotion/context playback, visible source mannequins, retarget deformation, loop pops, foot sliding/contact mismatch, gameplay states that never dispatch, stale poses after interruption, and props/effects that do not follow their animated attachment;
- production-art integrity in dense action: reject unintentional actor/prop/effect intersections, unreadable contact/depth, asset-family mismatch, sparse repeated blockout modules, empty placeholder panels, rectangular/columnar debug-looking water, flat quad/cone flames, coarse billboard smoke, or other engine/procedural shapes that lack a deliberate final-size visual language;
- cross-family integration in the same frame: compare world actors/objects, UI/icons, telegraphs/tutorial cues/threats, and VFX for perspective, edge treatment, texture density, scale, material/motion language, and contact/anchor/depth. Palette agreement cannot pass painterly world art crossed by foreign flat strips, thin wireframes, detached arrows/rings, unanchored smudges, or unrelated sharp VFX symbols;
- gameplay telegraph craft: aim, launch, ricochet, path, placement, area, and enemy-intent cues must visually encode owner/origin, direction, contacts/turns, endpoint, validity and consequence in the selected art/material/motion family. Exact math, `Line2D`, a mesh strip, polygon, dots, or arrows remain debug candidates until the raw target-build states prove both meaning and art-family fit;
- animation timing, transitions, effects, feedback, and motion comfort;
- hover/focus motion geometry: compare the control's visual center and neighboring `Control` rects before/after; incidental layout shift is a defect even when each still looks individually plausible;
- seams, halos, missing textures, z-fighting, sorting, clipping, debug visuals, defaults, and placeholders.

Inspect motion in motion; a still cannot validate animation, camera-relative control, both orbit axes, zoom/recenter, camera collision recovery, multi-occluder transitions, cutaway restoration, silhouette fallback behavior, mouse-capture recovery, effect overlap, or temporal feedback. Inspect assets inside the actual game, not only their source-tool preview.

## Iterate and report

Fix the most visible mismatch, recapture the same representative state, and compare again. Do not hide weak composition or incoherent assets with bloom, fog, vignette, grading, shake, or particles.

If no available tool can display the rendered game, complete structural/engine checks and state precisely that visual quality remains unverified. Do not call the result polished.

The building agent must first own routine rendered QA, including bind/T-pose detection, missing animation states, attachment failures, clipping, broken materials, obvious layout defects, and redundant gameplay-HUD text. Do not use later independent or user review as the discovery mechanism for these baseline failures. After builder-owned gates pass, a complete game or vertical slice still needs the rubric-required screenshot/motion review by a person or genuinely independent evaluation context that did not author the layout. Start with neutral raw artifacts and record the first read before giving the intended icon/action/progression mappings or the builder's desired verdict; later explanation cannot retroactively erase wrong guesses. Review the same exact candidate across menu, pause/runtime modal, settings, ordinary play/HUD, result/failure, the text-heaviest secondary surface, and integrated world/UI/telegraph/VFX states. Record who/what reviewed it, which viewport/state matrix was covered, and the defects found or absence thereof. A handoff cannot claim PASS from prose that a capture was reviewed: attach the concrete files and acceptance context required by `evals/rubric.json`. Optional user preference feedback can refine taste but does not replace either acceptance layer.

For a complete fixed-camera isometric case, use `assets/isometric-complete-review.template.md`; the early rendered art verdict must precede bulk level authoring, and the final review must include the density/composition matrix rather than only the best-looking frame.

For a fixed/high-angle 3D district/arena case, use `assets/high-angle-3d-district-review.template.md` as the builder-owned precursor. It must fail routine boundary, massing, repetition, semantic-density and camera-motion defects before independent or owner review.

At handoff, identify the states and resolutions inspected, the independent reviewer/context, and any visual state not reached. If builder-owned visual QA is complete and only the required independent verdict is unavailable, the candidate may be `BUILDER_COMPLETE / READY_FOR_HUMAN_TEST` but is not `PUBLICATION_CERTIFIED`; do not call it vaguely unready or turn the missing verdict into a screenshot checklist for the user.
