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

## Collision intent and resolved assembly parity

Do not treat every collision mesh as the same kind of evidence. `surface_parity` follows a
complex static surface where contact with its facets is intended; `solid_volume_parity`
represents an obstacle the production body must neither enter nor climb. A safety backstop
is secondary containment only and cannot be the first reachable contact.

| Assembly | Intent | Visual members | Enabled shapes / type | Bidirectional bindings | Global root transform error | Required approaches | Raw close-up | Verdict |
|---|---|---:|---|---|---:|---|---|---|
| | | | | | | | | NOT TESTED |

- Schema is v3 and assembly paths/counts/shape classes/root transforms are exporter-resolved:
- Every visual member maps to shape(s), every shape maps back to visible mass, and disabled variants are excluded symmetrically:
- `solid_volume_parity` uses convex/compound solid forms; a concave walkable skin is not accepted for rubble, vehicle piles or other impassable masses:
- `surface_parity` concave shapes belong only to static bodies and preserve authored openings/indentations:
- Collider and visual asset roots have matching final global origin, rotation and scale within the declared project epsilon:
- Collider first contact and independently measured render-shell contact differ by no more than the final-size stand-off budget:

## Production-body approach and module-seam coverage

| Assembly / seam | Edge | Corners | Concavities | Module joints | Opening negative | Entered/climbed? | Raw normal-speed trace / close-up | Verdict |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | NOT TESTED |

- Use the enabled shipping `CharacterBody3D` and capsule, not a ray or reduced QA shape:
- Sample the complete length of every boundary span and explicitly tag both endpoints, every concavity and every adjacent-module joint:
- For solid-volume obstacles, drive the production body into every required approach; it remains outside the occupied volume and below the allowed elevation gain:
- A successful center approach does not cover corners, recesses or seams:
- Every modular seam has a matching capsule sample plus a raw shipping-camera close-up proving visual and collision continuity:
- Open doors/gates/arches receive a negative approach proving the authored opening remains traversable:

## Production-physics whole-body reachability

| Production body/shape | Grid / safe polygon source | Free unsafe fringe | Reachable unsafe cells | Missing/unreachable safe cells | Raw grid/contact sheet | Verdict |
|---|---|---:|---:|---:|---|---|
| | | | | | | NOT TESTED |

- Schema is v3 and `production_physics_reachability.source_kind` is exporter-resolved, not adapter-authored:
- Grid uses the actual enabled production hero `CapsuleShape3D`, ground/blocker layers and resolved `World3D`:
- Every declared cell is queried; the unsafe fringe is nonempty and covers every required side:
- Cell size is within the production hero-radius budget; eight-neighbor flood fill cannot skip a diagonal escape:
- Flood fill begins from every production start and reaches zero unsafe-fringe cells:
- Visible limiter baseline/current IDs and retained/replaced disposition ledger exactly cover the perimeter:
- Any removed limiter has mapped replacement visible causes plus before/fixed/current whole-body and visible-first proof:

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
- Broad collider or safety backstop stops the hero before the visible edge although its ID maps to a visible cause: PASS / FAIL / NOT TESTED
- Concave collision on an impassable rubble/vehicle pile lets the production body climb a sheet or enter between bodies: PASS / FAIL / NOT TESTED
- Visible and collision roots share local-looking values but differ after parent transforms: PASS / FAIL / NOT TESTED
- Center samples pass while a corner, facade recess or adjacent-module seam contains a hero-width hole: PASS / FAIL / NOT TESTED
- Collision is continuous at a module joint but the visible silhouettes expose a crack, or the reverse: PASS / FAIL / NOT TESTED
- Adapter supplies hand-written `free_cells`, `blocked_cells` or `outside_cells` while the production capsule can leave the safe polygon: PASS / FAIL / NOT TESTED
- A visible house/vehicle/wall limiter is deleted and the report calls the off-map continuation fixed without replacement-continuity evidence: PASS / FAIL / NOT TESTED
- Point/ray evidence passes while the production capsule body reaches an unsafe fringe cell: PASS / FAIL / NOT TESTED

## Builder verdict

- Deterministic audit status / reachable-unsafe / invisible-first / unmapped-first counts:
- Raw close-up/contact-sheet status:
- Blocking defects:
- Final gate: PASS / FAIL / NOT TESTED
- Exact rerun command:
