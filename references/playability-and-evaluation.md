# Playability and Evaluation

Read this for a new game, a substantial vertical slice, or any task where the agent is expected to deliver a complete playable result. Startup without errors is not evidence that a game communicates a goal, closes its loop, or feels correct.

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

Keep the matrix proportional. A one-screen toy may need five states; a save/load feature needs persistence and corrupted/missing-data cases.

For a complete game, the boot/menu evidence also includes the exported app icon and primary menu mark at their actual display sizes. Have an independent reviewer describe what the mark depicts before receiving the intended explanation; a coherent palette or clean arrangement of primitives is not evidence of game-specific identity. Record the result with `assets/semantic-identity-review.template.md`.

## Prove onboarding through action

For a complete game or vertical slice with a non-obvious mechanic, onboarding must advance through an observable player action. Highlight or constrain the relevant target/control, wait for the player to perform the intended input, confirm the result, and then release the player into the normal loop. A paragraph, static hint, tutorial data field, localized string, or “How to play” page can support this sequence but cannot replace it.

Do not compress a multi-step core loop into one generic “interact” proof. Model onboarding as explicit states and transitions. For each brief-required verb or world consequence, record the target/cue, actual player input, immediate feedback, resulting gameplay/route state, failure-pressure policy, target visibility, and uncoached evidence. In the complete fixed-camera isometric case this ledger covers movement, pickup, context interaction, mechanism state change, traversal of the changed route, height/lift use, beacon/objective delivery, and restart/recovery. The player must cause every transition; narration, a scripted demonstration, or one final completion trace cannot stand in for the intermediate states. Use `assets/isometric-complete-review.template.md` for that canonical flow.

Test from the clean shipping profile with a person or independent evaluator who has not been coached on the mechanic. Evidence should show the prompt/state before the action, the actual input/state transition, feedback after success, and entry into the core loop. If the game's core action is genuinely self-evident and no tutorial is intended, document that decision and still verify first-action success without narration.

Do not let a pressure/failure timer undermine the teaching state. By default, freeze or substantially relax time pressure until the required onboarding action succeeds and its feedback is readable, then start or ramp normal pressure explicitly. Starting the shipping timer at scene entry is acceptable only when time pressure itself is the taught mechanic and an uncoached first-use test proves the player has enough time to understand, act, recover from one reasonable mistake, and enter the normal loop. A developer who already knows the controls is not evidence for this exception.

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

The runner does not inject keyboard, mouse, or controller input. Use a project test driver or an approved UI automation layer for input-dependent flows.

## Assign acceptance ownership without outsourcing routine QA

Use the `acceptance_owner` attached to an applicable rubric gate:

- **builder:** objective routine acceptance that the implementing agent must autonomously exercise, inspect, and fix before handoff. Deterministic contracts, target-build runs, recordings, logs, and builder observations are valid evidence. Examples include clean import, restart, production character motion, input routing, collision, and attachment following.
- **independent:** comprehension, semantic reading, or visual/UX judgment that explicitly needs a person or genuinely separate evaluation context that did not build the flow. The builder still performs its own QA first; independence is a second acceptance layer, not a substitute for it.
- **human:** irreducibly perceptual signoff explicitly named by the rubric, such as representative audio listening. Automation and builder triage prepare the evidence but cannot promote the gate.

Optional user preference feedback is outside these blocking ownership classes unless the brief explicitly elevates it into acceptance. Ask for it to refine taste—animation weight/personality, tone, pacing preference—not to discover a bind/T-pose, missing locomotion, broken attachment, clipped UI, or other routine production defect. When a separate evaluator is available, use that evaluation context for required independent gates rather than making the user execute a QA checklist.

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
- new 3D slice with a generated static prop and authored collision/wrapper;
- feature added to an existing convention-heavy project;
- constrained mobile/web build with performance and package-size budgets.
- approved UI-reference integration with native scene authorship and raw parity artifacts.

For each case record: brief, fixture/license, initial project hash, tools available, final project, validation commands, captures, audio listening notes, errors/warnings, human playability result, elapsed time, and token/tool-call usage. Compare regressions on structure, completion, visual coherence, audio quality, performance, and cost; do not tune only to one demo.

Use the stable machine-readable rubric in `evals/rubric.json` and author evidence against `evals/evidence.schema.json`. Respect each gate's `acceptance_owner`: the builder supplies and fixes builder-owned routine evidence; a human or independent evaluation context supplies only gates explicitly assigned to it. The building agent must not award itself high independent/perceptual scores from intent, file presence, or its own screenshots, but it also must not defer ordinary QA to the user. Record the builder and reviewer contexts and keep raw findings, including defects. Every blocking gate needs an artifact, command result, trace, capture review, or explicit rights record.

Create or migrate the case evidence instead of hand-copying the current rubric. Missing gates and dimensions are added as visibly unresolved values while existing evidence is preserved:

```bash
python <skill-dir>/scripts/evidence_helper.py --rubric <skill-dir>/evals/rubric.json --case <case-id> --output <evidence.json> --capture-manifest-output <captures.json> --review-output <independent-review.md> --yandex-checklist-output <yandex-checklist.md>
python <skill-dir>/scripts/evidence_helper.py --rubric <skill-dir>/evals/rubric.json --case <case-id> --from-existing <old-evidence.json> --output <migrated-evidence.json>
```

The helper never turns generated placeholders into passing evidence. It labels unresolved gates with their acceptance owner so builder-owned work is not accidentally pushed into the independent review. Fill the generated files with real artifacts, clean/seeded provenance, and only the independent/human evidence actually required. Use `assets/yandex-release-checklist.template.md` as the PASS/FAIL/NOT TESTED gate sheet for a Yandex release.

```bash
python <skill-dir>/scripts/eval_scorecard.py --rubric <skill-dir>/evals/rubric.json --case <case-id> --evidence <evidence.json> --summary --json-output <scorecard.json>
```

The scorecard normalizes applicable weighted dimensions, reports each gate's acceptance owner, blocks completion on every failed/untested blocking gate, and applies rubric-defined dimension caps when missing evidence makes a high submitted score indefensible. Compare both `submitted_score_100` and adjusted `score_100`; a blocked case with optimistic scores is not near-perfect evidence. Keep fixture, brief, rubric, and evaluation protocol stable when comparing skill revisions.

## Completion evidence

At handoff, distinguish:

- checked automatically;
- observed and accepted by the builder in runtime/capture;
- confirmed by a human playtest;
- reviewed by an independent evaluation context;
- optional user preference feedback;
- not tested or dependent on unavailable hardware/tools.

Never convert “not tested” into “works” because the scene or script looks plausible.
