# Game UI and HUD Patterns

Read this in addition to `ui.md` when the interface lives over active gameplay, uses world-space/diegetic elements, has frequent prompts/notifications, or must work across several input modalities. This guide defines behavior and evidence; it does not impose one visual style.

## Define UI information states

Inventory the information needed in each gameplay state and choose one of these project-defined visibility levels per cluster:

- **hidden** — no current decision depends on it;
- **peek** — a brief contextual value or prompt appears after a relevant event;
- **persistent** — it affects continuous decisions and remains readable during motion;
- **expanded** — a deliberate modal/detail state shows history, comparison, inventory, map, or explanation.

Do not leave every meter persistent because it exists. Record what causes each cluster to enter/leave a state, its minimum visible time, and whether it may hide during cinematics, exploration, aiming, dialogue, photo mode, or low-pressure play. UI scripts observe the game state model; they do not duplicate game rules.

Establish hierarchy from the actual loop. A common starting order is survival/current status, immediate objective/decision, action feedback, then secondary flavor, but the brief may legitimately differ. Review hierarchy during active play, not on an empty background.

## Make persistent HUD glanceable

For a complete game or production slice, fill `assets/gameplay-hud-glanceability-review.template.md`. Inventory every visible text line/reading zone and state which player decision it supports. Classify it as persistent, contextual/peek, expanded, or remove; then decide `keep`, `shorten`, `iconify`, `world-cue`, or `remove`. A polished panel does not justify a permanent caption.

Use icon-first or shape/meter-first telemetry for frequently checked resources and stable states—health, water/ammo/energy, vehicle/team integrity, checkpoint/route, cooldown, carried objective—when players can learn the meaning reliably. Remove captions and units already communicated by position, grouping, fill direction, symbol, or the value itself. Preserve numbers when precision matters. Keep longer text for newly introduced objectives, rare events, tutorial steps, ambiguity, or an expanded/accessibility view.

Do not turn this into blind icon-only UI. Ambiguous symbols need an accessible name, tooltip, first-use label/legend, or expanded description. A short label may disappear after demonstrated learning. Never rely on color alone; combine it with shape, pattern, direction, value, position, motion, sound, or another suitable channel.

Inventory non-text communication as explicitly as text. For each critical state or action, name the icon, meter, shape, world cue, material, motion, contact marker, sound, or spatial relationship that carries meaning before a sentence is read. Reject large panels/repeated identical labeled rectangles when they hide the action, obscure priorities or force unnecessary reading, even if localization and touch targets pass. Comparison-heavy strategy, simulation or upgrade flows may legitimately use tables and repeated rows; assess decision clarity rather than counting rectangles.

Build one authored icon family that belongs to the game's identity: consistent stroke/fill, perspective, corner/shape language, optical weight, palette, and final-size rendering. Emoji, arbitrary Unicode glyphs, default editor icons, unexplained AI-drawn symbols, and a stylistically foreign icon pack remain placeholders.

Audit simultaneous reading load over quiet, normal, dense interaction, and peak-VFX gameplay. Annotate the independent text-zone count, screen-area ratio, required gaze transfers from the action focus, distant-corner scanning, and competing objective/prompt panels. Declare any project thresholds before final review rather than relaxing them after failure. Metrics support comparison; an independent reviewer must still say which critical states are recognizable without reading and whether the immediate objective is understood in a brief glance during action.

Prefer a short action-oriented objective phrase over a permanent heading such as “Current objective” plus a full sentence. Contextual teaching prompts may appear near the relevant action, but they should not compete simultaneously with a large objective panel. Use authored waypoints, landmarks, world highlights, or diegetic cues when they communicate route/target meaning faster than another sentence.

## Context prompts and input modality

- Generate prompts from the current `InputMap`/binding model so remapping changes the displayed glyph/text.
- Track the active modality without flickering when mouse drift or controller noise occurs; use a justified debounce/hysteresis policy.
- Keep the same action meaning across keyboard, controller, and touch while allowing platform-appropriate labels and placement.
- Ambiguous icons need a text label, tooltip, learned context, or accessible alternative.
- If an action is unavailable, distinguish hidden, disabled, blocked, cooldown, insufficient-resource, and unsafe states when those meanings affect player decisions.

Do not assume universal A/B, Cross/Circle, confirm/cancel, safe-zone percentages, or controller-first priority. Follow declared target/platform conventions and test every supported modality end to end.

## Notifications and combat feedback

Use a queue/arbiter when several systems can emit notifications. Define:

- semantic category and priority;
- deduplication/coalescing key;
- interruption and replacement policy;
- maximum concurrent items;
- minimum/maximum dwell time;
- reduced-motion behavior;
- whether sound, vibration, color, shape, text, or world effect also communicates the event.

Repeated numbers, loot, quest updates, warnings, and tutorials should not cover the next decision or create an unreadable wall. Aggregate rapid low-priority events; let critical warnings preempt flavor. Damage numbers and markers need clustering/occlusion rules and a screen-density budget.

## Aim, trajectory, route, and intent telegraphs

When a mechanic previews aim, launch, ricochet, movement, placement, area, route, or enemy intent, define the visual grammar rather than drawing raw debug geometry:

- origin/owner and current direction;
- every material contact, bounce, split, turn, or state-change point;
- endpoint, affected target/area, and whether the action is valid, blocked, dangerous, or uncertain;
- occlusion/depth policy and how the cue competes with hazards, actors, VFX, and HUD;
- selected shape, edge, material, color/non-color, motion, and sound language from the art contract;
- reduced-motion, color-vision, touch/precision, and low-graphics behavior.

Exact physics/math is necessary but not sufficient. A default `Line2D`, bright mesh strip, polygon, debug dot, or generic dotted arrow that looks foreign to the art family fails production review even when every bounce is correct. Inspect at quiet, multi-contact, invalid/blocked, dense-action, and final-confirmation states; the player should read direction, contacts, endpoint, and consequence without developer narration.

## Diegetic and world-space UI

A world-space indicator must remain readable under camera distance, perspective, occlusion, lighting, and motion. Record:

- world ownership/attachment point and maximum useful distance;
- scale/depth/occlusion policy;
- off-screen and behind-camera behavior;
- screen-space fallback for critical information;
- colorblind/non-color channel and reduced-motion behavior;
- how it competes with targets, hazards, pickups, and navigation.

Diegetic presentation does not excuse missing focus, localization, or accessibility. Critical information needs a usable fallback if the world presentation can leave the camera or become obscured.

## Stable dynamic layout

- Give timers, scores, ammo, combo counts, currencies, and localized records stable regions so value width does not push neighboring controls.
- Exercise minimum, zero, singular, typical, maximum, negative, overflow, and abbreviated forms that the game can produce.
- Do not rebuild HUD trees every frame. Update from state changes/signals or a bounded refresh cadence appropriate to the data.
- Separate decorative animation from hit targets and container allocation.
- Keep persistent HUD within the sightline/occupancy contract in `ui.md`; no amount of transparency proves that a large panel preserves world readability.
- Stress at least two representative locale lengths. A telemetry cluster that works only because one language has a short caption should be shortened/iconified or given an adaptive expanded form, not patched with smaller unreadable text.

## Verification

Capture the same HUD states over quiet and dense/moving gameplay:

- hidden/peek/persistent/expanded transitions;
- active-modality prompt changes after real input and rebinding;
- simultaneous notification burst, deduplication, and critical preemption;
- world-space target near/far, partially occluded, off-screen, and restored;
- fixed-layout counters at representative numeric/localized extremes;
- pause, focus loss, scene transition, resize, and reduced-motion mode;
- controller focus path and touch reachability where supported.
- annotated `hud_quiet`, `hud_normal`, `hud_dense`, and `hud_vfx_peak` frames with persistent versus contextual text inventory, keep/remove/shorten/iconify decisions, text-zone count/area, gaze-transfer notes, and RU/EN or equivalent localization stress;
- final-size icon family, non-color differentiation, first-use labels/tooltips/accessible names, and the progressive-disclosure state after the icon is learned;
- objective panel and contextual prompt both separately and in any legitimate simultaneous state, plus the corresponding waypoint/world cue.
- aim/trajectory/route/intent telegraphs in quiet, multi-contact, invalid/blocked, dense, and confirmed states, including their art-family fit and direction/contact/endpoint/validity meaning.

Fail the review if UI obscures threats/routes, prompt glyphs disagree with actual bindings, modality cleanup cancels input, important world UI has no readable fallback, counters shift layout, notifications starve or stack without bound, frequent telemetry requires reading redundant captions across several corners, repeated labeled rectangles dominate complete-game communication, objective and contextual prompt compete, icons are ambiguous without accessible teaching, color is the only state channel, icon art is emoji/default/mismatched, a trajectory/route/intent cue is mathematically correct but debug-looking or semantically incomplete, localization recreates long persistent labels, or the HUD only looks coherent in a static designer-authored screenshot.
