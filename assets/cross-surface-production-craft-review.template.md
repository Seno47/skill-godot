# Cross-surface Production Craft Review

Use this blocking review after routine builder QA. One independent reviewer or genuinely separate evaluation context reviews one exact candidate across all top-level surfaces and integrated world/UI/VFX states. Do not provide the intended meanings before the blind first read.

## Candidate lock and provenance

- Game / exact build ID:
- Source revision/hash:
- Target platform/export:
- Builder/context:
- Independent reviewer/context:
- Reviewer did not build or previously study this flow: NOT TESTED
- Raw artifact root:
- Actual review modality/profile reset record:
- Brief and selected art/UI contract supplied after blind pass:

## Blind first-read protocol

- Neutral artifact order/IDs used:
- Time budget per surface:
- Builder intent, expected mappings, labels, and desired verdict withheld: NOT TESTED
- First-read observations were recorded before explanation: NOT TESTED
- Later explanation did not overwrite wrong guesses/uncertainty: NOT TESTED

### Critical icon/action predictions at actual final size

| Neutral ID | Raw final-size artifact | What the reviewer thinks it depicts | Predicted action/state | Confidence | Actual meaning shown only after answer | Match / ambiguity / mismatch |
|---|---|---|---|---|---|---|
| | | | | | | |

Include critical menu, HUD, settings, pause, result, progression, and world-cue symbols. Do not award recognition from a label the icon is supposed to replace. Ambiguous symbols may keep concise accessible text; the purpose is truthful prediction, not icon-only UI.

### Critical action-copy prediction

| Locale / surface | Raw copy and icon | Predicted exact effect | Continue/restart/new save/advance/return/purchase/loss understood | Actual effect revealed later | PASS / FAIL |
|---|---|---|---|---|---|
| | | | | | |

Fail atmospheric synonyms when the reviewer cannot predict the exact consequential action, when copy and icon disagree, or when a success/failure message contradicts the primary action.

## Same-candidate surface matrix

| Required state | Raw artifact | Primary hierarchy and likely first action | Repeated card/rectangle burden | Typography/copy/density/contrast/wrap | Icon/control family and state clarity | Optical alignment | PASS / FAIL / NOT TESTED |
|---|---|---|---|---|---|---|---|
| `main_menu` | | | | | | | NOT TESTED |
| `pause_or_runtime_modal` | | | | | | | NOT TESTED |
| `settings` | | | | | | | NOT TESTED |
| `ordinary_hud_or_core_play` | | | | | | | NOT TESTED |
| `result_or_fail` | | | | | | | NOT TESTED |
| `text_heaviest_secondary_surface` | | | | | | | NOT TESTED |

For a pausable game, use the actual pause surface. For a game with no meaningful pause state, use the material runtime modal that interrupts the loop and record why pause is not applicable. One attractive menu cannot compensate for an unfinished modal, settings screen, result, map, shop, inventory, or progression surface.

Custom/scene-authored widgets receive no automatic credit. Review slider/switch/option/scroll/focus/disabled/pressed craft, hierarchy, density, padding, state clarity, and whether a repeated outlined-card dashboard still dominates.

## Optical bounds and family audit

Attach the raw report from `scripts/icon_optical_audit.py` where applicable and record the remaining source/runtime observations.

| Asset/group | Intrinsic size or SVG viewBox/content bounds | Rendered rect | Visible alpha/pixel bounds | Optical center vs hit-target/group center | Internal padding / baseline | Relative visible weight | Filtering/halo/small-size result | Neighbor-family verdict |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

Equal container sizes and mathematical centers are supporting data only. Fail visible drift, inconsistent source scale, incompatible padding/silhouette/weight, cropped halos, or a compound icon-plus-label group whose optical center does not match the intended action hierarchy.

## Cross-family art coherence matrix

| Required state | Raw artifact | World actor/object family | UI/icon family | Telegraph/tutorial/threat family | Contact/anchor/depth | VFX/material/motion language | Coherent whole-frame verdict |
|---|---|---|---|---|---|---|---|
| `world_ui_normal` | | | | | | | NOT TESTED |
| `dense_contact_or_telegraph` | | | | | | | NOT TESTED |
| `peak_vfx_or_consequence` | | | | | | | NOT TESTED |

Compare perspective, edge treatment, texture density, scale, optical weight, material response, and contact language. Palette agreement does not pass painterly/generated world art crossed by foreign flat strips, thin wireframes, detached arrows/rings, unanchored smudges, or sharp unrelated VFX symbols.

## Independent first-glance progression when material

Do not show intended mappings or state names before this pass.

| Neutral raw state | Current state guessed | Next reachable goal/action guessed | Cost/requirement guessed | Consequence/new decision guessed | Uncertainty/wrong guesses recorded | PASS / FAIL / N/A |
|---|---|---|---|---|---|---|
| | | | | | | |

A later studied explanation cannot retroactively pass this first-glance result.

## Cross-surface comparison

- Does primary/secondary hierarchy remain consistent across surfaces?
- Are typography, spacing, edge treatment, state art, icon weight, and interaction feedback one family?
- Does any screen fall back to equal rectangles, generic geometry, thin decorative lines, or a dashboard of outlined rows?
- Can the reviewer identify the ordinary loop and consequential actions without builder narration?
- Which custom/authored elements still look unfinished despite being structurally valid?
- Which world/UI/telegraph/VFX elements disagree in perspective, texture density, contact, or material language?

## Final gate verdicts

- Cross-surface production craft: NOT TESTED
- Critical icon/action-copy comprehension: NOT TESTED
- Optical icon/group alignment and family coherence: NOT TESTED
- Cross-family world/UI/telegraph/VFX coherence: NOT TESTED
- Blind first-glance progression comprehension when applicable: NOT TESTED
- Blocking defects and exact surfaces:
- Review limitations:
