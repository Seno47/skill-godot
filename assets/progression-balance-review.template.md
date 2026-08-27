# Progression and Balance Review

## Scope and provenance

- Game / build ID:
- Progression model ID and audit report:
- Tested platform and input:
- Progression shape / genre:
- Monetization policy (`none`, `free path + optional acceleration`, other approved policy):
- Builder-owned target-build transaction trace:
- Independent human reviewer / recruitment context:
- Clean-profile provenance for each uncoached session:

## Declared hypothesis and budgets

Summarize the intended progression promise, session cadence, completion/reset cadence, applicable checks, and why any obviously relevant check is omitted. Confirm budgets were declared before the final evidence run rather than tuned around one observed trace.

## Sources, sinks, and reset boundaries

| Resource | Starting state | Sources | Sinks | Floor/cap | Reset/death/offline rule | Exploit/recovery notes |
|---|---:|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Power, challenge, rewards, and choices

| Checkpoint | Target time | Power/challenge intent | Meaningful unlock/reward | Choice or strategy | Failure/recovery intent |
|---|---:|---|---|---|---|
| Onboarding / first reward |  |  |  |  |  |
| First meaningful choice |  |  |  |  |  |
| Representative midgame |  |  |  |  |  |
| Late/high-pressure |  |  |  |  |  |
| Completion/reset |  |  |  |  |  |

## Builder-owned correctness verdict

- Deterministic probe: `PASS / FAIL`
- Target-build displayed/debited/granted values match the model: `PASS / FAIL`
- Reward/transaction exactly-once through retry, pause, save/reload, and scene transition: `PASS / FAIL`
- Floors/caps, overflow/rounding, bankruptcy, hoarding, duplicate reward, and clock/offline cases: `PASS / FAIL / N/A`
- Required options exercised; dead/dominant option findings:
- Model/build divergences and fixes:
- Builder gate: `PASS / FAIL / NOT TESTED`

## Player-facing visual comprehension matrix

Use raw target-build states from a clean profile. Correct transactions and localized text do not answer these questions by themselves.

| State ID | Raw artifact | What visibly changed | Next reachable goal/action | Cost or requirement | Consequence / new decision | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|---|---|
| `progression_clean_current` | | | | | | NOT TESTED |
| `progression_first_reward` | | | | | | NOT TESTED |
| `progression_first_choice` | | | | | | NOT TESTED |
| `progression_purchased_unlocked` | | | | | | NOT TESTED |
| `progression_locked_late` | | | | | | NOT TESTED |

Review whether maps, paths, node state, item/ability silhouettes, before/after art, meters, connectors, animation, landmarks, or another authored visual language communicate the progression. Reject a text table, solver trace, or repeated labeled card stack that requires builder narration to explain current state and consequence.

## Uncoached pacing sessions

Use at least two separate clean-profile human sessions and enough representative cohorts to stress the declared support contract. The reviewer need not be the user. Designer/autoplay/model traces are supporting evidence, not replacements.

| Trace | Cohort / prior genre experience | Strategy actually used | Observed time range | Choices / failures / recovery | Reward or drought observations | Completed / abandoned |
|---|---|---|---:|---|---|---|
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

## Independent pacing questions

- Could the player state the next progression goal without coaching?
- Which rewards changed a decision, and which were noise?
- Was any unlock/choice/reward drought confusing, dull, or coercive?
- Did failure invite a retry, or compound into fatigue/grind?
- Did any presented option feel mandatory, dead, or like a trap?
- Did the free path remain coherent without paid/rewarded acceleration?
- Did numeric/localized UI communicate cost, gain, cap, and locked state correctly?
- What differed between novice/conservative and expert/aggressive play?

## Independent visual-comprehension questions

- What changed after the reward or purchase?
- What can the player do next, and which goal is currently reachable?
- What does the next action cost or require?
- What consequence will the highlighted choice have?
- Which new route, build, action, or decision did the unlock create?
- Which of those answers came from authored visual state rather than reading a paragraph/table?

## Final verdict

- `progression_balance_model_evidence`: `PASS / FAIL / NOT TESTED`
- `progression_visual_comprehension_review`: `PASS / FAIL / NOT TESTED`
- `progression_pacing_playtest`: `PASS / FAIL / NOT TESTED`
- Tested range (early/mid/late/reset, systems and builds):
- Blocking defects:
- Explicitly untested progression, endgame, prestige, procedural, or monetized paths:
