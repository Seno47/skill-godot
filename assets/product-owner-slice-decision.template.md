# Product-owner Slice Decision

Use this before bulk content authoring for an open-ended new complete game. The representative slice must already pass routine builder-owned QA; this checkpoint asks whether the owner wants the concept and visual direction multiplied, not whether they can find ordinary defects.

## Representative slice

- Game / exact slice build ID:
- Source revision/hash:
- Product owner and decision context:
- Core promise in one sentence:
- Ordinary repeated loop demonstrated:
- Success/failure/recovery demonstrated:
- Selected visual direction and gameplay-size anchor:
- Raw target-build slice recording:
- Raw ordinary and dense screenshots:
- Actual clean review modality/profile:
- Builder-owned gates passed before owner review:
- Known limitations disclosed before decision:

## Bulk-authoring boundary

- Authored levels/encounters/chapters at review time:
- Representative mechanics and permutations present:
- Asset families present:
- Progression depth present:
- Work explicitly deferred until this decision:
- Date/build after which bulk multiplication would begin:

## Owner decision

Record one explicit outcome and the original user/product-owner context. Silence, an initial written idea, or an independent reviewer PASS is not approval after play.

- [ ] `APPROVE` — multiply this core loop/concept and visual direction.
- [ ] `REVISE` — change the named concept/direction choice and present a new slice.
- [ ] `WAIVE` — owner explicitly authorizes bulk work without this post-play approval.
- [ ] `CLOSE` — owner ends the project; record `project_disposition.status=user_closed`.

- Decision message/context:
- Decision timestamp/build:
- Named revisions or exclusions:
- Bulk authoring authorized: NOT TESTED
- Product-owner gate verdict: NOT TESTED

`APPROVE` or explicit `WAIVE` passes this gate. `REVISE` returns scoped work to the builder. `CLOSE` is not a failure to repair: it enters the non-success `PROJECT_CLOSED / USER_REJECTED` terminal and stops work.
