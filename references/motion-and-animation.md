# Production Motion and Animation

Read this whenever visible motion materially carries interaction, state, personality, physical action, automation, travel, UI feedback, camera response, or VFX timing. It complements character, vehicle, UI, audio, and genre-specific guidance. Motion is not complete because a `Tween`, `AnimationPlayer`, imported clip, or changing transform exists.

For a complete game or production slice, fill `assets/production-motion-review.template.md` and pass it as builder-owned routine QA. A separate character-motion contract is still required when a production character moves.

## Author the motion direction before multiplying it

Define a small motion language from the visual direction and core loop:

- physical/stylized weight, elasticity, inertia, cadence, and exaggeration;
- which actions may anticipate, overshoot, squash, shake, trail, or snap, and which must remain rigid or precise;
- the hierarchy of primary action, reward, danger, ambient motion, UI response, and camera response;
- input-to-visible-response, action, settle, loop, and interruption budgets;
- rules for path shape, facing, contact, attachment, depth/sorting, and reduced motion;
- how sound and VFX align to cause, contact, settlement, and consequence.

Preserve an explicit user reference or requested style, but translate its motion principles rather than copying protected characters or presentation. If the direction is open, compare motion-feasible art routes in the art-direction gate. A beautiful still that would require unavailable rigs, inconsistent sprite views, or unbounded bespoke animation is not a viable production direction.

Build one representative motion cell before bulk assets/content. It should include the core input response, one complete world/system action, a visible reward or state change, and a crowded or repeated state at gameplay scale. Reject the direction early if it only looks convincing in a still, enlarged preview, isolated rig viewer, or slowed recording.

Use `assets/motion-lab/` as an editable mechanism reference for press/reward, work/contact, travel/turning and panel interruption. Run its good and deliberately broken variants to calibrate observations. It is a teaching fixture, not production art or a required look. Adapt timing and geometry to the game's reference; compare matched cycles at 1x speed. Do not claim that its deterministic assertions certify naturalness. Bind the recording and actual watchback observations through [evidence-integrity.md](evidence-integrity.md).

## Use scene-authored motion ownership

- Keep reusable animations, curves, state machines, markers, sockets, and effect/audio anchors in the scene or external resources that own the visual action.
- Use `AnimationPlayer` for authored multi-property timing and events that benefit from editor timelines. Use `AnimationTree` when blending, transition graphs, or root motion materially improve the result. Use a fresh bound `Tween` for simple dynamic endpoints; do not grow choreography into scattered anonymous tweens.
- Keep gameplay outcome authoritative in gameplay state. Animation may expose authored contact/event markers, but a skipped, sped-up, interrupted, or reimported clip must not duplicate or lose transactions.
- Separate simulation position from presentation offsets. Recoil, squash, hover, selection, and shake should not corrupt collision, navigation, container allocation, or the next motion's start state.
- Give every moving object one transform owner at a time. Competing tweens, animation tracks, physics, navigation, and parent motion are a common source of jitter, drift, or snapping.
- Store tunable duration, speed, blend, anticipation, overshoot, path, and amplitude values in named resources or focused scene properties rather than unrelated magic numbers.

Official Godot references: [AnimationPlayer](https://docs.godotengine.org/en/stable/classes/class_animationplayer.html), [AnimationTree](https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html), [Tween](https://docs.godotengine.org/en/stable/classes/class_tween.html), and [PathFollow3D](https://docs.godotengine.org/en/stable/classes/class_pathfollow3d.html).

## Shape motion from cause and material

Do not apply one generic ease, bounce, rotation, or scale pulse to every event.

- Input response starts immediately without delaying the authoritative action. Make press, hold, release, disabled, and repeated-input behavior distinct when the control supports them.
- Organic or expressive actions usually benefit from clear poses, arcs, overlap, and follow-through. Rigid machinery benefits from constrained axes, staged acceleration/deceleration, stops, latches, and vibration only where physically motivated.
- Heavy objects need slower acceleration/settle and convincing contact; light objects may react faster. Overshoot on a rigid vehicle, wall, meter, or mechanical stop is a defect unless the style explicitly supports it.
- Constant-speed travel is appropriate for belts or deliberately uniform motion, not a universal default for arrivals, turns, pickups, rewards, panels, or characters.
- Squash/stretch must preserve the intended volume and pivot/contact. Scaling an entire world object or button around the wrong origin often reads as breathing, sliding, or layout wobble rather than impact.
- Anticipation cannot make controls feel late. When gameplay must respond immediately, separate the authoritative response from a short presentation anticipation or use anticipation in the target/world reaction.
- Settle and recovery must end in an exact reusable state. Subsequent cycles must not accumulate scale, rotation, opacity, offset, material, or camera error.

Judge spacing, not only duration: inspect where the object is on successive frames. A custom cubic curve can still produce a dead start, sudden middle jump, or floaty stop.

## Travel, turning, contact, and transfer

For any object that visibly travels:

- use a path or steering solution appropriate to the scene rather than independent X/Y/Z tweens that cut corners or drift through geometry;
- align facing to motion or authored path tangent, with bounded turn rate and a declared exception for strafing, reversing, hovering, or rail motion;
- prove acceleration, cruise, braking, stop alignment, reverse, interruption, and resume where those states occur;
- keep the visible pivot, collision footprint, shadow, trail, and effect origin synchronized;
- verify the exact production route under the shipping camera, including tight turns, endpoints, queues, and dense interactions.

For vehicles and wheeled props, check heading, steering pose, wheel roll from traveled distance, stop/park alignment, body motion, and reverse semantics. A car that translates sideways, rotates only after reaching a waypoint, or keeps static wheels cannot pass as finished transport motion.

For pickup, placement, crafting, repair, harvesting, service, or factory transfers, define approach -> align -> contact -> work/transfer -> release -> settle. The object must visibly belong to one source/hand/tool/socket/slot at a time. Reject gaps, penetration, teleporting between owners, work effects that miss the target, or rewards that settle before the visible cause.

## Loops, automation, and crowds

Repeated motion exposes defects that a single action hides.

- Make loop boundaries positionally and temporally clean unless a deliberate discontinuity is part of the style.
- Avoid synchronized identical ambient or worker cycles. Use bounded phase, clip, pose, route, or timing variants while preserving causality and throughput.
- Do not randomize every property independently. Variation should follow authored families and semantic state, not produce nervous noise or inconsistent machine timing.
- Preserve attention hierarchy. Background loops use lower contrast/amplitude/frequency than the current action, reward, warning, or decision.
- At high automation rates, aggregate or transition to a readable continuous loop instead of compressing every one-shot below perceptual clarity or spawning an effect/sound for every transaction.
- Test long running time for drift, phase collapse, leaked tweens, stale callbacks, queue overlap, animation starvation, and performance spikes.

## 2D, 2.5D, and 3D specifics

For 2D/frame animation, verify pivot stability, frame cadence, silhouettes, contact markers, sprite-facing coverage, sorting, pixel-grid behavior when applicable, and no accidental one-frame pops or scale changes. Generated in-betweens do not excuse melting contours, texture crawl, inconsistent volume, or identity drift.

For 2.5D, also verify world/depth motion against the camera: characters and props remain grounded, scale and sorting do not pop across depth bands, 2D effects share the world perspective, and billboard/flipbook orientation does not detach from the contact.

For skeletal 3D, verify deformation, root-motion policy, foot/hand contacts, blend poses, retarget scale/orientation, attachments, and interruption recovery. IK can repair bounded contact differences; it cannot rescue incompatible clips, wrong proportions, or an invalid rig.

For procedural animation, constrain noise, springs, look-at, secondary motion, and physics reactions with stable reference frames, damping, limits, pause behavior, and deterministic reset. Raw per-frame random jitter is not life.

For UI, animate an inner visual wrapper when scale/rotation would otherwise disturb `Container` allocation. Preserve hit targets, visible focus, optical center, neighbor rectangles, modal ownership, and reduced-motion semantics. A cascade of bouncing cards is not a substitute for hierarchy.

## Builder-owned validation

Declare project-specific budgets before judging the capture; do not invent permissive thresholds after seeing it. Measure what applies: response latency, durations, speed/acceleration/turn rate, tangent/heading error, lateral slip, path/endpoint error, contact gap/penetration, loop seam delta, callback/settlement count, phase distribution, interruption recovery, and frame-time cost.

Use a project-owned production-path probe to exercise the actual scenes and inputs. Deterministic checks should prove:

- the real gameplay event dispatches each required state exactly once;
- motion progresses with elapsed time rather than frame count and respects the chosen pause/time-scale policy;
- paths, facing, contacts, attachments, endpoints, and ownership stay within declared bounds;
- skip, spam, interruption, restart, scene change, save/load, and reduced-motion paths settle correctly;
- dense simultaneous loops preserve performance and do not synchronize, overlap, or starve important feedback;
- representative animation resources and callbacks survive import/reimport.

Then capture raw target-build motion at the shipping camera and normal playback speed. Cover core input response, one complete representative loop, travel/contact when present, dense simultaneous motion, and interruption/recovery. Watch the entire recording, use `scripts/mjpeg_avi_watchback.py` for Godot MJPEG integrity/contact sheets, and inspect the frames or video visually. Decoder success and coordinate assertions cannot certify naturalness.

Fail builder acceptance for visible sliding, floating, mechanical uniformity, weightless starts/stops, wrong pivots, linear path corners, late facing, contact gaps/penetration, animation-state pops, broken blends, loop seams, repetitive phase lock, over-animation, camera/VFX/audio mistiming, or movement that only looks acceptable in slow motion. Record exact timestamps and disposition in the review template.

Human preference may refine personality, stylization, intensity, or taste. It must not become the discovery mechanism for the routine defects above.
