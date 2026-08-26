# Difficulty and Pacing by Genre

Read this for every complete game in which challenge, tension, cognitive load, execution pressure, risk, or competitive skill is material. Apply it alongside the relevant genre guide and, when power/resources persist, [progression-and-balance.md](progression-and-balance.md).

There is no universal recommended curve. A useful envelope keeps challenge legible relative to learned skill, introduces novelty at a controlled pace, and gives the intended experience room to breathe. A wave, sawtooth, director, route map, skill band, run arc, or deliberately flat segment can all be correct. The contract must say which one is intended and prove that the build implements it; a steadily rising spreadsheet is not automatically good design.

## Research-grounded principles

- Match perceived challenge to the supported player's growing skill and teach through play. Separate execution, cognition, time, resources, punishment, uncertainty, coordination, and navigation/information load instead of hiding them in one number.
- Build mastery from learned concepts and meaningful combinations. More enemies, HP, speed, cost, obscurity, travel, or repetition is not a new idea by itself.
- Use peaks and relief when the experience depends on intensity. Recovery may be a quiet room, planning window, safe retry, low-stakes beat, replenishment, narrative release, or player-selected retreat—not necessarily an easy fight.
- Preserve agency and reliable feedback. Assistance or dynamic difficulty must not silently invalidate success, erase upgrade value, change ranked outcomes, or create exploitable rubber-banding.
- Treat models and automated traces as builder-owned correctness evidence. Perceived fairness, fatigue, excitement, mastery, and frustration still require uncoached target-build play; the commissioning user is not the default QA department.

The design rationale is informed by GameFlow's challenge/skill and pacing criteria, Butler et al.'s work on mastery of base concepts and combinations, Valve's intensity peaks/valleys in Left 4 Dead, Hunicke's DDA constraints, MDA, experience-driven PCG, and TrueSkill-style uncertainty-aware matchmaking. These are design inputs, not universal numeric thresholds:

- https://www.valuesatplay.org/wp-content/uploads/2007/09/sweetser.pdf
- https://www.microsoft.com/en-us/research/publication/automatic-game-progression-design-analysis-solution-features/
- https://valvearchive.com/archive/Other%20Files/Publications/ai_systems_of_l4d_mike_booth.pdf
- https://www.researchgate.net/profile/Robin_Hunicke/publication/220982524_The_case_for_dynamic_difficulty_adjustment_in_games/links/53fb98490cf2dca8fffe800a.pdf
- https://www.cs.northwestern.edu/~hunicke/MDA.pdf
- https://yannakakis.net/wp-content/uploads/2019/02/EDPCG.pdf
- https://www.microsoft.com/en-us/research/publication/trueskilltm-a-bayesian-skill-rating-system-2/

## Declare the envelope before bulk content

Adapt `assets/difficulty-pacing-contract.template.json`, then run:

```bash
python <skill-dir>/scripts/difficulty_pacing_probe.py --contract reports/difficulty-pacing.json --summary --json-output reports/difficulty-pacing-audit.json
```

Declare:

- one primary genre profile and curve model;
- the supported player cohorts and evidence sources;
- active difficulty dimensions and a definition of what score 0–5 means in this game;
- ordered beats with `teach`, `practice`, `twist`, `combine`, `test`, `peak`, `recovery`, `choice`, or `reset` roles;
- skills introduced and reused at each beat;
- novelty, consecutive-rise, peak-to-recovery, onboarding-pressure, and retry budgets;
- adaptation policy, its legal surfaces, bounds, cooldown/hysteresis, disclosure/control, and outcome/reward integrity;
- target-build observations that exercise the declared beats. Do not invent player enjoyment from them.

A scalar challenge score is only a readable index. Keep its dimension vector and authored cause. Two beats with the same scalar may feel entirely different if one raises execution while the other raises punishment or uncertainty.

## Genre profiles

- **Puzzle:** use `puzzle_mastery`; teach a concept safely, practice it, combine at least two learned concepts, then test transfer. Obscure wording, extra walking, a timer, or a larger search space is not automatically better puzzle difficulty.
- **Action, shooter, fighting, brawler:** use authored waves or skill bands. Vary enemy/attack composition, spatial decisions, execution and resource pressure; include readable peaks and recovery. Do not rely on HP/damage inflation or simultaneous unreadable attacks.
- **Platformer/metroidvania:** teach movement or ability vocabulary safely, repeat it in a changed context, combine it, and test mastery. Backtracking distance, camera friction, input imprecision, or unclear collision are defects, not difficulty.
- **Horror/survival:** distinguish tension/intensity from lethal punishment. Alternate anticipation, escalation, peak and relief; preserve resource agency and recovery. Constant maximum threat numbs rather than intensifies.
- **Roguelite/procedural:** model the within-run arc and across-seed envelope. Prove bounded floors/ceilings, recovery opportunities and no unwinnable novelty spikes; progression must not erase the run's core decisions.
- **RPG/progression/idle:** compose with the balance contract. Verify encounter/economy/loadout dimensions, power expression and recovery; level scaling must not cancel earned upgrades, while grind or waiting cannot masquerade as mastery.
- **Strategy/tactics/management:** grow decision space, concurrency, information and resource pressure with planning windows. Check snowball/comeback behavior and novice/expert routes; more units or faster clocks alone are insufficient.
- **Racing/vehicle:** teach track/handling vocabulary, then combine speed, surface, traffic and route decisions. Keep time-trial comparisons stable. Rubber-banding must be bounded, non-deceptive, non-exploitable and outside ranked outcome manipulation.
- **Extraction/survival sandbox/open world:** use self-selected routes or danger geography. Model low/medium/high-risk paths, loss and bankruptcy recovery; do not force every raid into the same linear escalation.
- **Co-op/director-paced:** track team intensity and individual vulnerability, cap concurrent threats, create peaks and relief, and test mixed-skill teams. Avoid punishing the whole team invisibly for one strong player.
- **Competitive multiplayer:** use visible rules, modes, matchmaking/rating bands and uncertainty-aware placement. Never use hidden mid-match DDA to steer a ranked result. Test asymmetric sides, team composition, queue quality and newcomers separately.
- **Narrative/cinematic:** model cognitive, emotional, choice and interaction load rather than inventing combat numbers. Use comprehension/rest beats around revelations and branching decisions.
- **Sandbox/creative:** prefer danger geography, opt-in goals and self-selected challenge. A single mandatory campaign curve may be inapplicable; declare the choice topology and safe experimentation/recovery instead.

For hybrids, choose the profile governing the current loop and record secondary genre constraints in the rationale. Do not average incompatible curves into one meaningless line.

## Dynamic difficulty and assistance

Prefer explicit difficulty, assist options, route choice, matchmaking, or pre-encounter composition changes when they preserve player understanding. If `adaptive_director` is used, require bounded declared surfaces, a cooldown or hysteresis rule, no mid-action stat flicker, preserved rewards/outcomes, deterministic control traces, and an unadjusted comparison. Assistance should first improve information, aim/input tolerance, checkpointing, resources, or optional hints where appropriate; it must not falsely report the original challenge as beaten if that distinction matters.

For competitive/ranked play, adjustment belongs in matchmaking, placement, team formation, or clearly declared modes—not hidden mid-match outcome steering. Record rating uncertainty and provisional/new-player handling rather than treating one point estimate as truth.

## Evidence and completion

Builder-owned evidence must include the declared JSON, deterministic probe report, target-build traces for required beats, and comparison traces for every adaptive surface. The probe rejects malformed or self-contradictory envelopes; it does not certify fun.

For a complete game, instantiate `assets/difficulty-pacing-review.template.md` and obtain at least two clean-profile uncoached target-build sessions across representative cohorts. Review challenge comprehension, skill use, peaks/relief, novelty, failure/retry, fatigue, fairness, adaptation perception, and genre-specific expectations. If the promised campaign/run/session length is longer than the observed range, the unobserved portion remains `NOT TESTED`.

Do not hand off a complete game as correctly paced while either `difficulty_pacing_evidence` or `difficulty_pacing_playtest` is unresolved. A vertical slice may pass only for its explicitly tested envelope and must not imply that unbuilt later difficulty is validated.
