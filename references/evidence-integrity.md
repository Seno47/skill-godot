# Evidence Integrity and Honest Evaluation

The scorecard validates recorded evidence; it does not generate perceptual verdicts. Keep four claims separate: a contract is listed, a deterministic test ran, media belongs to the candidate and decodes, and a reviewer actually judged that media. Synthetic fixtures test validators only.

## Candidate and receipts

Use `run_metadata.candidate` with `build_id`, `path`, and the SHA-256 of the exact exported build or deterministic source/dependency manifest. Keep `builder_context` as a stable session identifier. A passing gate records the same `build_id` and `candidate_sha256`.

For multi-file builds use the complete package or a verified manifest of all runtime files, not the EXE alone when a separate PCK/resources can change. A source manifest must cover instantiated dependencies, imports, scripts and relevant export settings and be regenerated/verified against those bytes (see [reproducible-builds-and-dependencies.md](reproducible-builds-and-dependencies.md)). The scorecard hashes the supplied candidate artifact; it does not discover omitted dependencies or establish that screenshots came from it. Capture provenance and dependency coverage still need their own checks.

Every artifact on a passing gate includes `path`, `kind`, `sha256`, and `states`. For video states include `segments` mapping state to `[start_seconds, end_seconds]`. Hashes detect stale/replaced files; media decoding checks actual content. A valid image does not prove that its state label is true: inspect it. Do not duplicate one screenshot under several filenames to manufacture the required state count.

For external acceptance include a `reviewer.receipt` JSON file with the reviewer ID/context, candidate binding, response provenance (`source_context` and exact `source_message`), and per-gate observations/decisions. The receipt must be an actual preserved response from that context, not a builder-authored substitute. Each PASS cites exact artifact hashes and states observed, concrete observations, and unresolved blockers (none for PASS). For blind visual gates preserve initial observations before intended mappings; for motion quality record normal-speed segments watched. Hash the receipt in the evidence.

One receipt may cover several gates, and one artifact may legitimately cover several visible states or timed segments. Do not create duplicate review forms. The validator can check internal consistency and stale media, not authenticate a human or prove blindness. Actual tool/session messages establish that boundary; never claim cryptographic identity from a context string.

## Media and tool availability

Images require successful full decoding with Pillow. Godot MJPEG AVI can be checked with the bundled RIFF reader plus Pillow; other video formats require ffmpeg/ffprobe. Video duration and state ranges must agree. Motion gates additionally require `watchback[video_sha256]` with `start_seconds=0`, `end_seconds` equal to the full decoded duration, `playback_speed=1`, and actual `observations`. A missing decoder leaves evidence unverified; do not silently accept an extension. Decoding is not watchback, nor is a contact sheet proof of smooth motion or sound.

Routine builder work still includes real input/animation/contact checks and visual inspection. A human preference check remains external and does not excuse a known defect. One independent craft review may serve several art/UI gates when it explicitly covers their states.

## Migration

Old evidence remains readable. `evidence_helper.py --from-existing ...` preserves notes and submitted statuses but adds unresolved candidate fields; old PASS claims fail admissibility until the actual artifacts and acceptance context are bound. Preserve external responses using `assets/review-receipt.template.json`. Use `scripts/evidence_bind.py` to hash existing local artifacts and bind the candidate; it does not change verdicts or invent review receipts. Re-run the scorecard and inspect invalidations.

## Skill tests versus forward evaluations

`forward_eval_audit.py --mode coverage` checks scenario declarations and prints COVERAGE, never behavioral PASS. Existing schema-v1 matrices are historical coverage records, not proof that their described experiments ran.

Execution mode requires schema-v2 observed runs with an immutable skill commit resolvable in `--skill-repo`, present hashed briefs/results, distinct builder/reviewer identifiers, expected and observed outcomes and a preserved reviewer receipt. Paths are relative to the matrix file. Positive and negative calibration cases must agree with their expected outcomes. Runtime and perception results should be reported separately; passing parser unit tests cannot establish artistic improvement.

Before calling an instruction change effective, run the relevant actual task or reusable scene, inspect outputs, and retain both working and deliberately broken cases. If no independent blind run happened, report that limitation rather than counting a planned scenario as passed.
