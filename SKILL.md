---
name: skill-godot
description: Build, improve, test, and release Godot 4 games with editable scenes, coherent assets and UI, intentional animation, gameplay systems, and verified target builds. Supports 2D, 3D and hybrid projects; use only for Godot.
---

# Godot Game Development

Translate the user's game into authored Godot scenes and resources. Preserve their genre, references, scope, platform and explicit choices. Choose presentation from gameplay and production constraints when it is open; a convenient asset pack does not decide the game.

## Start at the right scale

Inspect `project.godot`, engine/renderer, nearby scenes and dependencies, input, exports and version-control state. Use `scripts/project_snapshot.py --project <project> --summary` for a bounded overview.

- **Focused fix/review:** inspect the affected flow and regression risk. Do not demand complete-game certification or redesign unrelated screens.
- **New game/slice:** establish the core action, platform/input, camera, art direction and scope; build one representative playable slice before multiplying content.
- **Release/system work:** select the smallest truthful base case and material modifiers with `scripts/rubric_case_plan.py`. Grouping review work does not remove applicable gates.

Use [task routing](references/task-routing.md) to select relevant guides for genre, dimension, assets, systems and platform. [Scoped production contracts](references/scoped-production-contracts.md) preserve conditional invariants; consult the relevant topic rather than loading the whole catalogue for a small task.

## Keep the game editable

Persistent actors, levels, UI, cameras, lighting, collision, animation and interaction anchors belong in `.tscn`/`.tres`. Scripts own behavior and orchestration. Runtime construction fits procedural, transient, streamed or performance-driven content; instantiate reusable authored scenes where possible.

Use small text edits for understood serialization and Godot editor/tool scripts for fragile or bulk work. Verify ownership and disk round trips. Do not rewrite imported hierarchies to appease a text parser: use documented limitations plus an exact engine load. Do not migrate engines, renderers or addons silently.

## Establish craft before multiplying content

For a new production slice read [visual-style selection](references/visual-style-selection.md), [UI design workflow](references/ui-design-workflow.md), and [motion and animation](references/motion-and-animation.md). Existing approved design is the controlling reference; do not force alternatives.

1. Identify the player's main action and what they must perceive before and after it. Define focal objects, information hierarchy, visual family and motion behavior.
2. Build a **design anchor**: main play screen, one consequential secondary screen and a component/state sheet with real content. A compact layered visual reference precedes bulk UI implementation. Compare directions only when the choice is materially open.
3. Implement the anchor with native controls, shared themes, authored art and animation. Capture at gameplay size and the smallest supported layout; compare with the chosen reference.
4. Exercise input -> action/contact -> consequence/settle, then repeated and dense action. Verify response, weight, facing, contact, interruptions, reduced motion and audio timing.
5. Repair discrepancies before multiplying screens/assets/levels. For open-ended complete games obtain owner approval of the playable slice or an explicit waiver before bulk content.

Use `assets/ui-design-anchor.template.md` with the art-direction record. `assets/motion-lab/` contains editable mechanism examples with deliberately bad variants, not finished art or a universal style.

Conventional text, rectangular buttons and flat symbols can be excellent. Judge purpose, hierarchy, proportion, state clarity and fit. Do not replace useful labels with ambiguous icons or add ornament solely to look bespoke. Remove redundant panels/headings and give frequent information a readable visual form. A themed dashboard is not automatically a suitable game HUD.

Generated art needs coherent source families and repairable layers. Sound needs appropriate licensed assets and actual listening; bus presence does not establish pleasant audio. Read the respective asset/audio guides when they apply.

## Verify experience and evidence separately

For focused edits, load the affected scenes and run relevant input/state/layout regressions. Read [validation](references/validation.md) for release or multi-system verification and [visual validation](references/visual-validation.md) for material visible changes. Complete-candidate review covers target-build ordinary play, dense interactions, pause/settings/results and applicable narrow/wide layouts. Routine defects remain the builder's responsibility.

For a complete candidate produce one shared capture/review packet. Reuse it across menu, HUD, cross-surface craft, comprehension and art-family gates; each verdict cites the states it covers. Follow [production craft](references/production-craft-and-product-approval.md) for blind first reads and owner decisions. Withhold intended meanings and desired verdicts until the reviewer's initial observations are recorded.

Use [evidence integrity](references/evidence-integrity.md) for candidate hashes, media decoding, state coverage, review receipts and migration. `eval_scorecard.py` checks admissibility and aggregates recorded verdicts; it cannot judge beauty, certify fun, authenticate a person or replace review. A role string or an existing file is not independent acceptance.

Keep deterministic correctness, media/candidate integrity, actual visual/motion/UX observations and external acceptance distinct. Never call a coverage manifest or synthetic unit fixture a completed gameplay/visual evaluation. In skill maintenance use `forward_eval_audit.py --mode coverage` for declarations and `--mode execution` for bound observed runs.

## Work efficiently and hand off truthfully

Keep one short run-state record: current verified build, decisions, commands, evidence and next actions. Use scoped searches and relevant references. Prefer Godot CLI/project-owned input/capture probes. Desktop Computer Use requires explicit opt-in or otherwise unreachable native OS behavior.

Retest changed behavior and affected dependencies. Reuse captures only when their candidate binding and scope remain valid. A screenshot cannot prove animation; decoding does not prove normal-speed watchback.

When builder work and available QA are complete deliver `BUILDER_COMPLETE / READY_FOR_HUMAN_TEST`, identifying genuinely external evidence pending in one sentence. Use `PUBLICATION_CERTIFIED` only after all applicable external gates pass. Known review failures return repair responsibility to the builder. Avoid obvious user testing/upload checklists.

For first-use review use an isolated clean profile in the actual review modality. Preserve user progress; reset only confirmed QA-owned profiles or explicitly authorized saves, including backups.

An explicit owner cancellation means `PROJECT_CLOSED / USER_REJECTED`: preserve the postmortem and stop. If new external permission or an unavailable capability prevents further authorized work, report that boundary honestly; persistence does not authorize unrelated or destructive action.
