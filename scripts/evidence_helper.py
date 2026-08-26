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

from rubric_case_composer import CaseCompositionError, gate_applies, resolve_case_selector


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_TEMPLATE = ROOT / "assets" / "capture-manifest.template.json"
REVIEW_TEMPLATE = ROOT / "assets" / "independent-ux-review.template.md"
YANDEX_CHECKLIST_TEMPLATE = ROOT / "assets" / "yandex-release-checklist.template.md"
MENU_REVIEW_TEMPLATE = ROOT / "assets" / "menu-identity-craft-review.template.md"
PRODUCTION_ART_REVIEW_TEMPLATE = ROOT / "assets" / "production-art-state-review.template.md"
MOTION_REVIEW_TEMPLATE = ROOT / "assets" / "production-character-motion.template.md"
HUD_REVIEW_TEMPLATE = ROOT / "assets" / "gameplay-hud-glanceability-review.template.md"
PROGRESSION_BALANCE_REVIEW_TEMPLATE = ROOT / "assets" / "progression-balance-review.template.md"
NETWORK_REVIEW_TEMPLATE = ROOT / "assets" / "networked-multiplayer-review.template.md"
EXTRACTION_REVIEW_TEMPLATE = ROOT / "assets" / "extraction-review.template.md"
ONLINE_SERVICE_REVIEW_TEMPLATE = ROOT / "assets" / "online-service-readiness.template.md"
SAVE_REVIEW_TEMPLATE = ROOT / "assets" / "save-data-integrity-review.template.md"
AI_REVIEW_TEMPLATE = ROOT / "assets" / "ai-navigation-review.template.md"
PROCEDURAL_REVIEW_TEMPLATE = ROOT / "assets" / "procedural-generation-review.template.md"
INPUT_ACCESSIBILITY_REVIEW_TEMPLATE = ROOT / "assets" / "input-accessibility-review.template.md"
STRATEGY_REVIEW_TEMPLATE = ROOT / "assets" / "strategy-simulation-review.template.md"
VEHICLE_REVIEW_TEMPLATE = ROOT / "assets" / "vehicle-racing-review.template.md"
SHOOTER_REVIEW_TEMPLATE = ROOT / "assets" / "shooter-action-review.template.md"
NARRATIVE_REVIEW_TEMPLATE = ROOT / "assets" / "narrative-review.template.md"
PLATFORM_RELEASE_TEMPLATE = ROOT / "assets" / "platform-release-matrix.template.md"
MODDING_REVIEW_TEMPLATE = ROOT / "assets" / "modding-ugc-review.template.md"
LOCALIZATION_REVIEW_TEMPLATE = ROOT / "assets" / "localization-review.template.md"
REPRODUCIBLE_BUILD_REVIEW_TEMPLATE = ROOT / "assets" / "reproducible-build-review.template.md"
REPLAY_REVIEW_TEMPLATE = ROOT / "assets" / "replay-review.template.md"
LARGE_WORLD_REVIEW_TEMPLATE = ROOT / "assets" / "large-world-streaming-review.template.md"
MOBILE_NATIVE_REVIEW_TEMPLATE = ROOT / "assets" / "mobile-native-review.template.md"
LIVEOPS_REVIEW_TEMPLATE = ROOT / "assets" / "liveops-review.template.md"
XR_CONSOLE_REVIEW_TEMPLATE = ROOT / "assets" / "xr-console-review.template.md"
RUNTIME_AUTHORING_REVIEW_TEMPLATE = ROOT / "assets" / "runtime-authoring-review.template.md"
CRASH_REVIEW_TEMPLATE = ROOT / "assets" / "crash-resilience-review.template.md"
COMMERCE_REVIEW_TEMPLATE = ROOT / "assets" / "commerce-entitlement-review.template.md"
ACCOUNT_CLOUD_REVIEW_TEMPLATE = ROOT / "assets" / "account-cloud-review.template.md"
ONLINE_SAFETY_REVIEW_TEMPLATE = ROOT / "assets" / "online-safety-review.template.md"
UPGRADE_REVIEW_TEMPLATE = ROOT / "assets" / "upgrade-compatibility-review.template.md"
FAULT_REVIEW_TEMPLATE = ROOT / "assets" / "fault-injection-review.template.md"
DESKTOP_REVIEW_TEMPLATE = ROOT / "assets" / "desktop-hardware-review.template.md"
ASSISTIVE_REVIEW_TEMPLATE = ROOT / "assets" / "assistive-accessibility-review.template.md"
PROJECT_STATUS_TEMPLATE = ROOT / "assets" / "project-run-state.template.md"


class EvidenceHelperError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or migrate evaluation evidence against the current rubric without inventing passes."
    )
    parser.add_argument("--rubric", required=True, help="Rubric JSON, normally evals/rubric.json.")
    parser.add_argument(
        "--case",
        required=True,
        dest="case_id",
        help="One case ID or a '+'-joined fail-closed composite of rubric case IDs.",
    )
    parser.add_argument("--output", required=True, help="Destination evidence JSON.")
    parser.add_argument("--from-existing", help="Existing evidence JSON to preserve and migrate.")
    parser.add_argument("--capture-manifest-output", help="Also instantiate the canonical capture manifest.")
    parser.add_argument("--review-output", help="Also instantiate the independent review template.")
    parser.add_argument("--menu-review-output", help="Also instantiate the menu identity craft review.")
    parser.add_argument(
        "--hud-review-output",
        help="Also instantiate the gameplay HUD glanceability review.",
    )
    parser.add_argument(
        "--project-status-output",
        help="Also instantiate the compact durable project run-state record.",
    )
    parser.add_argument(
        "--progression-balance-review-output",
        help="Also instantiate the cross-genre progression and balance review.",
    )
    parser.add_argument(
        "--network-review-output",
        help="Also instantiate the networked multiplayer review.",
    )
    parser.add_argument(
        "--extraction-review-output",
        help="Also instantiate the extraction loop review.",
    )
    parser.add_argument(
        "--online-service-review-output",
        help="Also instantiate the MMO/online-service readiness review.",
    )
    parser.add_argument("--save-review-output", help="Also instantiate the save integrity review.")
    parser.add_argument("--ai-review-output", help="Also instantiate the AI/navigation review.")
    parser.add_argument(
        "--procedural-review-output",
        help="Also instantiate the procedural-generation review.",
    )
    parser.add_argument(
        "--input-accessibility-review-output",
        help="Also instantiate the input/accessibility review.",
    )
    parser.add_argument(
        "--strategy-review-output",
        help="Also instantiate the strategy/simulation review.",
    )
    parser.add_argument(
        "--vehicle-review-output",
        help="Also instantiate the vehicle/racing review.",
    )
    parser.add_argument(
        "--shooter-review-output",
        help="Also instantiate the shooter/action review.",
    )
    parser.add_argument(
        "--narrative-review-output",
        help="Also instantiate the narrative/cinematic review.",
    )
    parser.add_argument(
        "--platform-release-output",
        help="Also instantiate the platform/store release matrix.",
    )
    parser.add_argument(
        "--modding-review-output",
        help="Also instantiate the modding/UGC review.",
    )
    parser.add_argument("--localization-review-output", help="Also instantiate localization review.")
    parser.add_argument(
        "--reproducible-build-review-output",
        help="Also instantiate reproducible build and dependency review.",
    )
    parser.add_argument("--replay-review-output", help="Also instantiate replay/ghost review.")
    parser.add_argument(
        "--large-world-review-output", help="Also instantiate large-world streaming review."
    )
    parser.add_argument("--mobile-native-review-output", help="Also instantiate mobile review.")
    parser.add_argument("--liveops-review-output", help="Also instantiate LiveOps/privacy review.")
    parser.add_argument("--xr-console-review-output", help="Also instantiate XR/console review.")
    parser.add_argument(
        "--runtime-authoring-review-output", help="Also instantiate runtime authoring review."
    )
    parser.add_argument("--crash-review-output", help="Also instantiate crash resilience review.")
    parser.add_argument("--commerce-review-output", help="Also instantiate commerce review.")
    parser.add_argument("--account-cloud-review-output", help="Also instantiate account/cloud review.")
    parser.add_argument("--online-safety-review-output", help="Also instantiate online safety review.")
    parser.add_argument("--upgrade-review-output", help="Also instantiate upgrade review.")
    parser.add_argument("--fault-review-output", help="Also instantiate fault-injection review.")
    parser.add_argument("--desktop-review-output", help="Also instantiate desktop hardware review.")
    parser.add_argument("--assistive-review-output", help="Also instantiate assistive accessibility review.")
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
    rubric: dict[str, Any], case_selector: str, existing: dict[str, Any] | None, rubric_path: Path
) -> tuple[dict[str, Any], list[str]]:
    if rubric.get("schema_version") != 1:
        raise EvidenceHelperError("Only rubric schema_version 1 is supported")
    try:
        case_id, selected_cases, _ = resolve_case_selector(rubric, case_selector)
    except CaseCompositionError as exc:
        raise EvidenceHelperError(str(exc)) from exc

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
        if not isinstance(definition, dict):
            continue
        try:
            applies = gate_applies(definition, selected_cases)
        except CaseCompositionError as exc:
            raise EvidenceHelperError(str(exc)) from exc
        if not applies:
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
            "component_cases": selected_cases,
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
                args.hud_review_output,
                args.progression_balance_review_output,
                args.network_review_output,
                args.extraction_review_output,
                args.online_service_review_output,
                args.save_review_output,
                args.ai_review_output,
                args.procedural_review_output,
                args.input_accessibility_review_output,
                args.strategy_review_output,
                args.vehicle_review_output,
                args.shooter_review_output,
                args.narrative_review_output,
                args.platform_release_output,
                args.modding_review_output,
                args.localization_review_output,
                args.reproducible_build_review_output,
                args.replay_review_output,
                args.large_world_review_output,
                args.mobile_native_review_output,
                args.liveops_review_output,
                args.xr_console_review_output,
                args.runtime_authoring_review_output,
                args.crash_review_output,
                args.commerce_review_output,
                args.account_cloud_review_output,
                args.online_safety_review_output,
                args.upgrade_review_output,
                args.fault_review_output,
                args.desktop_review_output,
                args.assistive_review_output,
                args.project_status_output,
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
        if args.hud_review_output:
            copy_template(HUD_REVIEW_TEMPLATE, output_path(args.hud_review_output))
        if args.progression_balance_review_output:
            copy_template(
                PROGRESSION_BALANCE_REVIEW_TEMPLATE,
                output_path(args.progression_balance_review_output),
            )
        if args.network_review_output:
            copy_template(NETWORK_REVIEW_TEMPLATE, output_path(args.network_review_output))
        if args.extraction_review_output:
            copy_template(EXTRACTION_REVIEW_TEMPLATE, output_path(args.extraction_review_output))
        if args.online_service_review_output:
            copy_template(
                ONLINE_SERVICE_REVIEW_TEMPLATE,
                output_path(args.online_service_review_output),
            )
        if args.save_review_output:
            copy_template(SAVE_REVIEW_TEMPLATE, output_path(args.save_review_output))
        if args.ai_review_output:
            copy_template(AI_REVIEW_TEMPLATE, output_path(args.ai_review_output))
        if args.procedural_review_output:
            copy_template(PROCEDURAL_REVIEW_TEMPLATE, output_path(args.procedural_review_output))
        if args.input_accessibility_review_output:
            copy_template(
                INPUT_ACCESSIBILITY_REVIEW_TEMPLATE,
                output_path(args.input_accessibility_review_output),
            )
        if args.strategy_review_output:
            copy_template(STRATEGY_REVIEW_TEMPLATE, output_path(args.strategy_review_output))
        if args.vehicle_review_output:
            copy_template(VEHICLE_REVIEW_TEMPLATE, output_path(args.vehicle_review_output))
        if args.shooter_review_output:
            copy_template(SHOOTER_REVIEW_TEMPLATE, output_path(args.shooter_review_output))
        if args.narrative_review_output:
            copy_template(NARRATIVE_REVIEW_TEMPLATE, output_path(args.narrative_review_output))
        if args.platform_release_output:
            copy_template(PLATFORM_RELEASE_TEMPLATE, output_path(args.platform_release_output))
        if args.modding_review_output:
            copy_template(MODDING_REVIEW_TEMPLATE, output_path(args.modding_review_output))
        if args.localization_review_output:
            copy_template(
                LOCALIZATION_REVIEW_TEMPLATE, output_path(args.localization_review_output)
            )
        if args.reproducible_build_review_output:
            copy_template(
                REPRODUCIBLE_BUILD_REVIEW_TEMPLATE,
                output_path(args.reproducible_build_review_output),
            )
        if args.replay_review_output:
            copy_template(REPLAY_REVIEW_TEMPLATE, output_path(args.replay_review_output))
        if args.large_world_review_output:
            copy_template(
                LARGE_WORLD_REVIEW_TEMPLATE, output_path(args.large_world_review_output)
            )
        if args.mobile_native_review_output:
            copy_template(
                MOBILE_NATIVE_REVIEW_TEMPLATE, output_path(args.mobile_native_review_output)
            )
        if args.liveops_review_output:
            copy_template(LIVEOPS_REVIEW_TEMPLATE, output_path(args.liveops_review_output))
        if args.xr_console_review_output:
            copy_template(
                XR_CONSOLE_REVIEW_TEMPLATE, output_path(args.xr_console_review_output)
            )
        if args.runtime_authoring_review_output:
            copy_template(
                RUNTIME_AUTHORING_REVIEW_TEMPLATE,
                output_path(args.runtime_authoring_review_output),
            )
        if args.crash_review_output:
            copy_template(CRASH_REVIEW_TEMPLATE, output_path(args.crash_review_output))
        if args.commerce_review_output:
            copy_template(COMMERCE_REVIEW_TEMPLATE, output_path(args.commerce_review_output))
        if args.account_cloud_review_output:
            copy_template(ACCOUNT_CLOUD_REVIEW_TEMPLATE, output_path(args.account_cloud_review_output))
        if args.online_safety_review_output:
            copy_template(ONLINE_SAFETY_REVIEW_TEMPLATE, output_path(args.online_safety_review_output))
        if args.upgrade_review_output:
            copy_template(UPGRADE_REVIEW_TEMPLATE, output_path(args.upgrade_review_output))
        if args.fault_review_output:
            copy_template(FAULT_REVIEW_TEMPLATE, output_path(args.fault_review_output))
        if args.desktop_review_output:
            copy_template(DESKTOP_REVIEW_TEMPLATE, output_path(args.desktop_review_output))
        if args.assistive_review_output:
            copy_template(ASSISTIVE_REVIEW_TEMPLATE, output_path(args.assistive_review_output))
        if args.project_status_output:
            copy_template(PROJECT_STATUS_TEMPLATE, output_path(args.project_status_output))
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
            f"[PASS] Evidence prepared case={evidence['case_id']} added={len(added)} "
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
