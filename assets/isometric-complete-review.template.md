# Fixed-camera isometric complete-game review

Use this with the `new-isometric-fixed-camera-complete` rubric case. Preserve raw screenshots, hero-only masks, action traces, playtest notes, and build provenance. The builder may prepare evidence but cannot provide the independent final verdict.

## Build and camera contract

- Build/revision:
- Target platform and resolution:
- Fixed camera projection/rotation/zoom:
- Gameplay-safe frame and HUD occupancy budget:
- Spatial contract:
- Content-duration contract:
- Reviewer/context independent from builder:

## Early vertical-slice art gate

Complete this gate before bulk level authoring. Capture one representative gameplay frame at final gameplay size containing every required role.

| Role | Authored subject/state | Gameplay-size readable cue | Raw capture/artifact | Independent observation | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|
| Hero/keeper | | | | | |
| One mechanism: default and changed | | | | | |
| Beacon/delivery objective | | | | | |
| Representative structural and dressing decor | | | | | |
| Final-direction lighting/shadows/material response | | | | | |
| Gameplay HUD and tutorial feedback | | | | | |

- Does the frame communicate a specific world and core interaction rather than arranged primitives or sparse asset rows?
- Are the art source, palette, scale, outline/material, and density rules coherent at actual camera distance?
- Gate verdict: PASS / FAIL / NOT TESTED
- Bulk authoring was allowed only after revision/date:

## Character and route readability budget

Declare thresholds before evaluating captures. Produce a normal raw screenshot and a hero-only mask from the exact same camera/frame, then run `scripts/isometric_readability_audit.py --require-thresholds`.

| State | Screenshot | Same-frame hero mask | Report | Mean separation threshold/result | Edge separation threshold/result | Screen-size threshold/result | Independent silhouette/route verdict |
|---|---|---|---|---|---|---|---|
| Quiet/default floor | | | | | | | |
| Dense decor/mechanism | | | | | | | |
| Height/lift transition | | | | | | | |
| Route-changing/occlusion stress | | | | | | | |

- Character palette/material remains distinct from the lightest and most common floor/background values:
- Silhouette is recognizable without nameplate/tutorial highlight:
- Route endpoints, mechanism change, and next actionable space remain distinguishable:
- Readability gate verdict: PASS / FAIL / NOT TESTED

Numbers detect regressions; they do not replace raw visual review. Do not tune thresholds after seeing a failing final build without documenting the rationale and re-reviewing every state.

## Interactive onboarding state machine

The player must cause each transition in the shipping first-use flow. Text, developer narration, a scripted animation, or one generic interaction does not prove the sequence. Mark N/A only when the signed brief genuinely omits that mechanic; the canonical rubric case expects all rows.

| State/transition | Required player action | Target/cue | Immediate feedback | World/route state proven | Pressure policy | Target unobstructed | Uncoached evidence | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|---|
| Movement | Move to the taught space | | | | | | | |
| Pickup | Acquire/carry the light/object | | | | | | | |
| Context interaction | Use the correct nearby control | | | | | | | |
| Mechanism state change | Activate/toggle the mechanism | | | | | | | |
| Route change | Traverse the newly opened/changed route | | | | | | | |
| Height/lift | Enter, operate, and exit the height transition | | | | | | | |
| Beacon delivery | Deliver and receive completion feedback | | | | | | | |
| Restart/recovery | Recover from a reasonable mistake or restart | | | | | | | |

- Tutorial overlay never covers the highlighted target or the route needed to reach it:
- Failure pressure is frozen/relaxed until the relevant action and feedback are understood:
- First-use profile/build provenance:
- Onboarding gate verdict: PASS / FAIL / NOT TESTED

## Density and composition matrix

Review raw target-build captures at gameplay size, without editor overlays unless the row explicitly asks for one.

| State/location | Focal hierarchy | Foreground/midground/background structure | Landmark and route rhythm | Repetition/sparse-row defects | Occlusion/height readability | HUD/world competition | PASS/FAIL/NOT TESTED |
|---|---|---|---|---|---|---|---|
| Start/teaching area | | | | | | | |
| Typical puzzle | | | | | | | |
| Densest mechanism/decor area | | | | | | | |
| Highest/elevation transition | | | | | | | |
| Objective/result state | | | | | | | |

Reject default-white heroes lost on bright floors, long sparse tile rows without purposeful negative space, decoration that obscures routes, and nominal asset variety that does not improve gameplay-scale composition.

## Scope and independent verdict

- Content-duration verdict from `content-duration-contract.template.md`: PASS / FAIL / NOT TESTED
- Early art gate: PASS / FAIL / NOT TESTED
- Character/route readability: PASS / FAIL / NOT TESTED
- Onboarding state machine: PASS / FAIL / NOT TESTED
- Density/composition: PASS / FAIL / NOT TESTED
- Overall independent verdict: PASS / FAIL / NOT TESTED
- Blocking defects:
- Raw evidence location:
- Reviewer/date:
