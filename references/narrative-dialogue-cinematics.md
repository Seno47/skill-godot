# Narrative, Dialogue, and Cinematics

Read this for branching dialogue, cutscenes, voiced scenes, interactive conversations, narrative state, journals, subtitles, choices, relationship variables, or scripted sequences. Apply [quest-and-progression.md](quest-and-progression.md), [save-data-integrity.md](save-data-integrity.md), and [input-and-accessibility.md](input-and-accessibility.md) where relevant.

## Author content as versioned data

Use stable line/node/choice/sequence IDs and localization keys. Separate immutable dialogue/cinematic definitions from runtime visit/choice/variable state and presentation. Record speaker, conditions, effects, choice destination, interruptibility, skip behavior, re-entry policy, voice/subtitle timing, camera/actor ownership and save boundary.

Validate the narrative graph for unreachable required nodes, dangling destinations, unintended terminal nodes, impossible conditions, mutually exclusive prerequisites, cycles without an exit, and choices whose displayed result differs from committed state. Reuse `scripts/progression_graph_audit.py` when its graph contract fits, but retain narrative-specific conditions/effects and target-build traces.

## Make interruption safe

Test advance, choice, timeout, skip, pause, focus loss, language change, scene unload, actor disappearance, save/load before and after a state-changing line, replay and rollback/restart policy. A skipped cinematic must commit exactly the intended effects once and land in the same supported gameplay state as watching it; do not double rewards/quests/audio/camera restoration.

Subtitles need speaker identity, readable timing, safe-area placement, scalable text/background and captions for critical non-dialog sound when promised. Voice, subtitle and animation duration may differ by locale; never drive essential state solely from one language's audio length.

Use `assets/narrative-review.template.md` for raw target-build first encounter, branch alternatives, skip, interruption/recovery, save/reload, long localization, subtitles/voice and gameplay handoff. Independent review judges choice clarity, pacing, emotional readability, repetition, camera/actor staging and whether consequences match wording without designer narration.

