#!/usr/bin/env python3
"""Create or migrate truthful Godot skill evaluation evidence scaffolds."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_TEMPLATE = ROOT / "assets" / "capture-manifest.template.json"
REVIEW_TEMPLATE = ROOT / "assets" / "independent-ux-review.template.md"
YANDEX_CHECKLIST_TEMPLATE = ROOT / "assets" / "yandex-release-checklist.template.md"
MENU_REVIEW_TEMPLATE = ROOT / "assets" / "menu-identity-craft-review.template.md"
PRODUCTION_ART_REVIEW_TEMPLATE = ROOT / "assets" / "production-art-state-review.template.md"
MOTION_REVIEW_TEMPLATE = ROOT / "assets" / "production-character-motion.template.md"


class EvidenceHelperError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or migrate evaluation evidence against the current rubric without inventing passes."
    )
    parser.add_argument("--rubric", required=True, help="Rubric JSON, normally evals/rubric.json.")
    parser.add_argument("--case", required=True, dest="case_id", help="Case ID from the rubric.")
    parser.add_argument("--output", required=True, help="Destination evidence JSON.")
    parser.add_argument("--from-existing", help="Existing evidence JSON to preserve and migrate.")
    parser.add_argument("--capture-manifest-output", help="Also instantiate the canonical capture manifest.")
    parser.add_argument("--review-output", help="Also instantiate the independent review template.")
    parser.add_argument("--menu-review-output", help="Also instantiate the menu identity craft review.")
    parser.add_argument(
        "--production-art-review-output",
        help="Also instantiate the builder-owned production art state review.",
    )
    parser.add_argument(
        "--motion-review-output",
        help="Also instantiate the production character motion contract.",
    )
    parser.add_argument("--yandex-checklist-output", help="Also instantiate the Yandex release checklist.")
    parser.add_argument("--force", action="store_true", help="Allow replacing explicitly named outputs.")
    return parser.parse_args()


def read_json(path_value: str | Path, label: str) -> dict[str, Any]:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise EvidenceHelperError(f"{label} not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceHelperError(f"Could not read {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EvidenceHelperError(f"{label} root must be an object")
    return data


def output_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def require_writable(path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise EvidenceHelperError(f"Output exists; pass --force to replace it: {path}")
    if path.exists() and not path.is_file():
        raise EvidenceHelperError(f"Output is not a file: {path}")


def gate_applies(definition: dict[str, Any], case_id: str) -> bool:
    cases = definition.get("cases")
    return cases is None or (isinstance(cases, list) and case_id in cases)


def unresolved_gate(
    description: Any, acceptance_owner: str, requires_artifacts: bool
) -> dict[str, Any]:
    suffix = str(description).strip() if isinstance(description, str) else "current rubric gate"
    result: dict[str, Any] = {
        "status": "not_tested",
        "evidence": [
            f"UNRESOLVED [{acceptance_owner}-owned]: supply an artifact or limitation for {suffix}"
        ],
        "reviewer": {
            "role": acceptance_owner,
            "context": "UNRESOLVED: record the actual acceptance context before passing this gate",
        },
    }
    if requires_artifacts:
        result["artifacts"] = []
    return result


def unresolved_dimension(description: Any) -> dict[str, Any]:
    suffix = str(description).strip() if isinstance(description, str) else "current rubric dimension"
    return {
        "status": "scored",
        "score": 0,
        "evidence": [f"UNRESOLVED: score and cite observed evidence for {suffix}"],
        "notes": (
            "Generated unresolved value; replace with observed evidence or an allowed not_applicable status. "
            "Builder evidence is valid for routine objective checks; only rubric gates explicitly owned by "
            "independent or human contexts require those reviewers."
        ),
    }


def prepare_evidence(
    rubric: dict[str, Any], case_id: str, existing: dict[str, Any] | None, rubric_path: Path
) -> tuple[dict[str, Any], list[str]]:
    if rubric.get("schema_version") != 1:
        raise EvidenceHelperError("Only rubric schema_version 1 is supported")
    cases = {item.get("id"): item for item in rubric.get("cases", []) if isinstance(item, dict)}
    if case_id not in cases:
        raise EvidenceHelperError(f"Unknown case ID: {case_id}")

    if existing is None:
        result: dict[str, Any] = {
            "schema_version": 1,
            "case_id": case_id,
            "gates": {},
            "scores": {},
            "run_metadata": {},
            "limitations": [],
        }
    else:
        result = copy.deepcopy(existing)
        if result.get("schema_version") != 1:
            raise EvidenceHelperError("Only evidence schema_version 1 can be migrated")
        if result.get("case_id") != case_id:
            raise EvidenceHelperError("Existing evidence case_id does not match --case")

    allowed_top_level = {
        "schema_version",
        "case_id",
        "gates",
        "scores",
        "run_metadata",
        "limitations",
    }
    unknown = sorted(set(result) - allowed_top_level)
    if unknown:
        raise EvidenceHelperError(f"Existing evidence has unsupported top-level keys: {', '.join(unknown)}")
    gates = result.setdefault("gates", {})
    scores = result.setdefault("scores", {})
    metadata = result.setdefault("run_metadata", {})
    limitations = result.setdefault("limitations", [])
    if not isinstance(gates, dict) or not isinstance(scores, dict) or not isinstance(metadata, dict):
        raise EvidenceHelperError("gates, scores, and run_metadata must be objects")
    if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
        raise EvidenceHelperError("limitations must be an array of strings")

    added: list[str] = []
    owner_default = rubric.get("acceptance_owner_default", "builder")
    owner_definitions = rubric.get(
        "acceptance_owner_definitions",
        {"builder": "", "independent": "", "human": ""},
    )
    if not isinstance(owner_definitions, dict) or owner_default not in owner_definitions:
        raise EvidenceHelperError("Rubric acceptance owner definitions/default are invalid")
    for definition in rubric.get("blocking_gates", []):
        if not isinstance(definition, dict) or not gate_applies(definition, case_id):
            continue
        gate_id = definition.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            raise EvidenceHelperError("Every applicable blocking gate needs an ID")
        acceptance_owner = definition.get("acceptance_owner", owner_default)
        if acceptance_owner not in owner_definitions:
            raise EvidenceHelperError(f"Gate {gate_id} names an unknown acceptance owner")
        if gate_id not in gates:
            gates[gate_id] = unresolved_gate(
                definition.get("description"),
                acceptance_owner,
                definition.get("artifact_requirements") is not None,
            )
            added.append(f"gate:{gate_id}")
            continue
        gate_value = gates[gate_id]
        if not isinstance(gate_value, dict):
            raise EvidenceHelperError(f"Existing gate {gate_id} must be an object")
        if "reviewer" not in gate_value:
            gate_value["reviewer"] = {
                "role": acceptance_owner,
                "context": (
                    "UNRESOLVED: migrated evidence must record the actual acceptance context; "
                    "the previous status was preserved but cannot pass the current scorecard yet"
                ),
            }
            added.append(f"reviewer:{gate_id}")
        if definition.get("artifact_requirements") is not None and "artifacts" not in gate_value:
            gate_value["artifacts"] = []
            added.append(f"artifacts:{gate_id}")

    for definition in rubric.get("dimensions", []):
        if not isinstance(definition, dict):
            continue
        dimension_id = definition.get("id")
        if not isinstance(dimension_id, str) or not dimension_id:
            raise EvidenceHelperError("Every dimension needs an ID")
        if dimension_id not in scores:
            scores[dimension_id] = unresolved_dimension(definition.get("description"))
            added.append(f"score:{dimension_id}")

    digest = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
    helper_metadata = metadata.setdefault("evidence_helper", {})
    if not isinstance(helper_metadata, dict):
        raise EvidenceHelperError("run_metadata.evidence_helper must be an object when present")
    helper_metadata.update(
        {
            "rubric_sha256": digest,
            "case_id": case_id,
            "generated_values_are_unresolved": True,
        }
    )
    metadata.setdefault("builder_context", "unrecorded")
    metadata.setdefault("independent_reviewer_context", "unrecorded")
    metadata.setdefault("build_id", "unrecorded")
    metadata.setdefault("clean_profile_provenance", "unrecorded")
    metadata.setdefault("seeded_profile_provenance", "unrecorded")
    metadata.setdefault("capture_manifest", "unrecorded")
    metadata.setdefault(
        "artifact_root",
        ".",
    )
    return result, added


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def copy_template(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def main() -> int:
    args = parse_args()
    try:
        rubric_path = Path(args.rubric).expanduser().resolve()
        rubric = read_json(rubric_path, "rubric")
        existing = read_json(args.from_existing, "existing evidence") if args.from_existing else None

        evidence_output = output_path(args.output)
        optional_outputs = [
            output_path(value)
            for value in (
                args.capture_manifest_output,
                args.review_output,
                args.menu_review_output,
                args.production_art_review_output,
                args.motion_review_output,
                args.yandex_checklist_output,
            )
            if value is not None
        ]
        all_outputs = [evidence_output, *optional_outputs]
        if len(set(all_outputs)) != len(all_outputs):
            raise EvidenceHelperError("Output paths must be distinct")
        for path in all_outputs:
            require_writable(path, args.force)

        evidence, added = prepare_evidence(rubric, args.case_id, existing, rubric_path)
        write_json(evidence_output, evidence)
        if args.capture_manifest_output:
            copy_template(CAPTURE_TEMPLATE, output_path(args.capture_manifest_output))
        if args.review_output:
            copy_template(REVIEW_TEMPLATE, output_path(args.review_output))
        if args.menu_review_output:
            copy_template(MENU_REVIEW_TEMPLATE, output_path(args.menu_review_output))
        if args.production_art_review_output:
            copy_template(
                PRODUCTION_ART_REVIEW_TEMPLATE,
                output_path(args.production_art_review_output),
            )
        if args.motion_review_output:
            copy_template(MOTION_REVIEW_TEMPLATE, output_path(args.motion_review_output))
        if args.yandex_checklist_output:
            copy_template(YANDEX_CHECKLIST_TEMPLATE, output_path(args.yandex_checklist_output))

        print(
            f"[PASS] Evidence prepared case={args.case_id} added={len(added)} "
            f"output={evidence_output}"
        )
        for item in added:
            print(f"[UNRESOLVED] {item}")
        return 0
    except EvidenceHelperError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[ERROR] Could not write output: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
