# Actual Review-modality Profile Reset

Use this after the last builder run and before independent/product-owner handoff. Reset the exact path the reviewer will launch, not a convenient parallel profile.

## Candidate and review route

- Game / exact build ID:
- Source revision/hash:
- Planned reviewer:
- Exact launch modality (`Godot Editor Run Project/Scene`, exported desktop build, browser origin/profile, device app/account, other):
- Project/app identity used to resolve storage:
- Reset performed after the final builder automation/capture pass: NOT TESTED

## Storage envelope

| State location / namespace | Role (primary, backup, recovery, cloud, cache, settings) | Pre-reset existence/hash/summary | Reset method | Post-reset existence/hash/summary | Could restore seeded progress | PASS / FAIL / N/A |
|---|---|---|---|---|---|---|
| | | | | | | |

For Godot editor Run, resolve the real project `user://` location and include primary plus backup/recovery saves. For Web, record the exact origin and browser profile; clean automation storage does not cover an editor or another browser profile. Do not delete unrelated user data—scope the reset to the explicit test project/application identity.

## Expected and observed clean first boot

| Field | Shipping default | Observed through the actual review modality | PASS / FAIL |
|---|---|---|---|
| Progress/unlocks/completed content | | | |
| Tutorial/onboarding completion | | | |
| Currency/upgrades/inventory | | | |
| Settings that intentionally persist | | | |
| Seed/debug/developer state | | | |

- Raw first-boot artifact:
- Runtime trace/report proving the launched modality and loaded source:
- Backup/recovery did not repopulate seeded state: NOT TESTED
- A second clean launch remains deterministic: NOT TESTED
- Seeded QA profile remains separate and labeled: NOT TESTED
- Builder gate verdict: NOT TESTED
