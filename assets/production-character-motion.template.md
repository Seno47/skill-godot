# Production Character Motion Contract

Use this when a production player character, companion, enemy, or other focal actor is expected to move. This is a builder-owned release gate: routine animation defects must be found and fixed before optional user preference feedback.

## Applicability and production ownership

- Build/revision:
- Character/scene:
- Expected motion role:
- Production visual node and animation owner:
- Skeleton/rig or sprite animation resource:
- Retarget/source rig, when used:
- Intentionally static or limited-animation exception, with brief evidence:

## Required state contract

List only states required by the brief and ordinary play. Idle and locomotion are normally required for a character that stands and moves; context actions are required when the game presents them as character actions.

| State | Production clip/state | Real gameplay trigger | Loop/transition policy | Target-build artifact | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|---|
| Idle/standing | | | | | NOT TESTED |
| Locomotion | | | | | NOT TESTED |
| Context action 1 | | | | | NOT TESTED |
| Context action 2 | | | | | NOT TESTED |
| Failure/success or other brief-required state | | | | | NOT TESTED |

## Deterministic builder checks

| Check | Evidence | PASS / FAIL / NOT TESTED |
|---|---|---|
| Required clips/states resolve on the production character, not only on an imported preview rig | | NOT TESTED |
| Ordinary idle and locomotion do not remain in bind/rest/T-pose | | NOT TESTED |
| Sampled production pose changes over time for required looping states | | NOT TESTED |
| Required action dispatch is caused through the real gameplay path | | NOT TESTED |
| Retarget/root orientation, scale, loop boundaries, and contacts are plausible | | NOT TESTED |
| Source mannequin/preview mesh is hidden or absent in the shipping scene | | NOT TESTED |
| Required hand/socket/effect attachments follow the animated owner through representative poses | | NOT TESTED |
| Reset, interruption, restart, and scene transition do not leave a frozen or stale pose | | NOT TESTED |

For skeletal 3D work, record which stable bones or pose features were sampled and why they should move. A single root transform is insufficient when in-place clips keep the root still. For frame-based 2D work, record animation/frame progression, loop boundaries, pivot stability, and required attachment markers.

## Target-build motion evidence

- Raw idle recording:
- Raw locomotion recording:
- Raw context-action recording:
- Gameplay-size pose/contact sheet:
- Attachment-follow evidence:
- States/resolutions/camera framing:
- Builder observations: bind/rest/T-pose, duplicate mannequin, frozen tracks, loop pops, foot sliding, contact mismatch, detached props/effects, state-transition lag:

A still image can expose a T-pose but cannot prove motion, looping, state dispatch, or attachment following. Preserve a short raw target-build recording at the real gameplay camera and inspect it at normal speed. Deterministic pose assertions support this review; they do not replace it.

## Acceptance ownership

- Builder-owned baseline verdict: PASS / FAIL / NOT TESTED
- Objective defects found and disposition:
- Optional final human preference notes: unrecorded
- Remaining limitations:

Human preference can refine weight, personality, exaggeration, or taste after the baseline passes. It must not be used to defer routine defects such as a bind/T-pose, absent locomotion, gameplay states that never dispatch, a visible source mannequin, or an attachment that does not follow its animated bone/socket.
