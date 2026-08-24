# Third-Person 3D Target-Build Review

- Build/artifact: unrecorded
- Godot version/renderer: unrecorded
- Reviewer/context: unrecorded
- Reviewer did not build the flow: NOT TESTED
- Input devices: unrecorded
- Supported resolutions/aspects: unrecorded
- Controller probe artifact: unrecorded
- Production-HUD mouse probe artifact: unrecorded
- Visibility probe artifact: unrecorded
- Builder-owned production character motion contract: unrecorded
- Raw screenshot/video folder: unrecorded

Do not change `NOT TESTED` to `PASS` from scene structure, code inspection, input-map entries, or builder narration alone.

Before this independent review, the builder must complete `assets/production-character-motion.template.md` for an animated production player. Idle, locomotion, brief-required actions, bind/rest/T-pose rejection, real gameplay dispatch, source-mannequin absence, and attachment following are routine builder-owned acceptance; they are not a checklist to outsource to the user.

## Movement and camera matrix

| Check | PASS / FAIL / NOT TESTED | Raw evidence and observations |
|---|---|---|
| Forward/strafe at spawn yaw matches screen direction | NOT TESTED | Unrecorded |
| Forward/strafe after 45° camera yaw remains camera-relative | NOT TESTED | Unrecorded |
| Forward/strafe after 90° camera yaw remains camera-relative | NOT TESTED | Unrecorded |
| Mouse horizontal and vertical orbit through real full-screen HUD | NOT TESTED | Unrecorded |
| Hands-on mouse sensitivity/acceleration comfort | NOT TESTED | Unrecorded |
| Right-stick horizontal and vertical orbit, deadzone and limits | NOT TESTED | Unrecorded |
| Zoom range and limits | NOT TESTED | Unrecorded |
| Recenter follows current actor facing | NOT TESTED | Unrecorded |
| Clear-space camera distance | NOT TESTED | Unrecorded |
| Camera collision: rear wall / tight corner / vertical or overhead obstruction | NOT TESTED | Unrecorded |
| Camera collision: leaving obstruction restores distance without snap or penetration | NOT TESTED | Unrecorded |
| Pause/menu return restores intended mouse capture | NOT TESTED | Unrecorded |
| Focus loss/re-entry causes no stale-delta jump or accidental action | NOT TESTED | Unrecorded |

Camera-collision PASS does not count as player-visibility PASS.

## Player visibility and occlusion matrix

Record the desired unobstructed camera position and authored feet/torso/head (or equivalent) sample points. Pair raw rendered captures with collision/debug-overlay evidence when checking proxy fidelity.

For every previously reported visibility failure, include that exact location, camera height/orbit, and elevation. A more convenient generic room is not regression evidence. Faded-object count, alpha value, or player silhouette alone cannot pass route readability.

| Case/location | Iterative occluders found | Player samples readable | Route readable | Cutaway/silhouette state | Full restoration | PASS / FAIL / NOT TESTED | Artifact |
|---|---:|---|---|---|---|---|---|
| Single occluder | Unrecorded | Unrecorded | Unrecorded | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Two or more simultaneous occluders | Unrecorded | Unrecorded | Unrecorded | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Open center of doorway/gate: negative proxy test | Unrecorded | Unrecorded | Unrecorded | No false cutaway expected | Unrecorded | NOT TESTED | Unrecorded |
| Soft/local cutaway group | Unrecorded | Unrecorded | Unrecorded | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Strong/room-scale cutaway group | Unrecorded | Unrecorded | Unrecorded | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Exact reported/highest-structure elevation view | Unrecorded | Unrecorded | Unrecorded | No bright veil/grid; route contrast retained | Unrecorded | NOT TESTED | Unrecorded |
| Silhouette fallback | Unrecorded | Unrecorded | Unrecorded | Soft fallback only | Unrecorded | NOT TESTED | Unrecorded |
| Clear after blocked cycle | 0 expected | Unrecorded | Unrecorded | No lingering cutaway/silhouette | Unrecorded | NOT TESTED | Unrecorded |
| Second representative route location | Unrecorded | Unrecorded | Unrecorded | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |

### Render/collision shell agreement

| Check | PASS / FAIL / NOT TESTED | Evidence |
|---|---|---|
| Camera-only proxies use an intentional layer/mask and do not replace gameplay collision accidentally | NOT TESTED | Unrecorded |
| Doorway, gate, arch, railing, and window openings relevant to the camera agree with the render shell | NOT TESTED | Unrecorded |
| Repeated blocked/clear cycles restore visibility, transparency, materials/shaders, render layers, and shadows | NOT TESTED | Unrecorded |
| Scene restart/transition contains no leaked hidden or transparent state | NOT TESTED | Unrecorded |

## Gameplay visibility

- Recorded HUD top/bottom/side occupancy limits: unrecorded
- Recorded central sightline/route corridor: unrecorded

| View | HUD occupancy measurement | World obstruction observation | PASS / FAIL / NOT TESTED | Artifact |
|---|---|---|---|---|
| Clean start camera | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Normal route | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Corner/tight interior | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Elevation/vertical target | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |
| Bright emissive geometry under final exposure/bloom | Unrecorded | Unrecorded | NOT TESTED | Unrecorded |

## First-use pressure

| Check | PASS / FAIL / NOT TESTED | Evidence |
|---|---|---|
| Required action is taught interactively before normal pressure | NOT TESTED | Unrecorded |
| Timer is frozen/relaxed until teaching succeeds, or pressure-as-teaching exception passes uncoached review | NOT TESTED | Unrecorded |
| Player can make one reasonable first-use mistake and still recover | NOT TESTED | Unrecorded |

## Human audio listening signoff

- Listener label: unrecorded
- Target build: unrecorded
- Playback device(s): unrecorded
- Approximate listening duration: unrecorded
- States heard: core action / common overlap / repetition / UI / pressure / success-failure / transitions / pause-focus / settings / other
- Defects found and disposition: unrecorded
- Final audio verdict: NOT TESTED

Automated stream, bus, format, loudness, spectral, and provenance checks are supporting evidence only; they cannot replace this listening signoff.

## Final gate verdicts

| Gate | PASS / FAIL / NOT TESTED | Evidence summary |
|---|---|---|
| Builder-owned production character motion prerequisite | NOT TESTED | Unrecorded |
| Third-person control contract | NOT TESTED | Unrecorded |
| Gameplay visibility, including player occlusion and restoration | NOT TESTED | Unrecorded |
| Pressure-safe interactive onboarding | NOT TESTED | Unrecorded |
| Human audio listening | NOT TESTED | Unrecorded |

## Limitations

No limitations recorded.
