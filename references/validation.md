# Core Validation

Read this before claiming any Godot task is complete. Validate in proportion to the requested change and report evidence, not confidence.

## Core questions

1. **Structure:** Are scenes, resources, scripts, ownership, references, and imports valid and maintainable?
2. **Engine:** Can the project's actual Godot version import and parse the changed project?
3. **Behavior:** Does the requested flow work in play, including relevant edge states?

For visual work also read [visual-validation.md](visual-validation.md). For external/generated assets read [asset-validation.md](asset-validation.md). Performance, memory/loading, and export-size references contain their own measurement gates.

## Static and engine checks

Run the bundled checker from this skill:

```bash
python <skill-dir>/scripts/verify_godot_project.py --project <project-dir>
python <skill-dir>/scripts/verify_godot_project.py --project <project-dir> --engine
python <skill-dir>/scripts/verify_godot_project.py --project <project-dir> --engine --run
python <skill-dir>/scripts/scene_graph_audit.py --project <project-dir> --summary --json-output <report.json>
```

Use `--scene res://path/to/scene.tscn` for a specific scene and `--godot <editor-binary>` when discovery fails. Treat missing paths and parse/import/runtime errors as blockers. Review script-built-node warnings contextually: tooling/procedural systems may be valid; hidden authored levels/UI are not.

The scene-graph audit checks serialized hierarchy, parents, resource IDs/paths, signal endpoints, selected NodePaths, and common missing visual/collision properties. Its warnings about runtime-assigned values and methods require judgment. It cannot see nodes that were never saved, imported-scene internals, or runtime composition; engine import and play remain authoritative.

For C# projects, build with the project-compatible Godot/.NET workflow. Run existing project tests rather than replacing them with the generic checker.

## Import and runtime

Run editor import after changing scenes, resources, source assets, fonts, shaders, addons, or import settings. Do not edit/commit `.godot` cache unless the repository intentionally does so.

Classify bounded-run shutdown output instead of treating every line alike:

- non-zero exit, timeout, parse/script/resource failures, or errors reproduced during the exercised flow are blocking;
- `ObjectDB`/resource-leak or orphan diagnostics that appear only when `--quit-after` forcibly tears down an otherwise clean deterministic run are retained as `forced_quit_diagnostic_lines`, but are not blocking by themselves;
- the same leak on a normal project-owned exit, a growing/repeated leak, or a diagnostic accompanied by broken behavior remains a defect to investigate.

Do not delete raw logs or add broad ignore patterns to obtain a clean result. Corroborate a forced-quit classification with clean import plus deterministic scene/tests, and record the limitation at handoff.

Exercise the affected flow, not only startup:

- input, movement, interaction, state transitions, restart, and scene changes;
- collision/navigation and save/persistence cases touched;
- UI focus/device navigation and animation/effect timing touched;
- cold start and main-scene behavior for new projects.

For input-modality UI, run pointer/touch and keyboard/gamepad entry as distinct scenarios. Record which control owns focus after opening, whether focus art is visible, and whether a pointer-open selectable value falsely appears selected. For every required touch-scroll surface with real overflow, prove position movement from an actual touch/drag event; a `ScrollContainer` node or scrollbar override is only structural evidence.

Copy/adapt the reusable probe into a project-owned test path and point it at a deterministic scene where the target `ScrollContainer` is visible and overflowing:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/touch_scroll_probe.gd --frames 180 --user-arg scene=res://tests/settings_scroll_fixture.tscn --user-arg target=SettingsDialog/BodyScroll --user-arg viewport=336x629 --summary --json-output reports/touch-scroll.json
```

The template is `assets/godot-tests/touch_scroll_probe.gd`. It asserts a vertical scroll delta after `InputEventScreenTouch` plus `InputEventScreenDrag`; it does not prove that a browser/device forwards physical gestures correctly, so keep one target-build interaction check. Exclude temporary fixtures/probes from the shipping export unless the project intentionally maintains a test suite outside reachable release dependencies.

For localized compound/icon-only buttons, copy/adapt `assets/godot-tests/button_composition_probe.gd` into a deterministic project fixture that instances the real scene-authored widget without navigation side effects. The probe loops representative locales and viewport sizes, asserts visual-group versus button center, and feeds a full pointer press/release through `Input.parse_input_event()` to require `pressed`:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/button_composition_probe.gd --frames 300 --user-arg scene=res://tests/button_composition_fixture.tscn --user-arg compound_button=PlayButton --user-arg compound_visual=PlayButton/Center/Row --user-arg icon_button=SettingsButton --user-arg icon_visual=SettingsButton/Center/Icon --user-arg click_buttons=PlayButton,SettingsButton --user-arg locales=ru,en --user-arg viewports=336x629,1280x720 --summary --json-output reports/button-composition.json
```

Use every canonical viewport in the project's final layout test even if the reusable probe command is split into several bounded runs. A headless synthetic click proves the Godot input path and catches premature focus cleanup; still repeat the action in the release-like Web build because browser event forwarding and overlays can differ.

For isometric/2.5D coordinate work, copy/adapt `assets/godot-tests/isometric_projection_probe.gd` and point it at the project-owned projection resource or adapter. Include origin, negative, positive, and elevated cells:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/isometric_projection_probe.gd --frames 120 --user-arg projection=res://world/isometric_projection.tres --user-arg "cells=0:0:0;1:0:0;0:1:0;-2:3:0;4:-1:2" --summary --json-output reports/isometric-projection.json
```

For grid navigation and height links, copy/adapt `assets/godot-tests/isometric_navigation_probe.gd` into a fixture whose adapter exposes `find_cell_path(start, goal)` and optionally `is_cell_walkable(cell)`:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/isometric_navigation_probe.gd --frames 180 --user-arg scene=res://tests/isometric_navigation_fixture.tscn --user-arg adapter=NavigationAdapter --user-arg "routes=0:0:0>4:2:0;4:2:0>5:2:1" --user-arg require_height_change=true --summary --json-output reports/isometric-navigation.json
```

These probes establish logical round-trips and path invariants. They do not prove rendered depth, cursor behavior near cell boundaries, roof/wall occlusion, or camera/input synchronization. Exercise those in a deterministic rendered fixture and the target build as required by [isometric-and-2-5d.md](isometric-and-2-5d.md).

## Separate shipping defaults from QA state

For games with persistence, perform two explicitly labeled runs:

1. **Clean shipping profile:** use a fresh browser/profile/origin or clear the relevant `localStorage`, IndexedDB, cookies/service-worker state, and Godot `user://` data as applicable. Capture the first boot, default unlock/progress/settings values, first-use onboarding, and first meaningful action.
2. **Seeded QA profile:** load only the progress/state needed to reach later levels, records, unlocks, purchases, failure modes, or other deep states. Record how it was seeded and keep it separate from release defaults.

Do not reuse one mutable browser profile as proof of both states. A screenshot with completed levels or records must state whether the state came from the shipping default, previous manual play, a deterministic fixture, cloud data, or QA seeding. Before packaging, inspect the exported project/config/data for test seeds and repeat the clean-profile run against the release-like build. Browser storage remaining on the developer machine is not baked into the archive, but an unlabeled dirty-profile capture is misleading evidence.

For complete browser/mobile work, instantiate `assets/capture-manifest.template.json` and fill the build ID, storage-reset method, profile provenance, viewport/state entry, artifact path, console result, and reviewer. This is the shared handoff between the builder and independent reviewer; do not coordinate the matrix only through chat narration.

Use a bounded automated run. If actions are required, use suitable UI control, a project test harness, or a temporary deterministic debug entry point; remove test-only shortcuts afterward.

For a reproducible run report or rendered capture use:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --scene res://path/to/test_scene.tscn --frames 300 --summary --json-output <report.json>
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode capture --scene res://path/to/scene.tscn --frames 300 --output <capture.avi> --summary --json-output <report.json>
```

`godot_capture.py` bounds execution and gathers evidence but does not synthesize player input. For complete games and vertical slices also apply [playability-and-evaluation.md](playability-and-evaluation.md).
For `run` and `capture`, it performs a Godot version check and headless import preflight before the evaluated command. Use `--skip-import` only when the identical project state has already passed import and avoiding the repeated phase is intentional.

## Scene-first audit

- Persistent authored objects exist in `.tscn` scenes.
- Repeated concepts are instances, not copied trees.
- Shared definitions/styling are resources where useful.
- Ordinary levels, actors, and UI are not constructed wholesale by runtime scripts.
- Runtime generation has a real procedural/transient/streaming/performance reason.
- Editor-generated nodes have correct ownership and saved output.
- Imported assets are customized through wrappers/inheritance/resources, not cache edits.
- Isometric/2.5D work has one documented authoritative spatial model, projection/picking owner, pivot/sort convention, navigation contract, and multi-level occlusion strategy.

## Completion gate

Do not claim completion with engine errors, missing resources, broken inheritance, unreachable core flow, relevant collision/focus/camera failure, unsaved editor output, accidental placeholders in a claimed-finished state, a missing clean-profile proof for persistent games, or required conditional validation not performed.

At handoff, name commands/tests run, states exercised, storage/profile provenance for captured progress, remaining limitations, and anything not verified.

Official reference: [Godot command-line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)
