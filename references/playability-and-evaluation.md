# Playability and Evaluation

Read this for a new game, a substantial vertical slice, or any task where the agent is expected to deliver a complete playable result. Startup without errors is not evidence that a game communicates a goal, closes its loop, or feels correct.

## Keep the run steerable and resumable

For an exploratory brief, expose a real playable slice early and checkpoint only at consequential taste, scope, platform, or paid-cost decisions. For a finished brief, make reasonable reversible decisions and continue autonomously. In both modes, preserve current verified truth in `assets/project-run-state.template.md` when the run is long: source/build IDs, current playable loop, commands, evidence, asset/cost state, next bounded actions, and blockers. Replace stale values rather than accumulating narration.

## Define the playable contract

Before implementation, reduce the brief to an observable contract:

- player role and immediate goal;
- core verb/loop and the feedback that confirms it;
- success condition and resulting state;
- failure or pressure condition and resulting state;
- restart/retry path;
- controls and supported input devices;
- first-use interactive teaching for any core action that a new player cannot safely infer;
- audible confirmation for the core action, pressure, success/failure, and other must-hear states;
- music/ambience behavior, volume/mute controls, and any intentional use of silence;
- target session length, camera, viewport, and performance budget.

For a sandbox without victory, define a meaningful repeatable activity and reset/recovery instead of inventing a win screen. For narrative/exploration work, define the reachable endpoint or evidence of progression.

## Make duration and content depth falsifiable

When the brief, store copy, or handoff claims a duration, chapter count, level count, or complete game, create `assets/content-duration-contract.template.md` before bulk authoring. Break the claim into authored objectives/puzzles, mechanic introductions, meaningful permutations/combinations, estimated uncoached first-solve time, and observed playtest time. Report tutorial time, menus, retries, grind, replay, and procedural/unbuilt assumptions separately.

Separate level IDs do not prove depth when they repeat the same layout, only change a parameter, mirror a route, or swap presentation. A short vertical slice may be excellent and pass as a slice, but it must not substantiate multi-hour release scope. A duration claim passes only when the authored-content arithmetic and uncoached playtest provenance support it; otherwise revise the label/scope or author and test the missing content.

## Build an observable state matrix

List the representative states before polishing:

| State | Required evidence |
|---|---|
| Boot/menu | correct scene, focus, legible action |
| Dialog by modality | pointer/touch open has no false selected state; keyboard/gamepad open has visible meaningful focus |
| Clean first use | shipping-default state is visible; the player performs the taught core action without developer narration |
| First control | input produces expected motion/action plus visual and audible feedback |
| Core interaction | collision/raycast/state change, coherent feedback, no soft lock |
| Pressure/failure | failure can occur and is communicated visually and audibly when appropriate; clean first use is not punished before the required action is taught |
| Success/progression | goal can be completed, state advances, and result feedback is distinct |
| Restart/transition | clean reset, no duplicate state or leaked nodes |
| Edge case | relevant boundary, empty/full, pause, or device change |

For a new complete game or production slice, first retain the pre-bulk `assets/art-direction-selection.template.md` record plus raw `style_anchor` and `representative_composition` frames. A user-fixed direction may skip alternative pitches but not its production translation and anchor; an open brief cannot let asset availability choose the style by accident. At final review, extend the visual portion with `quiet`, `normal_gameplay`, `dense_interaction`, `vfx_peak`, and `result`. These are raw target-build acceptance states, not five variants of an empty opening frame. Use `assets/production-art-state-review.template.md`; dense/contact states are where asset-family mismatch, intersections, bad depth, detached effects, primitive VFX, broken action poses, and empty placeholder panels must be caught.

For an open-ended new complete game, the representative slice is also a product boundary. After routine builder acceptance and before bulk levels/content, use `assets/product-owner-slice-decision.template.md`. Independent art/UX review can prove clarity and craft but cannot infer that the owner wants the concept multiplied. `APPROVE` or an explicit owner `WAIVE` authorizes bulk work; `REVISE` repeats the slice; `CLOSE` enters the non-success closure terminal.

Audit gameplay HUD separately with `assets/gameplay-hud-glanceability-review.template.md`. The same release-like build supplies annotated `hud_quiet`, `hud_normal`, `hud_dense`, and `hud_vfx_peak` frames plus a persistent/contextual text inventory. The builder removes obvious duplicated captions and establishes accessible icon/world-cue language; an independent reviewer then states what is recognizable without reading, whether the objective remains action-oriented, and whether distant text zones or a competing prompt overload active play.

Keep the matrix proportional. A one-screen toy may need five states; a save/load feature needs persistence and corrupted/missing-data cases.

For a complete game, the boot/menu evidence also includes the exported app icon and primary menu mark at their actual display sizes. Have an independent reviewer describe what the mark depicts before receiving the intended explanation; a coherent palette or clean arrangement of primitives is not evidence of game-specific identity. Record the result with `assets/semantic-identity-review.template.md`.

## Prove onboarding through action

For a complete game or vertical slice with a non-obvious mechanic, onboarding must be perceptually discoverable in the clean shipping frame and advance through an observable player action. The uncoached player must notice that guidance exists, bind the shown input/control to the relevant world/UI target, perform it, read the immediate feedback and consequence, and then enter the normal loop. Highlight or constrain the relevant target/control and wait for the intended input. If the player does not find the tutorial or cannot state what to act on, the gate fails even when localized text and internal state transitions exist. A paragraph, static hint, tutorial data field, localized string, or “How to play” page can support this sequence but cannot replace it.

Do not compress a multi-step core loop into one generic “interact” proof. Model onboarding as explicit states and transitions. For each brief-required verb or world consequence, record the target/cue, actual player input, immediate feedback, resulting gameplay/route state, failure-pressure policy, target visibility, and uncoached evidence. In the complete fixed-camera isometric case this ledger covers movement, pickup, context interaction, mechanism state change, traversal of the changed route, height/lift use, beacon/objective delivery, and restart/recovery. The player must cause every transition; narration, a scripted demonstration, or one final completion trace cannot stand in for the intermediate states. Use `assets/isometric-complete-review.template.md` for that canonical flow.

Test from the clean shipping profile with a person or independent evaluator who has not been coached on the mechanic. Evidence should show the prompt/state before the action, the actual input/state transition, feedback after success, and entry into the core loop. If the game's core action is genuinely self-evident and no tutorial is intended, document that decision and still verify first-action success without narration.

Do not let a pressure/failure timer undermine the teaching state. By default, freeze or substantially relax time pressure until the required onboarding action succeeds and its feedback is readable, then start or ramp normal pressure explicitly. A scripted first teaching action must not deliberately push the threat near failure or open a fail result as its normal consequence. Starting the shipping timer at scene entry is acceptable only when time pressure itself is the taught mechanic and an uncoached first-use test proves the player has enough time to understand, act, recover from one reasonable mistake, and enter the normal loop. A developer who already knows the controls is not evidence for this exception.

Review content-bearing progression UI during the same first-use test. Level/chapter/mission selectors should help a player form a useful expectation and distinguish choices; localization completeness and numeric ordering alone do not prove authored content. Generic status-only cards require an explicit minimalist rationale plus comprehension evidence or should gain meaningful localized identity/cues.

## Make testing deterministic

- Give important runtime state stable names, groups, signals, and debug observability.
- Seed randomness for evaluation and record the seed.
- Prefer a project-owned test driver that invokes gameplay actions or state transitions through supported interfaces.
- For touch-scroll claims, use the reusable `assets/godot-tests/touch_scroll_probe.gd` against an overflowing project fixture and assert the scroll delta; static node presence is not behavioral evidence.
- Accept test scenario arguments after Godot's `--`; keep them disabled in normal release paths.
- Do not add permanent cheats solely so an agent can claim completion.
- Keep timeouts and bounded exits so CI and agents cannot hang indefinitely.

Use the bundled runner for reproducible startup/capture evidence:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --scene res://tests/core_loop_test.tscn --frames 300 --user-arg scenario=core_loop --summary --json-output reports/core-loop.json
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode capture --scene res://scenes/main.tscn --frames 300 --fixed-fps 30 --output reports/core-loop.avi --summary --json-output reports/capture.json
```

If the user has not watched or played the current target build, create a short delivery proof after routine gates pass:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode capture --scene res://scenes/main.tscn --proof-seconds 15 --fixed-fps 30 --output reports/delivery-proof.avi --summary --json-output reports/delivery-proof.json
python <skill-dir>/scripts/mjpeg_avi_watchback.py --input reports/delivery-proof.avi --output-dir reports/delivery-proof-watchback --expected-duration-seconds 15 --sample-fps 4 --require-temporal-change --summary
```

Use a project-owned driver to begin in a composed frame, progress through representative input/core interaction/feedback/result states, and avoid dead time or one repeatedly looped pose. Initialize camera and capture state before the first rendered frame. `mjpeg_avi_watchback.py` requires only Pillow: it parses Godot's MJPEG AVI directly, validates the RIFF/video headers, declared and actual frame count, duration and every JPEG frame, then extracts endpoint-inclusive uniform frames and ordered contact sheets. It does not need ffmpeg, ffprobe, OpenCV, or imageio.

Watch the entire recording back before handoff and record the states/defects in `capture-manifest.template.json`. Inspect every generated sheet in order. A sampled packet makes framing, state progression and frozen/dead stretches model-visible, but it does not prove normal-speed smoothness, transient defects between samples, or audio. Prefer actual normal-speed playback when available. If playback is unavailable and full visual frame coverage is required, rerun with `--all-frames --max-samples <actual-frame-count>` and inspect every resulting sheet in order; record the absence of normal-speed/audio acceptance rather than silently promoting the packet. File creation, successful decoding, or an uninspected sheet is not watchback. This clip is a compact user-facing proof, not a substitute for uncoached play, the raw screenshot/state matrix, human audio listening, performance profiling, or independent review.

The runner does not inject keyboard, mouse, or controller input. Use a project test driver or an approved UI automation layer for input-dependent flows.

“Approved UI automation” does not mean desktop Computer Use by default. Prefer project-owned drivers, `Input.parse_input_event()`, Godot fixtures, CLI capture, and browser automation scoped to a Web export. Use desktop Computer Use only after explicit user opt-in or when a required native OS surface cannot be verified otherwise; do not start it solely for routine game clicks or screenshots. Builder-operated GUI automation remains builder evidence and cannot satisfy an independent or human acceptance owner.

## Assign acceptance ownership without outsourcing routine QA

Use the `acceptance_owner` attached to an applicable rubric gate:

- **builder:** objective routine acceptance that the implementing agent must autonomously exercise, inspect, and fix before handoff. Deterministic contracts, target-build runs, recordings, logs, and builder observations are valid evidence. Examples include clean import, restart, production character motion, input routing, collision, and attachment following.
- **independent:** comprehension, semantic reading, or visual/UX judgment that explicitly needs a person or genuinely separate evaluation context that did not build the flow. The builder still performs its own QA first; independence is a second acceptance layer, not a substitute for it.
- **human:** irreducibly perceptual signoff explicitly named by the rubric, such as representative audio listening. Automation and builder triage prepare the evidence but cannot promote the gate.
- **provider:** an external store, platform, service, certification process, or account owner supplies the final observation. The builder still prepares and verifies the exact candidate and every locally reproducible path first.
- **product_owner:** the user or explicitly identified owner decides whether an already builder-verified representative slice's core loop/concept and visual direction should be multiplied, revised, explicitly waived, or closed. This is a material product/taste decision before bulk work, not routine QA delegated to the user.

Optional user preference feedback is outside these blocking ownership classes unless the brief explicitly elevates it into acceptance. Ask for it to refine taste—animation weight/personality, tone, pacing preference—not to discover a bind/T-pose, missing locomotion, broken attachment, clipped UI, or other routine production defect. When a separate evaluator is available, use that evaluation context for required independent gates rather than making the user execute a QA checklist.

## Separate builder completion from publication certification

Use responsibility-scoped status instead of one ambiguous "ready/not ready" label:

- **Builder work remaining:** any applicable builder-owned gate is `FAIL` or `NOT TESTED` despite available authorized tooling; a routine defect is known; an independent/human/provider review returned `FAIL` and its actionable defects are not fixed; the exact candidate or evidence packet is missing; or a builder-owned quality floor remains below its pre-external threshold. Continue autonomously. Do not hand off a repair checklist.
- **`BUILDER_COMPLETE / READY_FOR_HUMAN_TEST`:** every applicable builder-owned gate passes on the exact candidate, the builder inspected the required raw states and motion, no known external-review failure remains unfixed, and the candidate plus review packet are ready. Required independent, human, provider, hardware, account, upload, or moderation evidence may remain `NOT TESTED` when it is genuinely outside the available authority or environment.
- **`PUBLICATION_CERTIFIED`:** the exact same candidate also passes every applicable external blocking gate and the final score/floors. Changing the candidate after certification invalidates affected evidence.
- **`PROJECT_CLOSED / USER_REJECTED`:** the user/product owner explicitly ended the project. Preserve the failure packet and unresolved gates, record `project_disposition.status=user_closed` with `continue_authorized=false`, make no READY/PUBLICATION claim, and stop until the user explicitly reopens it. This is a terminal disposition, not successful completion and not an escape from difficult builder work.

A `NOT TESTED` external gate is an evidence boundary, not delegated labor. Report it in one concise sentence, for example: "Publication certification is not claimed because representative human audio listening is external to this run." Do not end with instructions to open a console, upload an archive, run a human test, or publish unless the user explicitly asks for that workflow. Once the builder is complete, the user chooses whether to test, upload, or publish.

Do not force a builder to self-award a perceptual score that the rubric says only an external owner can establish. When a submitted dimension misses its final case floor, `eval_scorecard.py` may defer that floor to a pending external gate only if the same gate has an explicit score cap for that dimension and the honest builder score is at least that cap. Example: `audio_direction_quality=2` with `human_audio_listening=NOT TESTED` and cap `2` is ready for human listening; score `1` remains builder work. The final floor and publication verdict still require the external gate. This exception never applies to a missing/failed builder gate or an external gate without a matching cap.

If an external review returns a defect, ownership of the repair returns to the builder. Fix it, rerun affected builder gates, regenerate the candidate, and request only the narrow re-review that remains external. Do not ask the user to work through a general QA checklist.

Before any independent/product-owner review, reset the exact launch modality after the final builder run using `assets/review-profile-reset.template.md`. A clean browser automation profile does not cover Godot Editor Run or an exported desktop app; reset the actual `user://`/application-data envelope including primary and backup/recovery state, then capture the clean first boot. Keep seeded QA state in a separately labeled profile.

## Evaluate in layers

1. **Static:** scene graph, paths, resources, asset formats, and obvious omissions.
2. **Engine:** import, parse, load, bounded runtime, and error log.
3. **Behavior:** each state in the playable contract is actually reached.
4. **Visual/audio:** the builder inspects representative captures at final framing and motion and fixes routine defects; audio is actually listened to in context by a human listener, not inferred from file presence, node paths, buses, waveforms, or automated metrics.
5. **Independent human/evaluator playtest:** someone who did not build the flow can understand the goal, complete every required onboarding transition, and close the loop without developer narration.

Do not let a high structural score hide a broken game. Treat unreachable success/failure, static-text-only onboarding for a non-obvious core action, unclear controls, a soft lock, or a nonfunctional restart as completion blockers.

For complete games and vertical slices, also treat missing production audio, generic beep/boop placeholders, an unrelated stock music track, broken loops, or unusable mix/settings as completion blockers unless the brief explicitly calls for silence. Use the audio acceptance and evidence requirements in [audio-vfx-fonts.md](audio-vfx-fonts.md).

## Forward-evaluation set for this skill

When changing this skill materially, test it on isolated projects representing at least:

- new 2D slice with provided sprites;
- new 2D slice requiring generated/edited sprites;
- complete local 2D fighting slice with fixed-tick replay/input/frame evidence;
- complete metroidvania slice with modeled and physically played gate/escape/save paths;
- complete idle/clicker slice with economy/offline/save evidence;
- complete quest-driven slice with duplicate-event and exactly-once reward evidence;
- new 3D slice using a ready-made asset pack;
- complete fixed-camera isometric game with an early rendered art gate, measured character/route readability, full onboarding state machine, density/composition matrix, and content-duration evidence;
- complete 2.5D game with an explicit spatial model, production-art dense/VFX/contact matrix, character motion recording, gameplay-HUD glanceability/iconography evidence, menu identity craft review, and independent Windows target-build UX/visual verdict;
- new 3D slice with a generated static prop and authored collision/wrapper;
- feature added to an existing convention-heavy project;
- constrained mobile/web build with performance and package-size budgets.
- approved UI-reference integration with native scene authorship and raw parity artifacts.

For each case record: brief, fixture/license, initial project hash, tools available, final project, validation commands, captures including proof watchback when applicable, audio listening notes, errors/warnings, human playability result, elapsed time, external generation cost/retries, and token/tool-call usage. Compare regressions on structure, completion, visual coherence, audio quality, performance, and cost; do not tune only to one demo.

Use the stable machine-readable rubric in `evals/rubric.json` and author evidence against `evals/evidence.schema.json`. Respect each gate's `acceptance_owner`: the builder supplies and fixes builder-owned routine evidence; a human or independent evaluation context supplies only gates explicitly assigned to it. The building agent must not award itself high independent/perceptual scores from intent, file presence, or its own screenshots, but it also must not defer ordinary QA to the user. Record the builder and reviewer contexts and keep raw findings, including defects. Every passing gate records a matching `reviewer.role` and concrete context. Gates with `artifact_requirements` also attach structured files under `artifacts`; paths resolve from `run_metadata.artifact_root`, which defaults to the evidence file's directory. A prose note that a movie, screenshot, or review existed cannot replace a missing/empty file.

Create or migrate the case evidence instead of hand-copying the current rubric. Missing gates and dimensions are added as visibly unresolved values while existing evidence is preserved:

```bash
python <skill-dir>/scripts/evidence_helper.py --rubric <skill-dir>/evals/rubric.json --case <case-id> --output <evidence.json> --capture-manifest-output <captures.json> --project-status-output <project-run-state.md> --art-direction-selection-output <art-direction.md> --review-output <independent-review.md> --menu-review-output <menu-review.md> --cross-surface-craft-review-output <cross-surface-review.md> --review-profile-reset-output <review-profile.md> --product-owner-slice-output <owner-slice.md> --hud-review-output <hud-review.md> --production-art-review-output <production-art-review.md> --motion-review-output <character-motion.md> --yandex-checklist-output <yandex-checklist.md>
python <skill-dir>/scripts/evidence_helper.py --rubric <skill-dir>/evals/rubric.json --case <case-id> --from-existing <old-evidence.json> --output <migrated-evidence.json>
```

The helper never turns generated placeholders into passing evidence. It labels unresolved gates with their acceptance owner so builder-owned work is not accidentally pushed into the independent review. Fill the generated files with real artifacts, clean/seeded provenance, and only the independent/human evidence actually required. Use `assets/yandex-release-checklist.template.md` as the PASS/FAIL/NOT TESTED gate sheet for a Yandex release.

```bash
python <skill-dir>/scripts/eval_scorecard.py --rubric <skill-dir>/evals/rubric.json --case <case-id> --evidence <evidence.json> --summary --json-output <scorecard.json>
```

The scorecard normalizes applicable weighted dimensions, reports each gate's acceptance owner, blocks publication certification on every failed/untested blocking gate, and applies rubric-defined dimension caps when missing evidence makes a high submitted score indefensible. It also reports `responsibility_status`, builder-owned unresolved gates, and pending external gates. Compare both `submitted_score_100` and adjusted `score_100`; a publication-blocked case may still be `ready_for_human_test` when only legitimate external evidence is absent, but optimistic submitted scores never certify publication. Keep fixture, brief, rubric, and evaluation protocol stable when comparing skill revisions.

## Completion evidence

At handoff, distinguish:

- checked automatically;
- observed and accepted by the builder in runtime/capture;
- confirmed by a human playtest;
- reviewed by an independent evaluation context;
- optional user preference feedback;
- not tested or dependent on unavailable hardware/tools.

Never convert “not tested” into “works” because the scene or script looks plausible.

Then emit exactly one successful responsibility status: `BUILDER_COMPLETE / READY_FOR_HUMAN_TEST` or `PUBLICATION_CERTIFIED`. If builder work remains, continue instead of ending with a list of actions for the user. Keep any external evidence boundary factual and concise; it is not the user's assigned checklist. If the user explicitly closed the project, emit only the non-success `PROJECT_CLOSED / USER_REJECTED` disposition and stop.
