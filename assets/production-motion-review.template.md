# Production Motion Quality Contract

Use this for every complete game or production slice with visible motion. This is builder-owned routine acceptance; it complements specialized character, vehicle, camera, UI, and genre contracts.

## Candidate and motion direction

- Build/revision:
- Target/runtime and renderer:
- Shipping camera/viewports:
- Visual/motion reference and explicit exclusions:
- Weight, elasticity, inertia, cadence, and exaggeration rules:
- Primary / reward / danger / ambient / UI / camera motion hierarchy:
- Reduced-motion policy:
- Intentionally static or limited-motion exception, with brief evidence:

## Motion inventory

| System/action | Player-visible purpose | Real trigger and transform owner | Anticipation -> action/contact -> settle | Path/facing/attachment rule | Interruption/pause/reduced-motion rule | Raw artifact | Verdict |
|---|---|---|---|---|---|---|---|
| Core input response | | | | | | | NOT TESTED |
| Representative world/system cycle | | | | | | | NOT TESTED |
| Travel/turn/transfer/contact, if present | | | | | | | NOT TESTED |
| Reward/state transition | | | | | | | NOT TESTED |
| Ambient/background loop family | | | | | | | NOT TESTED |
| Dense simultaneous state | | | | | | | NOT TESTED |

## Declared measurable budgets

Use only applicable metrics and set them before reviewing the final capture.

| Metric | Declared budget/rationale | Production-path measurement | Verdict |
|---|---|---|---|
| Input to first visible response | | | NOT TESTED |
| Action/contact/settle duration | | | NOT TESTED |
| Speed, acceleration/deceleration, turn rate | | | NOT TESTED |
| Tangent/heading error and lateral slip | | | NOT TESTED |
| Path/endpoint/parking/alignment error | | | NOT TESTED |
| Contact gap/penetration and ownership transfer | | | NOT TESTED |
| Loop position/pose/velocity seam | | | NOT TESTED |
| Exactly-once callback/reward settlement | | | NOT TESTED |
| Phase/variant distribution for simultaneous loops | | | NOT TESTED |
| Interruption/restart recovery | | | NOT TESTED |
| Dense-state frame-time/allocation budget | | | NOT TESTED |

## Deterministic production-path checks

| Check | Evidence | PASS / FAIL / NOT TESTED |
|---|---|---|
| Real gameplay input/event dispatches each required state; direct test-only playback is not the sole trigger | | NOT TESTED |
| Motion is elapsed-time based and has an explicit pause/time-scale policy | | NOT TESTED |
| One transform owner controls each moving object at a time | | NOT TESTED |
| Path, facing, pivot, shadow, collision, trail, and effect/audio anchors remain synchronized | | NOT TESTED |
| Visible contacts/transfers use the authored marker/socket/slot and do not gap, penetrate, or teleport between owners | | NOT TESTED |
| Callback/transaction/reward settles exactly once under input spam, skip, speed-up, and interruption | | NOT TESTED |
| Restart, scene change, save/load, and resume restore a valid reusable state | | NOT TESTED |
| Repeated cycles have clean seams and intentional phase/variant distribution | | NOT TESTED |
| Dense automation/crowd state stays within the declared performance and attention hierarchy | | NOT TESTED |
| Imported/generated animation resources and event bindings survive reimport | | NOT TESTED |

## Dimension-specific checks

- 2D: pivot/frame-grid/cadence/facing/sorting/contact-marker result:
- 2.5D: depth/grounding/perspective/billboard/effect-origin result:
- Skeletal 3D: deformation/root-motion/blend/IK/contact/attachment result:
- Vehicle/travel: tangent-facing/turn timing/wheel roll/parking/reverse result:
- UI: inner-wrapper/container allocation/hit target/focus/optical center result:

## Raw target-build watchback

| Required state | Raw video and timestamps | Trace/report | Builder observation | Verdict |
|---|---|---|---|---|
| `core_input_response` | | | | NOT TESTED |
| `representative_system_cycle` | | | | NOT TESTED |
| `travel_or_contact` | | | | NOT TESTED |
| `dense_simultaneous_motion` | | | | NOT TESTED |
| `interruption_recovery` | | | | NOT TESTED |

- MJPEG decoder report, when applicable:
- Ordered contact sheets and whether inspected:
- Entire recording watched at normal speed: YES / NO / UNAVAILABLE
- Shipping FPS/playback speed confirmed:
- Exact timestamps of defects and recaptured fixes:

## Perceptual rejection checklist

Marking a line PASS means it was inspected in motion at gameplay size.

- [ ] No sliding, floating, late facing, linear-corner snap, wrong pivot, or detached shadow/trail.
- [ ] Starts, stops, turns, anticipation, impact/contact, settle, and recovery communicate suitable weight.
- [ ] Arcs/spacing/easing fit the material and action; one default bounce/ease is not reused indiscriminately.
- [ ] No contact gaps, penetration, ownership teleport, effect miss, reward-before-cause, or impossible pose.
- [ ] No bind/rest leakage, broken blend, stale pose, deformation, one-frame pop, loop seam, or accumulated transform drift.
- [ ] Repeated actors/machines do not move in robotic phase lock or nervous random noise.
- [ ] Primary action remains dominant; ambient/UI/camera motion does not compete or cause discomfort.
- [ ] Audio/VFX/camera peaks align with visible cause/contact/consequence.
- [ ] Normal speed looks finished; slow motion or selected stills are not hiding defects.
- [ ] Reduced motion preserves state, feedback, and completion without merely disabling all communication.

## Acceptance

- Builder-owned baseline verdict: PASS / FAIL / NOT TESTED
- Objective defects found and fixed:
- Remaining external preference/taste questions:
- Evidence limitations:

A deterministic trace, valid animation resource, decoder PASS, or contact sheet alone cannot award PASS. The builder must inspect the raw exact-candidate motion and fix routine visible defects before handoff.

