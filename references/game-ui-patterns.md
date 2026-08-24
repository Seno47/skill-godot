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

## Verification

Capture the same HUD states over quiet and dense/moving gameplay:

- hidden/peek/persistent/expanded transitions;
- active-modality prompt changes after real input and rebinding;
- simultaneous notification burst, deduplication, and critical preemption;
- world-space target near/far, partially occluded, off-screen, and restored;
- fixed-layout counters at representative numeric/localized extremes;
- pause, focus loss, scene transition, resize, and reduced-motion mode;
- controller focus path and touch reachability where supported.

Fail the review if UI obscures threats/routes, prompt glyphs disagree with actual bindings, modality cleanup cancels input, important world UI has no readable fallback, counters shift layout, notifications starve or stack without bound, or the HUD only looks coherent in a static designer-authored screenshot.
