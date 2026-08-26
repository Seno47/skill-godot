# Modding and UGC Review

## Trust and format

- Build/mod API/schema versions:
- Tier: `data-only / media / authored pack / executable code`
- Namespace/load-order/dependency policy:
- Size/type/decode limits:
- Distribution/moderation/rights path:
- Independent security reviewer context:

## Acceptance matrix

| Content/state | Expected | Observed isolation/diagnostic | Save effect | Artifact | Verdict |
|---|---|---|---|---|---|
| Valid content |  |  |  |  |  |
| Malformed/corrupt |  |  |  |  |  |
| Oversized/decode bomb |  |  |  |  |  |
| Traversal/protected collision |  |  |  |  |  |
| Missing/cyclic dependency |  |  |  |  |  |
| Incompatible/duplicate ID |  |  |  |  |  |
| Removed-mod save |  |  |  |  |  |
| Safe mode/no mods |  |  |  |  |  |

- Is arbitrary code possible and how is consent/trust communicated?
- Can rejected content partially mutate registries or saves?
- Are licenses, reports/takedowns and offline/update flows defined?

- `modding_ugc_evidence`: `PASS / FAIL / NOT TESTED`
- `modding_security_review`: `PASS / FAIL / NOT TESTED`
- Blocking defects:

