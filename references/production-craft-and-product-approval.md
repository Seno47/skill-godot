# Production Craft and Product Approval

Read this for a new complete game, a production candidate with several top-level UI surfaces, or a project whose concept/content will be multiplied after a vertical slice. This guide calibrates acceptance; it does not prescribe one visual style.

## Separate four questions

Do not collapse these decisions into one attractive screenshot or one reviewer paragraph:

1. **Routine builder correctness:** does the exact candidate work, render, animate, save, reset, and expose the required states without obvious defects?
2. **Independent production craft:** do the same candidate's menu, pause/runtime modal, settings, ordinary play/HUD, result/failure, and text-heaviest secondary surface form one coherent, legible product?
3. **Product-owner approval:** after playing a representative slice, does the owner want this core loop and visual direction multiplied into a complete game?
4. **Optional final preference:** after the blocking layers pass, would the owner prefer different flavor, pacing personality, or aesthetic taste?

An independent reviewer can judge comprehension and craft, but cannot decide whether the product owner likes the concept. Conversely, owner taste feedback does not replace routine builder QA.

## Review one candidate across surfaces

Use `assets/cross-surface-production-craft-review.template.md`. Lock one build/source ID and review these raw states together:

Reuse this packet for the menu/HUD/art-family gates when the same reviewer covered them. Bind actual artifacts and review receipts using [evidence-integrity.md](evidence-integrity.md). A declared independent role is not proof that another context reviewed the build. Include both a clear conventional design and an ornamental but confusing design in reviewer calibration; bespoke widgets receive no preference merely for being bespoke.

- main menu;
- pause or the material runtime modal that interrupts play;
- settings with real control states;
- ordinary gameplay and HUD;
- success/result and failure when applicable;
- progression/map/shop/inventory or the text-heaviest secondary surface;
- a final-size sheet of critical action/state icons;
- normal and dense gameplay frames where UI, world assets, telegraphs, contact effects, and peak VFX coexist.

One polished menu cannot cover an unfinished pause, settings dashboard, result panel, or map. Scene authorship, custom widgets, theme resources, shared colors, and consistent rectangles are implementation facts—not craft verdicts.

Compare hierarchy, typography, repeated card/rectangle motifs, density, contrast, wrapping, interaction-state clarity, icon family, optical alignment, action naming, and cross-surface consistency. A strong primary action must remain visibly primary; four equal choices are not hierarchy merely because they are arranged in a grid.

## Start with a blind first read

Before showing design intent, implementation notes, expected icon mappings, progression narration, or the builder's verdict:

- give the independent reviewer raw artifacts with neutral state IDs;
- ask what every critical icon depicts and which action/state it predicts at actual final size;
- ask the exact effect of each menu, pause, and result action, including whether it continues, restarts, discards progress, returns, advances, or purchases;
- for progression, use a short first-glance pass and ask current state, next reachable goal, cost/requirement, consequence, and new decision;
- record wrong guesses, uncertainty, and confidence before any explanation.

Later study can diagnose the problem but cannot retroactively turn the first read into PASS. Do not coach the reviewer with labels such as “purchased state,” “restart icon,” or a paragraph explaining the mapping before the initial observation.

Atmospheric language may support identity, but standard consequential actions use predictable player language first. A metaphor such as “Restore,” “Begin the path,” or “From the beginning” fails when an uncoached reviewer cannot predict whether it retries, creates a new save, resumes, or repairs an in-world object. A label/icon pair also fails when they predict different outcomes or contradict the surrounding result message.

Contextual calibration examples—not mandatory exact wording:

| Context | Ambiguous when used alone | Usually predictable player-language direction |
|---|---|---|
| Menu creates/resets a run | “Новый путь” / “New path” | “Новая игра” / “New game”, with flavor secondary |
| Pause resets the current level | “Сначала” / “From the beginning” | “Перезапустить уровень” / “Restart level” |
| Failure retries | “Восстановить” / “Restore” | “Повторить” / “Retry” |
| Success advances or returns | “Восстановить” / “Restore” | “Следующий уровень” / “Next level” or “К карте” / “Back to map” |

Use the project's actual locale and action model. Plain wording is not a ban on authored voice; it anchors consequence before metaphor.

## Audit visible pixels, not only node rectangles

For every critical icon-plus-label group, icon-only action, and major world cue, record:

- source dimensions or SVG `viewBox` and intrinsic content bounds;
- rendered control/group rect and actual final-size raster crop;
- visible alpha/pixel bounds and alpha-weighted or otherwise justified optical center;
- internal left/right/top/bottom padding and baseline relationship;
- visible area/weight relative to neighboring family members;
- filtering, halo/fringe, contrast, and small-size degradation;
- center of the whole compound group relative to its hit target.

Equal `TextureRect` sizes, matching pivots, or mathematical centers do not prove optical alignment. Use `scripts/icon_optical_audit.py` on final-size transparent crops for repeatable alpha bounds/centroid/weight evidence, then inspect the result visually. Metrics do not replace judgment: a ring, open arrow, dense wheel, and tiny square mark can have similar boxes while remaining an incoherent family.

## Judge cross-family integration in the same frames

Review world actors/objects, UI, telegraphs, tutorial cues, threats, and VFX together for:

- perspective and projection;
- edge treatment and outline/stroke language;
- texture/noise density and material response;
- scale and optical weight;
- contact, anchor, depth, occlusion, and attachment;
- shape/motion language and final-size filtering.

Palette agreement is only one channel. Reject painterly or textured world art crossed by foreign flat strips, thin wireframes, detached clip-art arrows/rings, debug-like lines, unanchored markers, or sharp VFX symbols that do not share the selected production language. A coherent asset family must survive dense interaction, not only an isolated source sheet.

## Reset the actual review modality

Before an independent or product-owner handoff, fill `assets/review-profile-reset.template.md` after the last builder run. Use an isolated clean profile in the exact modality where possible. Preserve user-owned progress. Reset only identified QA-owned saves or explicitly authorized saves, including recovery files, and verify the path the reviewer will use:

- Godot Editor **Run Project/Scene**: the real project `user://` save envelope, primary file, backup/recovery file, tutorial flag, and relevant settings;
- exported desktop build: its actual application data/save location and profile/slot;
- browser/Web: the exact browser profile/origin storage, service worker/cache version when material, and cloud/mock separation;
- mobile/console: the actual app data/account profile where available.

A clean Playwright/browser profile does not prove Godot editor Run is clean. A clean primary save does not pass if a backup restores seeded progress. Verify the clean first boot after resetting and after the final builder-owned automation/capture pass.

## Obtain product-owner approval before bulk content

For an open-ended new complete game, stop after a representative playable vertical slice and use `assets/product-owner-slice-decision.template.md` before multiplying levels, chapters, encounters, progression content, or expensive asset families. The slice must already pass routine builder QA; do not ask the owner to discover broken controls or unfinished art.

The owner decision is deliberately small:

- **approve** the core loop/concept and visual direction for bulk authoring;
- **revise** a named concept/direction choice and repeat the slice;
- explicitly **waive** this checkpoint and authorize bulk work;
- **close** the project.

A written initial idea, an agent-side independent PASS, or silence is not post-play approval. Record the exact slice build, what content existed at the decision, and the owner message/context. This is a product/taste authority boundary, not a user QA checklist.

## Close a rejected project truthfully

If the user/product owner explicitly cancels or closes the project, stop. Preserve the raw failure packet and set evidence `project_disposition.status` to `user_closed` with the decision context and `continue_authorized: false`. The scorecard terminal is `PROJECT_CLOSED / USER_REJECTED` (`project_closed_user_rejected` in JSON):

- it is not a PASS, READY, or publication claim;
- unresolved gates and defects remain visible for postmortem learning;
- the agent does not continue repairs or present a user checklist;
- reopening requires a new explicit user instruction, not an inferred continuation.

Do not use closure to hide builder-owned work or to stop merely because a task is difficult. It applies only to an explicit owner decision to end the project.
