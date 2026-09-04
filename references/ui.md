# Godot UI Production

Use this for menus, HUDs, dialogs, overlays, inventories, settings, editors, and input prompts.

For new UI or a substantial redesign, begin with [ui-design-workflow.md](ui-design-workflow.md) and its rendered design anchor before multiplying widgets. Conventional geometry and clear text are valid; judge hierarchy and fit instead of rewarding custom decoration. Use a shared capture packet across the applicable reviews.

## Author UI as scenes

- Build persistent interface hierarchy with `Control` nodes in `.tscn` scenes.
- Extract reusable widgets, panels, prompts, list rows, tooltips, and dialogs as scenes when they have identity, behavior, or repeated use.
- Use scripts for state and behavior, not for constructing ordinary widget trees in `_ready()`.
- Use a `CanvasLayer` only when the desired draw/camera relationship requires it.
- Keep world-space UI attached through an appropriate 2D/3D presentation layer while preserving native `Control` layout where possible.
- Treat a localized icon-plus-label action as one visual group. Built-in `Button.icon` placement and `Button.text` alignment are separate policies, so centered text plus a left-aligned icon does not prove that the combined composition is centered. When the intended group drifts by locale or viewport, keep the root `Button` as the interactive shell and author its presentation as `CenterContainer -> HBoxContainer -> TextureRect + Label`; use an analogous centered inner visual for icon-only buttons. Make decorative children ignore pointer input so the shell retains the full hit target.

## Layout before coordinates

- Use anchors for parent-relative placement and `Container` nodes for flow, grids, rows, columns, margins, and responsive composition.
- Use minimum sizes, size flags, separation, and theme constants rather than scripts full of pixel coordinates.
- Avoid fighting a container by manually positioning its children.
- Define a reference viewport and stretch policy, then test at supported aspect ratios, resolutions, UI scales, localization lengths, and safe areas.
- Use clipping/scrolling intentionally for content that can grow.
- In scrollable settings/lists, keep persistent chrome such as the dialog title and close/back action outside the scrolling body when they must remain reachable. Reserve an explicit scrollbar gutter and inspect the viewport at both scroll limits.
- Keep conceptually related helper text, footers, legends, and actions inside the same responsive composition/container unless an intentional overlay or safe-area relationship requires separate anchoring. A valid scene tree does not prove that independently edge-anchored elements will remain visually attached.
- For `TextureRect`, set both sizing and stretch behavior intentionally. `expand_mode` changes layout/minimum-size behavior but does not by itself preserve the texture's aspect ratio; non-cover icons/illustrations normally need an appropriate `KEEP`/`KEEP_ASPECT_*` stretch mode. Inspect the runtime rect inside its actual `Container`.
- For `Sprite2D` and other image-bearing controls, reject accidental non-uniform scale unless distortion is part of the art direction. Compare the source/intrinsic aspect ratio with the rendered bounds, not only the inspector values.

Absolute offsets are appropriate for deliberate fixed-size elements, fine art-directed adjustments, and canvas-like tools. They are not the default responsive layout system.

## Theme as a resource system

- Establish typography, font sizes, colors, spacing, corner/rule treatment, focus/hover/pressed/disabled states, and icon style as one system.
- Put shared styling in `Theme`, `StyleBox`, font, and icon resources instead of repeating per-node overrides.
- Use theme type variations for semantic variants. Avoid a unique style override on every control.
- Preserve contrast and readability over every gameplay background; add a designed backdrop/scrim where necessary.
- Do not leave accidental default styling that conflicts with the game's interface direction.
- Inspect actual sliders, tracks, thumbs, switches, checkboxes, option buttons, scrollbars, and focus/disabled states in the target build. Native `HSlider`, `VSlider`, `CheckButton` and `CheckBox` are appropriate mechanisms; use the shared `Theme`/scene-authored presentation to make a coherent readable family. Functional values and persistence do not establish craft, but replacing native behavior or adding decorative art is not required.
- Custom and scene-authored controls receive no automatic quality credit. A dashboard of repeated outlined rows/cards, obscure state glyphs, weak descriptions, inconsistent padding/weight, or unclear pressed/disabled states remains unfinished even when every value persists and no native Godot pixels remain.
- Treat `StyleBox` content margins, expand margins, border width, theme constants, and the control's runtime minimum size as different mechanisms. An expand margin draws outside the control rect and can be clipped without increasing its hit target; do not use it as hidden layout spacing.

## Interaction and input

- Support the input devices named in the brief. Keep prompts and button glyphs consistent with the active scheme when required.
- Configure focus neighbors or a reliable focus order for keyboard/controller navigation.
- Make modal focus capture/release explicit and restore sensible focus when dialogs close.
- Track the modality that opened a dialog. Pointer/touch opening must not unconditionally `grab_focus()` on a selectable value and make it look chosen before interaction; keyboard/gamepad opening must place visible focus on a meaningful first action. Exercise and capture these as separate flows.
- Provide visible hover, pressed, focus, disabled, selection, error, and loading states as applicable.
- Inspect focus/hover/pressed styles inside every clipping ancestor. Focus outlines that rely on `StyleBox.expand_margin_*` may be cut by a `ScrollContainer`; keep the state legible inside the allocated rect or provide intentional internal clearance.
- Keep hit targets appropriate to the target device and avoid hover-only information on touch.
- Separate UI actions from gameplay actions when simultaneous input would cause conflicts.
- For captured third-person mouse-look, review the real full-screen HUD's event routing. `Node._unhandled_input()` runs only after GUI handling, so a covering `Control` can consume `InputEventMouseMotion` even when the HUD looks non-modal. Either make passive HUD regions ignore/propagate the motion intentionally or receive captured look at an earlier suitable stage and gate it explicitly by gameplay/modal state. A direct controller-method call and an `InputMap` entry do not prove the production scene receives mouse motion.
- Do not clear focus or pressed state in `_input`/`_gui_input` on pointer release before `BaseButton` finishes its release action. If pointer-focus cleanup is required, let `pressed` emit first and release focus afterward (commonly deferred). Prove the target Web build emits `pressed`; hover feedback alone is not click evidence.
- Do not claim touch scrolling because a `ScrollContainer` exists. When overflowing content is touch-accessible, inject or perform a real `InputEventScreenTouch` plus `InputEventScreenDrag`, assert that scroll position changes, and still verify the exported browser/device gesture path.

## Information architecture and feedback

- Give the most important current decision/action the strongest hierarchy.
- Name standard consequential actions so an uncoached player can predict the exact result: resume, restart, retry, next/continue, return, new game/save, purchase, discard, and exit must not be hidden behind an atmospheric synonym. Theme language may be secondary. In menu, pause, and result states, copy and icon must predict the same effect and make progress loss/retention clear.
- Remove decorative labels, cards, icons, and meters that do not improve comprehension.
- Audit the whole interface flow—menu, settings, HUD, result, map/selector, upgrades/shop, and progression surfaces—for what is communicated visually versus only through text. Repeated identical labeled rectangles, large text panels, and localized tables do not become finished UI merely because their layout, touch targets, and transactions are correct. Prefer authored state art, icons, meters, spatial grouping, maps, world cues, and visible before/after change while retaining concise accessible text where symbols are not yet learned.
- Prefer progressive disclosure to a wall of equally weighted controls.
- Use animation to clarify state change, spatial relationship, causality, or priority. Keep it interruptible where interaction can reverse.
- Respect reduced-motion/accessibility requirements when the project targets them.
- Explain accessibility settings in player language. A label such as “Reduced motion” is not enough when its effect is ambiguous; add a concise description or preview of what changes while preserving the player's choice.
- Ensure text is real text when it needs localization, accessibility, or dynamic content; do not bake arbitrary UI copy into generated images.
- Test interpolated counts and records with locale-representative values for zero, singular, plural, and larger numbers. Do not ship English shortcuts such as `pulse(s)` or slash-separated word forms; use the project's localization/plural rules and inspect the result at the narrowest supported width.

For a complete-game main menu, separate navigation clarity from identity craft. The title must read as a deliberate wordmark or typographic composition at runtime size. Native `Label` text is valid when font, weight, spacing, line breaks, treatment, placement, and relation to the mark/background are authored; a huge default/common-font label is not automatically a wordmark. Audit every kicker, subtitle, tagline, and premise sentence for a player-facing purpose. Remove generic marketing/explanatory copy when the screen already communicates the game and choices. Apply the same anti-scaffolding standard to settings and results: a themed menu cannot excuse incoherent control states or a result screen whose panel repetition hides the result and next action.

Review the whole menu for template fingerprints, especially a small badge/kicker, huge title, decorative accent line, redundant “do X / survive Y” tagline, and four identical rectangular buttons over an interchangeable dark/gradient background. Individual devices may be appropriate, but an unexplained stack is not production identity. Create a clear primary/secondary action hierarchy, integrate the background/world motif, and record the independent verdict with `assets/menu-identity-craft-review.template.md`.

For camera-driven 3D play, budget persistent HUD in screen space before styling it. Record the intended maximum top/bottom/side band occupancy and a central gameplay sightline corridor for each supported aspect ratio; count opaque and strongly translucent backplates, not just label bounds. Measure runtime `Control` rects and review the same frame with representative world content. A project-specific budget is preferable to a universal percentage, but it must preserve the route, interaction target, horizon, and near-player hazards rather than merely justify an already oversized panel. Modal menus may cover the world intentionally; ordinary gameplay HUD may not.

Screen-space occupancy is not enough: a compact HUD can still impose excessive reading. For complete games/slices, use `assets/gameplay-hud-glanceability-review.template.md` with [game-ui-patterns.md](game-ui-patterns.md). Audit every persistent caption/heading/unit, prefer authored icon/shape/meter/world-cue telemetry for frequently checked states, preserve accessible teaching for ambiguous symbols, and review simultaneous text zones/gaze transfers during quiet, normal, dense, and peak-VFX play. Do not rely on emoji, arbitrary Unicode, default editor icons, unrelated icon packs, or color alone.

Review content semantics as well as localization and layout. Repeated selection cards must communicate a meaningful identity or distinction appropriate to the game—such as a short localized name, objective, mechanic, thumbnail, region, or other authored cue—plus availability/progress when useful. A grid of numbers with only generic statuses such as “New”, “Locked”, or a record value can be technically localized yet still read as placeholder content. Do not invent decorative prose where a deliberately number-driven design is clearer; document that choice and test comprehension.

For ordinary sequential numbering, prefer `1`, `2`, `3` over decorative `01`, `02`, `03`. Leading zeros need an actual diegetic, archival, timer/code, fixed-width, or art-direction rationale; they are not a default polish treatment.

For a complete game/slice, review the whole interface family together with `assets/cross-surface-production-craft-review.template.md` and [production-craft-and-product-approval.md](production-craft-and-product-approval.md). The raw packet includes main menu, pause/runtime modal, settings, ordinary play/HUD, result/failure, the text-heaviest secondary surface, and critical icons from one exact candidate. A polished menu cannot cover an unfinished pause/result; shared colors and aligned rectangles cannot cover missing hierarchy.

Audit visible pixels in addition to nodes. For critical icons and compound actions, compare source/viewBox bounds, rendered rects, final-size alpha/pixel bounds, optical center, internal padding, baseline, filtering/halo, and visible weight against neighboring family members. `scripts/icon_optical_audit.py` provides repeatable raster alpha metrics; independent final-size judgment still decides whether nominally centered assets look aligned and coherent.

Choose a navigation model before building a large selector. Record item count, expected revisit/comparison behavior, supported input, and narrow-screen reachability; then choose scrolling, pagination, chapters, search/filter, or a combination. Pagination needs visible current/total position, deterministic previous/next behavior, focus restoration, and no unreachable tail. Do not universalize one page size—derive rows/columns from the supported viewport matrix and touch targets.

Long localized card titles are content, not incidental overflow. Give name and status separate authored regions when both matter, test representative long strings on the narrowest viewport, and prefer a bounded two-line wrap when it preserves identity. Ellipsis is acceptable only when the full identity remains available and choices stay distinguishable.

For repeated compound settings such as audio buses, keep each label, current value, slider/control, and mute/action within one readable row/group. Use consistent substructure, separators/spacing, and enough viewport height that the initial scroll position does not accidentally expose an unexplained clipped half-control when a cleaner boundary is practical.

## UI verification

Inspect at minimum:

- default, hover/focus, pressed, disabled, selected, error, empty, loading, and overflow states that exist in the feature;
- raw main-menu, settings, text-heaviest result/map/upgrade surface, and ordinary gameplay captures for a complete game; identify which meanings remain text-only and whether repeated labeled rectangles dominate the hierarchy;
- the same exact candidate's pause/runtime modal and result/failure beside its menu, settings, ordinary HUD, and text-heaviest secondary surface; reject cross-screen hierarchy, typography, rectangle/card, control-state, and icon-family drift;
- blind first-read prediction of every critical menu/pause/result action and critical icon before implementation notes, expected mappings, or builder verdicts are shown; record uncertainty and wrong guesses rather than allowing later explanation to overwrite them;
- intrinsic/rendered/visible-alpha bounds, optical center, padding, baseline, filtering/halo, and relative weight for critical icons and icon-plus-label groups at actual final size;
- pointer-open and keyboard/gamepad-open focus flows as separate cases, plus mouse, controller, and touch interaction required by the target;
- narrow/wide and low/high resolution extremes;
- source-to-runtime aspect ratios for icons, illustrations, portraits, and thumbnails inside `Container` nodes;
- localized compound action buttons in at least two representative string lengths/locales at narrow and wide matrix points: assert that the inner visual group's center is within a justified tolerance of the root `Button` center; for icon-only buttons compare the icon visual center with the control center;
- long localization strings and dynamic values;
- localized numeric forms and placeholder substitution, including singular/plural records and result copy;
- UI over both quiet and busy gameplay backgrounds;
- persistent HUD runtime occupancy against its recorded budget, plus unobstructed central/route sightlines in representative 3D gameplay views;
- persistent HUD glanceability in annotated quiet/normal/dense/VFX frames: inventory each text zone, remove duplicated headings/captions/units, verify critical state recognition without sentence reading, review objective-versus-context-prompt competition, and stress representative RU/EN or equivalent locale lengths;
- authored icon-family coherence, final-size recognition, non-color state channels, accessible names/tooltips/first-use labels, and progressive disclosure after learning;
- pause/resume, scene transitions, and focus restoration.
- captured mouse-look through the production HUD: inject `InputEventMouseMotion` with `Input.parse_input_event()`, require both yaw and pitch change, then assess sensitivity hands-on in the target build;
- real overflow with a raw screenshot proving scrollbar thickness, contrast, gutter, grabber, and clipped-content boundary; serialized theme overrides or a theme constant alone do not pass;
- touch-drag movement of every required scroll surface, preferably with the reusable probe in `assets/godot-tests/touch_scroll_probe.gd` plus target-build interaction;
- before/hover/focus geometry for animated controls: the visual center stays stable within a justified tolerance and sibling/container allocations do not move unless reflow is intentional. Scale around a deliberate pivot after layout rather than changing minimum size or margins as an incidental hover effect.
- a full pointer press/release on affected `BaseButton` controls in the exported Web build, with an observable `pressed` signal/result after any modality-focus cleanup.

For guided onboarding overlays, verify the instruction panel, pointer/highlight, highlighted world target, and required control together at every compact matrix point. The target and required control must remain visible and tappable; a translucent card or glow does not excuse a blocking bounds intersection. Reflow or move the card to another region instead of merely shrinking critical text.

Reject the pass if controls overlap, images distort, a localized icon-plus-label group is visually off-center, an icon-only visual drifts from its hit target, related helper/footer content visually detaches, persistent HUD exceeds its recorded occupancy or blocks ordinary 3D sightlines, gameplay telemetry depends on redundant persistent captions or distant multi-zone reading, objective and contextual prompt compete, icons are ambiguous/unrelated/default/emoji without accessible teaching, color is the only state channel, localization recreates paragraph-like HUD, pointer-open creates a false selected/focused value, keyboard focus disappears, focus cleanup cancels the pending click, hover works without `pressed`, focus/hover art is clipped, an overflowing scrollbar is effectively invisible, touch drag does not move required content, compound rows lose ownership, list navigation hides or strands content, semantic cards look like placeholders, accessibility controls are unexplained, hover shifts neighbors, theme variants drift, default styling remains accidentally, a complete-game menu relies on generic title/tagline/button-stack composition without an independent craft verdict, or runtime scripts rebuild a hierarchy that belongs in a scene.

Useful official references:

- [Godot GUI documentation](https://docs.godotengine.org/en/stable/tutorials/ui/)
- [Using containers](https://docs.godotengine.org/en/stable/tutorials/ui/gui_containers.html)
- [Using themes](https://docs.godotengine.org/en/stable/tutorials/ui/gui_using_theme_editor.html)
- [`Button`: separate text and icon alignment](https://docs.godotengine.org/en/stable/classes/class_button.html)
- [`BaseButton`: release action and `pressed`](https://docs.godotengine.org/en/stable/classes/class_basebutton.html)
