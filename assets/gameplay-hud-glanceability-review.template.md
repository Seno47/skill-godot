# Gameplay HUD Glanceability Review

Use this blocking complete-game gate for persistent gameplay HUD, contextual prompts, objectives, telemetry, waypoints, and warning clusters. The builder owns the information inventory and obvious cleanup; a reviewer or genuinely separate evaluation context that did not author the HUD owns the final glanceability verdict.

## Context and support contract

- Build/artifact:
- Builder/context:
- Independent reviewer/context:
- Reviewer did not author the HUD: NOT TESTED
- Gameplay focal region or moving action that must remain visible:
- Supported viewports/input modes:
- Representative locales and longest expected dynamic values:
- Raw target-build capture folder:
- Annotated capture/report artifact:

## Information inventory

Audit every visible text line or independent reading zone, not only whole panels. Classify it as `persistent`, `contextual/peek`, `expanded`, or `remove`, then make one explicit decision: `keep`, `shorten`, `iconify`, `world-cue`, or `remove`.

| ID | Current text/zone | Player decision it supports | Frequency/urgency | Visibility class | Encoding now | Decision | Why text must remain or how it changes | RU/EN stress |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

Titles such as “Current objective”, “Health”, “Water”, “Integrity”, route/role captions, units, and repeated status words do not earn permanent space merely by being localized. If position, shape, an authored icon, meter behavior, or a learned world cue already communicates the category, remove or shorten the duplicate caption. Keep longer text for a newly introduced objective, rare event, tutorial, ambiguity resolution, or expanded/accessibility view.

Also inventory the non-text channel for every critical state/action. A blank entry means the player must read; decide whether an authored icon, meter, state shape, world cue, material, motion, contact marker, sound, or spatial relation should carry the first-glance meaning. Reject large panels and repeated identical labeled rectangles as the dominant complete-game language even when localization and layout pass.

## Icon and non-text language contract

| Telemetry/state | Authored icon/shape/meter/world cue | Recognizable at final size | Non-color channel | Accessible name/tooltip/first-use label | Progressive-disclosure rule | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|---|---|
| | | | | | | NOT TESTED |

Prefer icon-first telemetry for frequently checked health, water/ammo/energy, vehicle/team integrity, checkpoint/route, and similarly stable resources when the meaning can be learned reliably. This is not an icon-only mandate:

- ambiguous or unfamiliar symbols need an accessible name, tooltip, short first-use label, legend, or expanded view;
- do not rely on color alone; retain shape, fill direction, pattern, position, text/value, sound, or another channel appropriate to the state;
- a short teaching label may disappear after demonstrated recognition, leaving the learned symbol/meter;
- numeric values remain when precision changes decisions; category captions may still be redundant;
- use one authored icon family with coherent stroke/fill, perspective, corner/shape language, optical weight, palette, and final-size behavior;
- emoji, arbitrary Unicode glyphs, default editor icons, unexplained AI-drawn symbols, and stylistically unrelated icon packs are not production UI.

## Simultaneous reading-load matrix

Annotate every visible text zone in the raw frame. Record project-owned measurements for comparison; do not invent universal maximums after seeing the result.

| State ID | Raw annotated artifact | Independent text-zone count | Persistent text-area ratio | Required gaze transfers from action focus | Competing objective/prompt zones | Critical state understood in a brief uncoached glance | PASS / FAIL / NOT TESTED |
|---|---|---:|---:|---:|---:|---|---|
| `hud_quiet` | | | | | | | NOT TESTED |
| `hud_normal` | | | | | | | NOT TESTED |
| `hud_dense` | | | | | | | NOT TESTED |
| `hud_vfx_peak` | | | | | | | NOT TESTED |

Count separated headings, captions, objective paragraphs, telemetry labels, values with units, prompts, notifications, and route text as independent zones when the eye must move or parse them separately. Record the union or annotated sum of their runtime screen area relative to the viewport, and note whether critical telemetry is split across distant corners. Numbers are regression evidence, not automatic design approval: the reviewer must still state what can be recognized without reading.

## Objective, prompt, and world-cue coexistence

| Check | Evidence | PASS / FAIL / NOT TESTED |
|---|---|---|
| The current objective is a short action-oriented phrase rather than a permanent heading plus sentence | | NOT TESTED |
| A contextual teaching/action prompt appears only when relevant and does not compete with a large persistent objective panel | | NOT TESTED |
| Waypoints, landmarks, highlights, or world-space cues carry route/target meaning when they are more immediate than another sentence | | NOT TESTED |
| Rare explanation can expand on demand without keeping every phrase persistent | | NOT TESTED |

## Aim, trajectory, route, and intent cues when applicable

| State | Raw artifact | Owner/origin and direction | Contact/bounce/turn meaning | Endpoint and validity/consequence | Art-family fit | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|---|---|
| Ordinary preview | | | | | | NOT TESTED |
| Multi-contact / changed direction | | | | | | NOT TESTED |
| Invalid / blocked | | | | | | NOT TESTED |
| Dense gameplay / confirmation | | | | | | NOT TESTED |

Exact physics/math supports this table but cannot pass a raw debug-looking `Line2D`, mesh strip, polygon, dots, or arrow that does not belong to the selected shape/material/motion language.

## Localization and accessibility stress

Review at least two representative language lengths, normally RU and EN when both ship. Verify that icon-first telemetry does not depend on one language's short label, that dynamic values remain stable, and that accessible names/tooltips/expanded descriptions remain available even when visible captions are reduced.

## Independent questions

- Which critical states can be recognized without reading any sentence?
- Which captions merely name an already obvious icon, meter, position, or grouping?
- Can the reviewer state the immediate objective after a brief glance while normal/dense action continues?
- Does understanding require scanning several distant corners or reading competing objective and prompt panels?
- Do the icons belong to one authored visual identity and remain distinguishable without color alone?

## Final verdict

- Builder inventory completed and obvious redundant text removed: NOT TESTED
- Icon/non-text telemetry is coherent, learnable, and accessible: NOT TESTED
- Quiet/normal/dense/VFX reading load is acceptable: NOT TESTED
- Objective/context/world-cue hierarchy is glanceable: NOT TESTED
- RU/EN or representative localization stress: NOT TESTED
- Independent gameplay HUD glanceability verdict: NOT TESTED
- Blocking defects and disposition:
- Remaining limitations:
