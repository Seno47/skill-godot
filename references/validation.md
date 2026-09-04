# Core Validation

Read this before claiming any Godot task is complete. Validate in proportion to the requested change and report evidence, not confidence.

## Core questions

1. **Structure:** Are scenes, resources, scripts, ownership, references, and imports valid and maintainable?
2. **Engine:** Can the project's actual Godot version import and parse the changed project?
3. **Behavior:** Does the requested flow work in play, including relevant edge states?

For visual work also read [visual-validation.md](visual-validation.md). For a new or materially changed game-wide visual direction, first apply [visual-style-selection.md](visual-style-selection.md) and preserve its pre-bulk decision evidence. For external/generated assets read [asset-validation.md](asset-validation.md). Performance, memory/loading, and export-size references contain their own measurement gates.

## Static and engine checks

Run the bundled checker from this skill:

```bash
python <skill-dir>/scripts/verify_godot_project.py --project <project-dir>
python <skill-dir>/scripts/verify_godot_project.py --project <project-dir> --engine
python <skill-dir>/scripts/verify_godot_project.py --project <project-dir> --engine --run
python <skill-dir>/scripts/scene_graph_audit.py --project <project-dir> --summary --json-output <report.json>
```

Use `--scene res://path/to/scene.tscn` for a specific scene and `--godot <editor-binary>` when discovery fails. Treat missing paths and parse/import/runtime errors as blockers. Review script-built-node warnings contextually: tooling/procedural systems may be valid; hidden authored levels/UI are not.

The scene-graph audit checks serialized hierarchy, parents, resource IDs/paths, signal endpoints, selected NodePaths, and common missing visual/collision properties. Its warnings about runtime-assigned values and methods require judgment. It cannot see nodes that were never saved, imported-scene internals, or runtime composition; engine import and play remain authoritative. A node override, NodePath, or connection below a locally declared `[editable path]` `PackedScene` instance is recorded as `editable_packed_scene_internal_references`, not an unconditional missing-parent error: the local instance boundary is statically provable, but the internal path is not. Require a clean engine load/import of the exact wrapper before accepting that limitation. Missing parents without the editable PackedScene boundary and invalid editable targets remain blocking.

For C# projects, build with the project-compatible Godot/.NET workflow. Run existing project tests rather than replacing them with the generic checker.

When tooling generates or rewrites a complete scene, verify the generated-scene round trip from [scene-architecture.md](scene-architecture.md): compare intended persistent node paths/count before packing, after `PackedScene` instantiation, and after disk reload; stop ownership recursion at instantiated/imported scene roots. A clean compiler/import cannot reveal a child silently dropped before the saved file existed.

## Prefer engine-owned verification over desktop automation

Default to the Godot CLI/editor command line, project-owned deterministic input drivers, reusable probes, and `scripts/godot_capture.py`. Do not launch Computer Use or other desktop GUI automation merely to click through a game, take a screenshot, or reproduce input that the project/engine can drive itself.

Use desktop Computer Use only when the user explicitly opts in, or when a required native OS behavior cannot be observed through Godot/CLI—such as the actual Windows taskbar icon, installer/shell integration, exclusive-fullscreen transition, native file picker, per-monitor DPI, or another external desktop surface. Scope and disclose that exception. GUI automation performed by the builder remains builder evidence; it does not become an independent playtest or human perceptual signoff.

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

## Prove production character motion before release

When a production character is expected to move, instantiate `assets/production-character-motion.template.md` and treat it as builder-owned acceptance rather than an optional human checklist. The project-specific deterministic contract should prove:

- required idle, locomotion, and brief-required context clips/states resolve on the production visual owner;
- ordinary idle/locomotion are not the imported bind/rest/T-pose and sampled production pose features vary over time;
- real movement/interaction paths dispatch the expected state instead of a test-only direct animation call;
- retarget/root policy, source-mannequin visibility, and action reset/interruption are intentional;
- required held props/effects/sockets follow the animated bone or authored marker through representative poses.

For skeletal 3D, sample several stable non-root bones or equivalent pose features because in-place motion may keep the root still. For 2D, sample animation/frame progression, pivots, and attachment markers. Choose project-owned tolerances that distinguish real motion from numerical jitter; do not universalize one bone list, arm angle, or delta across rigs.

Then capture and inspect raw target-build motion at the actual gameplay camera: idle, locomotion, and required context actions, normally for several seconds at a fixed frame rate. Preserve a contact sheet when it helps compare poses, but do not replace the recording with stills. The builder must reject a frozen character, bind/T-pose leakage, missing state dispatch, duplicate/source mannequin, loop/contact failure, or detached attachment before asking the user for preference feedback. Human comments about motion style remain optional unless the brief explicitly makes them an acceptance requirement.

For a freely orbiting third-person controller, copy/adapt `assets/godot-tests/third_person_controller_probe.gd` into a flat deterministic fixture that instances the real player and camera rig. The fixture must expose the actual production input actions and nodes rather than a second test-only movement implementation. Exercise camera-relative forward movement after 45° and 90° yaw plus the supported right-stick axes, zoom, and recenter:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --script res://tests/third_person_controller_probe.gd --frames 600 --user-arg scene=res://tests/third_person_controller_fixture.tscn --user-arg player=Player --user-arg yaw_pivot=Player/CameraRig/Yaw --user-arg pitch_pivot=Player/CameraRig/Yaw/Pitch --user-arg camera=Player/CameraRig/Yaw/Pitch/SpringArm3D/Camera3D --user-arg spring_arm=Player/CameraRig/Yaw/Pitch/SpringArm3D --user-arg move_forward=move_forward --user-arg look_right=look_right --user-arg look_up=look_up --user-arg zoom_out=zoom_out --user-arg recenter=camera_recenter --user-arg pause_action=pause --user-arg "yaw_degrees=45;90" --summary --json-output reports/third-person-controller.json
```

The generic controller probe proves direction, observable control response, and optional camera-collision shortening/restoration; it deliberately does **not** prove player visibility. Run it windowed when supplying `pause_action`, because a headless display may not enter `MOUSE_MODE_CAPTURED`; a headless run may omit that argument and report the capture check as skipped. Mark unsupported or deliberately excluded controls in the brief before implementation; silently omitting an axis does not pass.

The flat controller fixture does not prove that the production HUD allows captured mouse motion to reach the camera. Copy/adapt `assets/godot-tests/third_person_hud_mouse_probe.gd` into a fixture that instances the production controller/camera and the real visible full-screen gameplay HUD. The probe injects `InputEventMouseMotion` through `Input.parse_input_event()` at the viewport center and requires both yaw and pitch; do not replace this with a direct method call:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/third_person_hud_mouse_probe.gd --frames 180 --user-arg scene=res://tests/third_person_production_hud_fixture.tscn --user-arg yaw_pivot=Player/CameraRig/Yaw --user-arg pitch_pivot=Player/CameraRig/Yaw/Pitch --user-arg hud_root=HUD/FullScreenRoot --user-arg mouse_delta=30:20 --summary --json-output reports/third-person-hud-mouse.json
```

The fixture must use the production HUD hierarchy and mouse filters, not an empty substitute. If the event is consumed before `_unhandled_input()`, fix routing deliberately: passive HUD can ignore/propagate motion, or captured look can run at an earlier suitable input stage with explicit gameplay/modal gating. A passing synthetic event catches routing regressions but cannot judge sensitivity, acceleration, comfort, or native event forwarding; add a hands-on target-build note for those.

For third-person visibility/occlusion, copy/adapt `assets/godot-tests/third_person_visibility_probe.gd` into a fixture that instances the production occlusion system. Its small adapter surface changes deterministic authored cases but the probe itself performs multi-height iterative physics collection. Include at least a single blocker, two simultaneous blockers, an open-hole negative case, a silhouette fallback case when used, and a final clear/restoration case:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/third_person_visibility_probe.gd --frames 360 --user-arg scene=res://tests/third_person_visibility_fixture.tscn --user-arg adapter=OcclusionProbeAdapter --user-arg desired_camera=DesiredCamera --user-arg "sample_points=Player/VisibilityPoints/Feet;Player/VisibilityPoints/Torso;Player/VisibilityPoints/Head" --user-arg "exclude_nodes=Player" --user-arg "cases=single:1:cutaway;multi:2:cutaway;fallback:1:silhouette;open_hole:0:clear;restored:0:clear" --user-arg collision_mask=8 --summary --json-output reports/third-person-visibility.json
```

The adapter must call the real production state transitions and expose `probe_set_case(name)`, `probe_is_occluder_resolved(collider)`, `probe_active_cutaway_count()`, `probe_is_silhouette_visible()`, `probe_restoration_issues()`, and `probe_shell_issues(case_name)`. Do not implement a second fake occlusion algorithm solely for the fixture. A PASS proves the declared ray/cutaway invariants and adapter-reported shell checks, not rendered quality or full render/collision-shell fidelity. Complete `assets/third-person-3d-review.template.md` with raw target-build blocked/clear captures from several locations, collision/debug overlay for the open-hole case, and restoration evidence.

For isometric/2.5D coordinate work, copy/adapt `assets/godot-tests/isometric_projection_probe.gd` and point it at the project-owned projection resource or adapter. Include origin, negative, positive, and elevated cells:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/isometric_projection_probe.gd --frames 120 --user-arg projection=res://world/isometric_projection.tres --user-arg "cells=0:0:0;1:0:0;0:1:0;-2:3:0;4:-1:2" --summary --json-output reports/isometric-projection.json
```

For grid navigation and height links, copy/adapt `assets/godot-tests/isometric_navigation_probe.gd` into a fixture whose adapter exposes `find_cell_path(start, goal)` and optionally `is_cell_walkable(cell)`:

```bash
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode run --headless --script res://tests/isometric_navigation_probe.gd --frames 180 --user-arg scene=res://tests/isometric_navigation_fixture.tscn --user-arg adapter=NavigationAdapter --user-arg "routes=0:0:0>4:2:0;4:2:0>5:2:1" --user-arg require_height_change=true --summary --json-output reports/isometric-navigation.json
```

These probes establish logical round-trips and path invariants. They do not prove rendered depth, cursor behavior near cell boundaries, roof/wall occlusion, or camera/input synchronization. Exercise those in a deterministic rendered fixture and the target build as required by [isometric-and-2-5d.md](isometric-and-2-5d.md).

For fixed-camera character readability, render a normal raw gameplay screenshot and a hero-only mask at the exact same camera, frame, resolution, animation pose, and world state. Declare thresholds in the project review before evaluating the final captures, then measure at least one mean separation metric, one local-edge separation metric, and one screen-space size metric:

```bash
python <skill-dir>/scripts/isometric_readability_audit.py --screenshot reports/isometric-dense.png --mask reports/isometric-dense-hero-mask.png --require-thresholds --min-mean-luminance-delta <project-value> --min-edge-luminance-delta <project-value> --min-bbox-height-ratio <project-value> --summary --json-output reports/isometric-dense-readability.json
```

Repeat for quiet/default, dense mechanism/decor, height/lift, and route-changing/occlusion stress states. A mask generated from a different frame, a diagnostic-only run without thresholds, or one convenient capture cannot pass. Complete `assets/isometric-complete-review.template.md`; raw independent review remains authoritative for silhouette meaning, route composition, state readability, and sparse/default-looking art.

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
python <skill-dir>/scripts/godot_capture.py --project <project-dir> --mode capture --scene res://path/to/scene.tscn --proof-seconds 15 --fixed-fps 30 --output <delivery-proof.avi> --summary --json-output <delivery-proof.json>
python <skill-dir>/scripts/mjpeg_avi_watchback.py --input <delivery-proof.avi> --output-dir <watchback-dir> --expected-duration-seconds 15 --sample-fps 4 --require-temporal-change --summary
```

`godot_capture.py` bounds execution and gathers evidence but does not synthesize player input. For complete games and vertical slices also apply [playability-and-evaluation.md](playability-and-evaluation.md).
For `run` and `capture`, it performs a Godot version check and headless import preflight before the evaluated command. Use `--skip-import` only when the identical project state has already passed import and avoiding the repeated phase is intentional.

For Godot MJPEG AVI, `mjpeg_avi_watchback.py` is the built-in no-ffmpeg inspection path. A PASS proves that headers/count/duration agree, every JPEG frame decodes, endpoints are represented, and the reported sheets exist. The builder must still inspect the sheets and, when available, normal-speed playback. Use `--all-frames` with an explicit raised safety bound when a playback-less environment needs every visual frame exposed; do not infer smooth motion or audio quality from contact sheets.

## Scene-first audit

- Persistent authored objects exist in `.tscn` scenes.
- Repeated concepts are instances, not copied trees.
- Shared definitions/styling are resources where useful.
- Ordinary levels, actors, and UI are not constructed wholesale by runtime scripts.
- Runtime generation has a real procedural/transient/streaming/performance reason.
- Editor-generated nodes have correct ownership and saved output.
- Generated scenes prove in-memory -> packed instance -> disk-reloaded node/path parity without crossing ownership into imported/instanced internals.
- Imported assets are customized through wrappers/inheritance/resources, not cache edits.
- Complete games and production slices have a builder-owned `production-art-state-review` covering quiet, normal gameplay, dense interaction, peak VFX/contact, and result states; scene serialization cannot promote blockout/debug geometry to production art.
- Complete games and production slices have a gameplay-HUD glanceability inventory and independent raw review across quiet/normal/dense/VFX states; frequent telemetry is not left as redundant distant text merely because panels fit the screen.
- Complete-game menus have a separate independent craft review of runtime wordmark/typography, copy necessity, background, hierarchy, and interaction state in addition to semantic icon/mark recognition.
- Production characters expected to move have a builder-owned motion contract covering required states, bind/rest/T-pose rejection, real dispatch, target-build motion, and attachments.
- Isometric/2.5D work has one documented authoritative spatial model, projection/picking owner, pivot/sort convention, navigation contract, and multi-level occlusion strategy.
- Complete fixed-camera isometric work has an independently approved gameplay-size art slice before bulk authoring, a same-frame character-readability matrix, a player-performed onboarding transition ledger, a density/composition matrix, and a content-duration contract matching the claimed scope.
- Complete fixed/high-angle 3D district work has a builder-owned visible-boundary ledger, district/zone/view-corridor plan, modular-variation/repetition audit, target-build state matrix, normal-speed camera evidence, a zero-error resolved dependency-closure provenance audit linked to every evidence contract, zero-error local `environment_integrity_audit.py`, zero-error schema-v2 whole-map `environment_coverage_audit.py`, and zero-error schema-v3 `visible_first_boundary_audit.py` backed by a complete shipping-camera survey, semantic zone/fallback/adjacency results, bidirectional exporter-owned visible-solid/collider overlap and hero raster, explicit evidence-backed non-solid VFX classifications, exporter-owned production-capsule reachability against a nonempty unsafe fringe, collision-intent assembly bindings, global visual/collision root parity, collider/render contact-distance parity, edge/corner/concavity/seam/opening approaches, solid-volume non-entry/non-climb trials, visible-limiter retention/replacement continuity, production occluder aliases and topmost surface/object contacts. If streets exist, the exact copied exporter first passes its engine-backed `PlaneMesh`/`BoxMesh` fixture under the project's Godot version; it then has zero-error schema-v6 `streetscape_semantics_audit.py`, a complete road-junction shipping-camera survey, lane/junction/sidewalk/crosswalk topology, resolved marking mesh endpoints, typed road-end policy and before/at/between/beyond topmost-surface samples, no surrogate road-end planes or markings beneath caps, class-specific vegetation/furniture placement, full building/vehicle/furniture forbidden-surface footprints, source-bound facade/roof/openings/trim roles, two opposed diagonal shipping-camera views, maximum-openings view selection, MSAA-normalized mutually exclusive role masks and flood-fill/separation metrics, approach-aware furniture, vertex-resolved support mounts, incident closures and a hero-radius visible-boundary reachability raster.
- A high-angle boundary/road report fails closed when the adapter supplies reachability cells instead of the exporter, the actual production capsule reaches outside, a visible limiter is deleted without mapped replacement proof, a vehicle closure removes or covers the continuing road, a facade closure leaves road/markings beneath the facade, any road-end overlay mesh is present, vegetation or curb furniture permits protected road/pedestrian surfaces, or an exporter logs failure and still writes evidence or emits `[PASS]`.

## Completion gate

Do not claim completion with engine errors, missing resources, broken inheritance, generated-scene node loss or ownership-driven resource bloat, unreachable core flow, a new complete game/slice whose visual direction lacks a durable user-fixed/constraint-determined/compared selection rationale and raw pre-bulk gameplay-size anchor/composition, a production character frozen in bind/rest/T-pose or missing required idle/locomotion/context motion, test-only animation dispatch, a visible source mannequin, detached animated attachments, missing raw normal-speed motion artifacts, relevant collision/focus/camera failure, camera-relative movement or capture recovery unproved where applicable, production-HUD mouse routing proved only by input maps/direct calls, camera collision mistaken for player-visibility proof, unresolved multi-occluders, false camera proxies over open holes, incomplete cutaway restoration, high-structure cutaway that leaves the route veiled, unsafe or partial first-use teaching, gameplay sightlines blocked by HUD/emissive geometry, complete-game gameplay HUD lacking an information inventory and independent glanceability review, frequent telemetry that still requires reading duplicated labels across distant zones, objective/prompt competition, ambiguous/default/mismatched iconography, color-only state encoding, localization-dependent paragraph-like HUD, complete-game audio lacking human listening signoff, a complete-game app/menu mark lacking semantic final-size review, a generic/default-font title/tagline/button-stack menu lacking independent craft review, production art reviewed only in a quiet frame, debug-looking VFX or primitive/mismatched assets in dense gameplay, fixed-camera isometric art scaled before a gameplay-size slice passes, missing same-frame character/route readability evidence, sparse/default-looking composition, fixed/high-angle 3D districts bounded mainly by repeated fence/containers/cloned backdrop mass, contactable invisible walls without a visible cause, view corridors ending in void/fog/clones, meaningless prop scatter, unbudgeted visible modular runs, random architectural hue cycling/checkerboard adjacency, flat flood-fill overrides that erase texture/material structure, palette roles unproved in same-zone and cross-zone target-build frames under exact gameplay lighting, collision/boundary coverage used to excuse visible transformed prop penetrations or fused contacts, origin-only placement used instead of full support-footprint surface ownership, broad floor collision used instead of render-mesh seam coverage, one permissive whole-map surface region, uncovered shipping-camera survey cells, unexplained zone adjacency/fallback patchwork, enabled static colliders without visible render mass, asymmetric disabled/hidden variants, synthetic-only or unmapped production occluders, allowed material labels used to excuse impossible topmost surface/object fusion, overhead signs/wires/poles/towers lacking vertical-clearance proof, roads whose lanes/junctions/approaches/sidewalks/crosswalks are disconnected or physically implausible, adapter-declared marking distances unbound from resolved marking meshes, common RoadNetwork meshes or sidewalk slabs used as physical caps, off-map roads without road/sidewalk/curb/marking continuation, buildings intersecting continuation corridors, building or furniture footprints in forbidden street surfaces, source openings/trim omitted from target-build role masks, default/unpainted or flood-filled camera-visible facade/roof/openings/trim, mounted supports proved only by scalar gap instead of support-vertex/mount-triangle contact, hydrants/signals/signs/poles outside their curb/junction/approach/orientation budgets, incident props without graph closures/alternate routes, visible cars/props that leave a reachable pocket against a safety-only wall, an incomplete shipping-camera road-junction survey, a resolved target-scene report identified only by its root `.tscn` hash, a missing/stale recursive or runtime dependency entry, an unhashed evidence exporter/export preset, or high-angle camera motion lacking safe-frame/lead/zoom/volume/occlusion restoration proof, a duration/content claim unsupported by authored depth and uncoached playtime, paid generation retried without checking its durable provider job record, unsaved editor output, accidental placeholders in a claimed-finished state, a missing clean-profile proof for persistent games, a scorecard PASS whose reviewer provenance/concrete artifact files fail validation, or required conditional validation not performed.

At handoff, name commands/tests run, states exercised, storage/profile provenance for captured progress, remaining limitations, and anything not verified. Then apply the responsibility status from [playability-and-evaluation.md](playability-and-evaluation.md): continue if builder-owned work or an unfixed review defect remains; otherwise say `BUILDER_COMPLETE / READY_FOR_HUMAN_TEST`, or `PUBLICATION_CERTIFIED` only after external gates pass. A missing human/provider observation stays an evidence boundary, not a user to-do list.

Official reference: [Godot command-line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)
