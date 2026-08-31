# Whole-perimeter Visible-first Boundary Review

Use with `references/3d-environment-integrity.md` and `references/road-and-streetscape-semantics.md`. This is builder-owned blocking evidence for any high-angle map that keeps an invisible safety collider behind visible boundary art.

## Exact candidate

- Build ID / target artifact:
- Production scene / shipping camera:
- Resolved dependency-closure digest and manifest SHA-256:
- Probe/exporter path + SHA-256:
- Contract JSON / audit JSON:
- Hero radius / height / collision mask:
- Declared perimeter spans / total deterministic samples:
- Raw trace / contact-sheet root:

## Span coverage and first-contact order

| Span | Start/end | Outward direction | Spacing / samples | Probe kind / hero coverage | First visible cause mapping | Safety backstop | Minimum measured clearance | Raw overview | Verdict |
|---|---|---|---:|---|---|---|---:|---|---|
| | | | | | | | | | NOT TESTED |

- Every enabled safety-only perimeter collider exported:
- Every declared span sampled endpoint-to-endpoint with no missing index:
- Maximum spacing is no greater than the hero diameter:
- Capsule matches production hero radius/height, or ray bundle covers the full width without lateral gaps:
- Every probe points inward-to-outward:
- First contact is a collider with an exact visible render-shell/cause mapping:
- Safety-only contact occurs only behind the visible cause with the declared clearance:
- Opening/exit spans remain traversable and are not silently included as closed perimeter:

## Detected defect provenance

| Class / span / sample | Before build/raw close-up | Fixed build/raw close-up | Candidate rerun/raw close-up | Audit result | Verdict |
|---|---|---|---|---|---|
| | | | | | NOT TESTED |

## Negative regressions

- Flood-fill reports zero reachable safety pockets while one evenly sampled perimeter point hits the safety wall first: PASS / FAIL / NOT TESTED
- Root/provenance or build differs between trace, raw close-up and candidate: PASS / FAIL / NOT TESTED
- A point ray is narrower than the hero and no full-width ray bundle/capsule evidence exists: PASS / FAIL / NOT TESTED
- Visible object name exists but hit collider/render shell is unmapped or stale: PASS / FAIL / NOT TESTED
- Safety wall is behind visible art but below the minimum clearance margin: PASS / FAIL / NOT TESTED

## Builder verdict

- Deterministic audit status / invisible-first / unmapped-first counts:
- Raw close-up/contact-sheet status:
- Blocking defects:
- Final gate: PASS / FAIL / NOT TESTED
- Exact rerun command:
