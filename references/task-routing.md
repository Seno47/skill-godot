# Task Routing

Core construction:

- Open-ended brief or new slice: [references/brief-and-genre.md](brief-and-genre.md)
- Creating/restructuring scenes: [references/scene-architecture.md](scene-architecture.md)
- 2D world/gameplay: [references/production-2d.md](production-2d.md)
- 3D world/gameplay: [references/production-3d.md](production-3d.md)
- Isometric, dimetric, orthographic, or mixed 2D/3D world/gameplay: [references/isometric-and-2-5d.md](isometric-and-2-5d.md), plus the 2D or 3D guide for the selected primary architecture
- Fixed/high-angle 3D district, arena, settlement, urban route, extraction map, action-camera volume/rail, or visible-repetition problem: [references/high-angle-3d-districts.md](high-angle-3d-districts.md), plus the 3D, visual-validation, and applicable genre guides
- Dense 3D prop intersections, full-footprint/topmost-surface ownership, ground patchwork/seams, whole-map shipping-camera survey, invisible static blockers, production occluder aliases, overhead clearance, or collision-PASS/visual-FAIL problems: [references/3d-environment-integrity.md](3d-environment-integrity.md)
- High-angle roads, lane/junction/sidewalk/crosswalk topology, marking endpoints, road terminations, building mass in corridors, incomplete facade/roof/openings/trim roles, hydrant/signal/sign/pole placement, floating supports, incident road closures, or reachable pockets behind visible boundary props: [references/road-and-streetscape-semantics.md](road-and-streetscape-semantics.md), plus the district and environment-integrity guides
- UI/HUD/menus: [references/ui.md](ui.md)
- New UI composition or repeated template-like output: [ui-design-workflow.md](ui-design-workflow.md), then implement and compare the rendered anchor
- Gameplay HUDs, contextual prompts, notifications, or diegetic/world-space UI: [references/game-ui-patterns.md](game-ui-patterns.md), plus the base UI guide
- Animation, motion design, click response, loops, automation, travel/turning, object transfer/contact, character/vehicle/mechanical/UI motion, or unnatural tweening: [references/motion-and-animation.md](motion-and-animation.md), plus the relevant dimension and genre guide
- Approved screenshot/mockup-to-Godot parity work: [references/ui-reference-integration.md](ui-reference-integration.md), plus the base UI and visual-validation guides
- Traditional/platform fighting or frame-defined buffered combat: [references/genre-fighting.md](genre-fighting.md)
- Ability-gated interconnected exploration/metroidvania: [references/genre-metroidvania.md](genre-metroidvania.md)
- Idle, clicker, incremental, automation, or prestige economies: [references/genre-idle-clicker.md](genre-idle-clicker.md)
- Quests, missions, branching objectives, or persistent event-driven progression: [references/quest-and-progression.md](quest-and-progression.md)
- Persistent progression, XP/levels, upgrades/builds, rewards, resources/economies, difficulty curves, roguelite meta, strategy/survival balance, or monetized acceleration: [references/progression-and-balance.md](progression-and-balance.md), plus the relevant genre guide
- Difficulty curves, encounter/chapter pacing, tension/intensity, skill mastery, peaks and recovery, adaptive difficulty/assists, matchmaking bands, or genre-specific challenge: [references/difficulty-and-pacing.md](difficulty-and-pacing.md), plus the relevant genre and progression guides
- Save files, migrations, corruption/interruption recovery, cloud/device conflicts, or exactly-once durable state: [references/save-data-integrity.md](save-data-integrity.md)
- Procedural maps, encounters, loot, quests, seeds, solvability, generation budgets, or replayable content: [references/procedural-generation.md](procedural-generation.md)
- Enemies, NPCs, perception, behavior/state logic, navigation, crowds, telegraphs, off-screen simulation, or repeated stuck-side recovery: [references/game-ai-and-navigation.md](game-ai-and-navigation.md)
- Keyboard/mouse, gamepad, touch, remapping, hot-plug, glyph modality, local-player ownership, focus recovery, or accessibility behavior: [references/input-and-accessibility.md](input-and-accessibility.md)
- RTS, tactics, management, colony, automation, economy, job/command queues, time controls, or mass simulation: [references/genre-strategy-simulation.md](genre-strategy-simulation.md)
- Vehicles, racing, handling, checkpoints/laps, surfaces, high-speed camera, or recovery: [references/genre-vehicles-racing.md](genre-vehicles-racing.md)
- Shooter/action combat, aim, weapons, projectiles, hit/damage authority, cooldowns, or dense combat: [references/genre-shooter-action.md](genre-shooter-action.md)
- Dialogue, branching narrative, cutscenes, subtitles/captions, skip/interruption, or gameplay handoff: [references/narrative-dialogue-cinematics.md](narrative-dialogue-cinematics.md)
- Online/networked multiplayer, client/server authority, replication, prediction/rollback, impairment, reconnect, dedicated server, or Web networking: [references/multiplayer-networking.md](multiplayer-networking.md)
- Extraction, raid/stash boundaries, loot/loss/insurance, settlement, risk routes, or recovery: [references/genre-extraction.md](genre-extraction.md), plus the multiplayer guide when online
- MMO, persistent online worlds, zones/shards, identity/persistence services, interest management, load/soak, observability, restore, deployment, moderation, or honest production-slice scope: [references/mmo-and-online-services.md](mmo-and-online-services.md), plus the multiplayer and progression guides
- Multiple locales, plurals, fonts/scripts, runtime switching, subtitles, or global storefront copy: [references/localization-and-globalization.md](localization-and-globalization.md)
- Replay, ghosts, spectators, input/state recording, playback compatibility, or determinism claims: [references/replay-and-determinism.md](replay-and-determinism.md)
- In-game editors, builders, level/character tools, runtime creation, undo/redo, or creator export: [references/runtime-authoring-tools.md](runtime-authoring-tools.md)
- Complete game/vertical slice or autonomous build: [references/playability-and-evaluation.md](playability-and-evaluation.md) and [references/audio-vfx-fonts.md](audio-vfx-fonts.md)
- Cross-surface production craft, blind action/icon review, optical asset integration, exact review-profile reset, product-owner slice approval, or explicit project closure: [references/production-craft-and-product-approval.md](production-craft-and-product-approval.md), plus the UI, visual-validation, and playability guides
- Live editor automation, bridge, or MCP: [references/editor-bridge-mcp.md](editor-bridge-mcp.md)

Assets and presentation:

- Visual-style selection for a new/open brief, materially different art routes, or style-family production constraints: [references/visual-style-selection.md](visual-style-selection.md)
- Art direction/coherence: [references/assets-and-art-direction.md](assets-and-art-direction.md)
- Search, provenance, licensing, downloads: [references/asset-sourcing.md](asset-sourcing.md)
- Concrete source selection for 2D, 3D, UI, audio, fonts, shaders, or animation assets: [references/asset-source-catalog.md](asset-source-catalog.md), plus the sourcing guide
- Choosing a community addon/template/framework/theme/shader or interpreting the reviewed source catalogue: [references/evaluated-ecosystem.md](evaluated-ecosystem.md)
- Generation/editing: [references/asset-generation.md](asset-generation.md)
- Import/adaptation/wrapper scenes: [references/asset-integration.md](asset-integration.md)
- Audio, VFX, shaders, fonts: [references/audio-vfx-fonts.md](audio-vfx-fonts.md)

Optimization and release:

- FPS, CPU/GPU/physics bottlenecks or performance budgets: [references/performance-and-profiling.md](performance-and-profiling.md)
- RAM/VRAM, loading, streaming, stutter, lifecycle: [references/memory-and-loading.md](memory-and-loading.md)
- Large/open worlds, chunk ownership, origin/precision decisions, rapid traversal, or streaming continuity: [references/large-worlds-and-streaming.md](large-worlds-and-streaming.md)
- Export/package/download size, release presets, PCK/archive hygiene, or accidental QA/report dependencies: [references/export-and-size.md](export-and-size.md)
- CI/CD, dependency locks, clean rebuilds, signing separation, or reproducibility claims: [references/reproducible-builds-and-dependencies.md](reproducible-builds-and-dependencies.md)
- Desktop/mobile/console storefront candidates, signing, install/update, platform SDKs, cloud/achievements, or store submission: [references/platform-release-and-stores.md](platform-release-and-stores.md)
- Native Android/iOS install, safe area, orientation, lifecycle, permission, thermal, memory, or device QA: [references/mobile-native-production.md](mobile-native-production.md)
- Remote config, experiments, events, telemetry, privacy, rollout, rollback, or backend fallback: [references/liveops-telemetry-and-privacy.md](liveops-telemetry-and-privacy.md)
- OpenXR/headsets or authorized console SDK/devkit work: [references/xr-and-console.md](xr-and-console.md)
- Mods, plugins, PCK/resource packs, user-authored content, load order, safe mode, or UGC trust/distribution: [references/modding-and-ugc.md](modding-and-ugc.md)
- Yandex Games Web integration, monetization, saves, lifecycle, moderation, or archive QA: [references/yandex-games-web.md](yandex-games-web.md)
- Crash reporting, abnormal-exit recovery, watchdogs, safe mode, symbols, support logs, or recovery budgets: [references/crash-resilience-and-diagnostics.md](crash-resilience-and-diagnostics.md)
- Purchases, paid currency, DLC/subscriptions, entitlements, restores, refunds, or revocations: [references/commerce-and-entitlements.md](commerce-and-entitlements.md)
- Guest/account linking, cloud saves, cross-device conflicts, user switching, or cross-progression: [references/accounts-cloud-and-cross-progression.md](accounts-cloud-and-cross-progression.md)
- Anti-cheat/integrity, reports, mute/block, sanctions, appeals, moderation, or online privacy operations: [references/online-safety-and-anti-abuse.md](online-safety-and-anti-abuse.md)
- Godot/dependency/protocol upgrades, old artifact compatibility, migration fixtures, or rollback: [references/upgrade-compatibility.md](upgrade-compatibility.md)
- Failure injection, parser/service fuzzing, interruption, replay/reordering, disk-full, or permission hardening: [references/fault-injection-and-fuzzing.md](fault-injection-and-fuzzing.md)
- Desktop minimum hardware, renderers/drivers, ultrawide/HiDPI/HDR, multiple displays, window lifecycle, or device hot-plug: [references/desktop-hardware-and-display.md](desktop-hardware-and-display.md)
- Screen readers, semantic UI, non-visual play, switch-like/non-pointer access, live announcements, or deeper motor/cognitive assists: [references/assistive-accessibility.md](assistive-accessibility.md)

Validation:

- Candidate hashes, decoded media, timed motion, review receipts or legacy evidence migration: [evidence-integrity.md](evidence-integrity.md)

- Always before completion: [references/validation.md](validation.md)
- Visual deliverables: [references/visual-validation.md](visual-validation.md)
- Raw Godot MJPEG AVI motion/delivery evidence: after capture, run `scripts/mjpeg_avi_watchback.py` to verify every encoded frame and duration and to produce an ordered frame/contact-sheet packet; file creation is not watchback
- External/generated assets: [references/asset-validation.md](asset-validation.md)
- Sprite sheets or generated 2D production art: sprite checks in [references/asset-generation.md](asset-generation.md)
- GLB/glTF models: model checks in [references/asset-integration.md](asset-integration.md)
- Performance/memory optimization: validation section in the relevant optimization reference
- Export/build-size work: validation section in the export reference
- Complete mobile/web evidence setup or rubric migration: generate fresh evidence files with `scripts/evidence_helper.py` instead of reconstructing gates, profiles, and the viewport matrix from memory
- Mixed-genre/platform/system work: run `scripts/rubric_case_plan.py --rubric <skill-dir>/evals/rubric.json --case <base+modifier+...> --json-output <plan.json> --summary`, then pass the same canonical composite selector to `evidence_helper.py` and `eval_scorecard.py`
- Long autonomous build or work likely to span context compaction: instantiate `assets/project-run-state.template.md`, keep it short, and update verified truth instead of appending a diary
- Complete game/slice packet: fill the art-direction selection, semantic identity, menu craft, cross-surface craft, production-art state, production-motion quality, HUD glanceability, applicable character-motion, exact review-profile reset and independent UX templates named above, with their required raw target-build states and reviewer owners; one self-review cannot replace the packet
- UI behavior: adapt the bundled touch-scroll or button-composition Godot probe when applicable; for reference parity use its template plus `scripts/image_compare.py`, and for third-party adoption record the decision in `assets/addon-adoption-record.template.md`
- Selected gameplay/system contracts: run the project-specific model, deterministic probe, target-build traces and review named in its routed reference. A model PASS does not replace authored-flow proof or required independent/human acceptance
- Online, platform, device and creator contracts: retain separate-process/real-service, exact-candidate, real-device/hardware/authorization, or uncoached-creator evidence required by the selected case; mocks and future work remain limitations
- Reliability/service/release modifiers: instantiate the routed JSON contract, run its dedicated probe, preserve raw target-build failure-state evidence, then obtain only the independent or human verdict explicitly owned by the rubric; routine correctness stays builder-owned
- Changes to this skill itself: maintain `assets/forward-eval-matrix.template.json` and run `scripts/forward_eval_audit.py`; every changed contract needs positive and negative fixtures in isolated builder/reviewer contexts
- Free-orbit third-person locomotion/camera/visibility work: adapt `assets/godot-tests/third_person_controller_probe.gd`, `assets/godot-tests/third_person_hud_mouse_probe.gd`, and `assets/godot-tests/third_person_visibility_probe.gd`, then complete the target-build matrix in `assets/third-person-3d-review.template.md`
- Isometric projection, picking, grid navigation, height transitions, depth sorting, or occlusion: apply the conditional validation in [references/isometric-and-2-5d.md](isometric-and-2-5d.md); adapt `assets/godot-tests/isometric_projection_probe.gd` and `assets/godot-tests/isometric_navigation_probe.gd` where their contracts fit
- Complete fixed-camera isometric/orthographic game: before bulk content, fill `assets/isometric-complete-review.template.md`; measure same-frame character/background separation with `scripts/isometric_readability_audit.py --require-thresholds`; and support the claimed scope with `assets/content-duration-contract.template.md`
- Complete fixed/high-angle 3D district or arena: add rubric modifier `high-angle-3d-district-complete`; fill the district/environment/visible-first reviews and resolved-scene provenance manifest; first run the copied streetscape exporter's engine-backed `--self-test-primitive-mesh true` fixture under the project's Godot version; run `scripts/resolved_scene_provenance_audit.py` with every evidence contract, then `scripts/environment_integrity_audit.py`, schema-v2 `scripts/environment_coverage_audit.py`, schema-v3 `scripts/visible_first_boundary_audit.py`, and schema-v6 `scripts/streetscape_semantics_audit.py` when roads exist; preserve the exporter fixture log plus raw target-build boundary/corridor/gameplay/repetition/contact close-ups, a zero-gap shipping-camera survey contact sheet, whole-perimeter ordered-hit trace/contact sheet, exporter-owned production-capsule grid/contact sheet, collision-assembly intent/bindings/global-transform/contact-distance report, solid-volume traversal traces, modular-seam/opening close-ups, visible-limiter continuity ledger, bidirectional visible-solid/collider inventory and raster overlays, explicit non-solid VFX classifications, two opposed diagonal facade-role captures with MSAA-normalized exclusive masks, resolved marking chains, typed road-end policy/topmost-surface samples, vertex-to-mount support close-ups, and production occluder/camera restoration video
- Complete non-isometric 2.5D game: use rubric case `new-2-5d-complete`, keep an explicit spatial contract, and combine the production-art state matrix, general production-motion contract, applicable production-character motion contract, gameplay-HUD glanceability review, menu/semantic identity reviews, and independent Windows target-build UX verdict

Hybrid tasks may require several references, but only after the composite case plan names the material contracts. Do not read unrelated references preemptively.
