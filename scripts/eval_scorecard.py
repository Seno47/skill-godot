#!/usr/bin/env python3
"""Validate and score evidence from independent Godot skill evaluations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from rubric_case_composer import CaseCompositionError, gate_applies, resolve_case_selector


class ScorecardError(RuntimeError):
    pass


ARTIFACT_EXTENSIONS = {
    "image": {".png", ".jpg", ".jpeg", ".webp"},
    "video": {".avi", ".mp4", ".webm", ".mov", ".mkv"},
    "review": {".md", ".json", ".txt"},
    "report": {".md", ".json", ".txt", ".log"},
    "trace": {".json", ".txt", ".log", ".csv", ".md"},
    "log": {".log", ".txt", ".json"},
    "audio": {".wav", ".ogg", ".mp3", ".flac", ".m4a"},
    "build": {".exe", ".zip", ".pck", ".wasm", ".html", ".apk", ".appimage"},
}
UNRESOLVED_PREFIXES = ("unrecorded", "unresolved", "not tested", "not_tested")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a Godot skill evaluation against a stable rubric.")
    parser.add_argument("--rubric", required=True, help="Rubric JSON, normally evals/rubric.json.")
    parser.add_argument("--evidence", required=True, help="Evaluation evidence JSON.")
    parser.add_argument(
        "--case",
        required=True,
        dest="case_id",
        help="One case ID or a '+'-joined fail-closed composite of rubric case IDs.",
    )
    parser.add_argument("--baseline", help="Optional previous scorecard JSON for a score delta.")
    parser.add_argument("--json-output", help="Write the complete scorecard JSON.")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def read_json(value: str, label: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ScorecardError(f"{label} not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScorecardError(f"Could not read {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScorecardError(f"{label} root must be an object")
    return data


def evidence_items(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ScorecardError(f"{label} must be a list of non-empty strings")
    return value


def artifact_items(value: Any, label: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ScorecardError(f"{label} must be an array")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ScorecardError(f"{label}[{index}] must be an object")
        path = item.get("path")
        kind = item.get("kind")
        states = item.get("states", [])
        description = item.get("description")
        if not isinstance(path, str) or not path.strip():
            raise ScorecardError(f"{label}[{index}].path must be a non-empty string")
        if kind not in ARTIFACT_EXTENSIONS:
            raise ScorecardError(
                f"{label}[{index}].kind must be one of {', '.join(sorted(ARTIFACT_EXTENSIONS))}"
            )
        if not isinstance(states, list) or any(
            not isinstance(state, str) or not state.strip() for state in states
        ):
            raise ScorecardError(f"{label}[{index}].states must be an array of non-empty strings")
        if len(states) != len(set(states)):
            raise ScorecardError(f"{label}[{index}].states must not contain duplicates")
        if description is not None and (not isinstance(description, str) or not description.strip()):
            raise ScorecardError(f"{label}[{index}].description must be a non-empty string")
        result.append(
            {
                "path": path.strip(),
                "kind": kind,
                "states": states,
                **({"description": description.strip()} if isinstance(description, str) else {}),
            }
        )
    return result


def resolve_artifact_root(evidence_path: Path, run_metadata: Any) -> Path:
    root_value = run_metadata.get("artifact_root", ".") if isinstance(run_metadata, dict) else "."
    if not isinstance(root_value, str) or not root_value.strip():
        raise ScorecardError("run_metadata.artifact_root must be a non-empty path string")
    root = Path(root_value).expanduser()
    if not root.is_absolute():
        root = evidence_path.parent / root
    return root.resolve()


def validate_pass_artifacts(
    gate_id: str,
    artifacts: list[dict[str, Any]],
    requirements: Any,
    artifact_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    failures: list[str] = []
    resolved_artifacts: list[dict[str, Any]] = []
    for item in artifacts:
        path = Path(item["path"]).expanduser()
        if not path.is_absolute():
            path = artifact_root / path
        path = path.resolve()
        enriched = {**item, "resolved_path": str(path)}
        resolved_artifacts.append(enriched)
        if not path.is_file():
            failures.append(f"artifact is missing or not a file: {item['path']}")
            continue
        try:
            if path.stat().st_size <= 0:
                failures.append(f"artifact is empty: {item['path']}")
        except OSError as exc:
            failures.append(f"artifact cannot be inspected: {item['path']} ({exc})")
            continue
        allowed = ARTIFACT_EXTENSIONS[item["kind"]]
        if path.suffix.lower() not in allowed:
            failures.append(
                f"artifact kind {item['kind']} has unexpected extension {path.suffix or '<none>'}: "
                f"{item['path']}"
            )

    if requirements is None:
        return resolved_artifacts, failures
    if not isinstance(requirements, dict):
        raise ScorecardError(f"Gate {gate_id}.artifact_requirements must be an object")
    minimum_by_kind = requirements.get("minimum_by_kind", {})
    required_states = requirements.get("required_states", {})
    if not isinstance(minimum_by_kind, dict):
        raise ScorecardError(f"Gate {gate_id}.artifact_requirements.minimum_by_kind must be an object")
    if not isinstance(required_states, dict):
        raise ScorecardError(f"Gate {gate_id}.artifact_requirements.required_states must be an object")

    unique_by_kind: dict[str, set[str]] = {}
    for item in resolved_artifacts:
        unique_by_kind.setdefault(item["kind"], set()).add(item["resolved_path"])
    for kind, minimum in minimum_by_kind.items():
        if kind not in ARTIFACT_EXTENSIONS:
            raise ScorecardError(f"Gate {gate_id} requires unknown artifact kind: {kind}")
        if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
            raise ScorecardError(
                f"Gate {gate_id}.artifact_requirements.minimum_by_kind.{kind} must be a positive integer"
            )
        actual = len(unique_by_kind.get(kind, set()))
        if actual < minimum:
            failures.append(f"requires at least {minimum} concrete {kind} artifact(s); found {actual}")

    for state, allowed_kinds in required_states.items():
        if not isinstance(state, str) or not state:
            raise ScorecardError(f"Gate {gate_id} has an invalid required artifact state")
        if (
            not isinstance(allowed_kinds, list)
            or not allowed_kinds
            or any(kind not in ARTIFACT_EXTENSIONS for kind in allowed_kinds)
        ):
            raise ScorecardError(
                f"Gate {gate_id}.artifact_requirements.required_states.{state} must list known kinds"
            )
        if not any(
            state in item["states"] and item["kind"] in allowed_kinds
            for item in resolved_artifacts
        ):
            failures.append(
                f"missing required state '{state}' as one of: {', '.join(allowed_kinds)}"
            )
    return resolved_artifacts, failures


def main() -> int:
    args = parse_args()
    try:
        evidence_path = Path(args.evidence).expanduser().resolve()
        rubric = read_json(args.rubric, "rubric")
        evidence = read_json(args.evidence, "evidence")
        if rubric.get("schema_version") != 1 or evidence.get("schema_version") != 1:
            raise ScorecardError("rubric and evidence schema_version must be 1")
        try:
            case_id, selected_cases, case_definition = resolve_case_selector(rubric, args.case_id)
        except CaseCompositionError as exc:
            raise ScorecardError(str(exc)) from exc
        if evidence.get("case_id") != case_id:
            raise ScorecardError("evidence.case_id does not match --case")

        gate_evidence = evidence.get("gates")
        score_evidence = evidence.get("scores")
        if not isinstance(gate_evidence, dict) or not isinstance(score_evidence, dict):
            raise ScorecardError("evidence.gates and evidence.scores must be objects")

        owner_default = rubric.get("acceptance_owner_default", "builder")
        owner_definitions = rubric.get(
            "acceptance_owner_definitions",
            {"builder": "", "independent": "", "human": "", "provider": ""},
        )
        if not isinstance(owner_definitions, dict) or not owner_definitions:
            raise ScorecardError("rubric.acceptance_owner_definitions must be a non-empty object")
        allowed_owners = set(owner_definitions)
        if owner_default not in allowed_owners:
            raise ScorecardError("rubric.acceptance_owner_default must name a defined acceptance owner")
        artifact_root = resolve_artifact_root(evidence_path, evidence.get("run_metadata", {}))

        gates: list[dict[str, Any]] = []
        blocking = False
        for definition in rubric.get("blocking_gates", []):
            gate_id = definition.get("id")
            try:
                applies = gate_applies(definition, selected_cases)
            except CaseCompositionError as exc:
                raise ScorecardError(f"Gate {gate_id}: {exc}") from exc
            if not applies:
                continue
            value = gate_evidence.get(gate_id)
            if not isinstance(value, dict):
                raise ScorecardError(f"Missing gate evidence: {gate_id}")
            status = value.get("status")
            if status not in {"pass", "fail", "not_tested"}:
                raise ScorecardError(f"Gate {gate_id}.status must be pass, fail, or not_tested")
            evidence_notes = evidence_items(value.get("evidence", []), f"gate {gate_id}.evidence")
            if not evidence_notes:
                raise ScorecardError(f"Gate {gate_id} requires at least one evidence artifact or limitation record")
            acceptance_owner = definition.get("acceptance_owner", owner_default)
            if acceptance_owner not in allowed_owners:
                raise ScorecardError(
                    f"Gate {gate_id}.acceptance_owner must name a defined acceptance owner"
                )
            reviewer = value.get("reviewer")
            reviewer_role = reviewer.get("role") if isinstance(reviewer, dict) else None
            reviewer_context = reviewer.get("context") if isinstance(reviewer, dict) else None
            structured_artifacts = artifact_items(value.get("artifacts"), f"gate {gate_id}.artifacts")
            resolved_artifacts, validation_failures = validate_pass_artifacts(
                gate_id,
                structured_artifacts,
                definition.get("artifact_requirements"),
                artifact_root,
            )
            if status == "pass":
                if reviewer_role != acceptance_owner:
                    validation_failures.append(
                        f"passing gate requires reviewer.role={acceptance_owner}; found {reviewer_role or 'missing'}"
                    )
                if not isinstance(reviewer_context, str) or not reviewer_context.strip():
                    validation_failures.append("passing gate requires a non-empty reviewer.context")
                elif reviewer_context.strip().lower().startswith(UNRESOLVED_PREFIXES):
                    validation_failures.append("passing gate reviewer.context is still unresolved")
            effective_status = "fail" if status == "pass" and validation_failures else status
            blocking = blocking or effective_status != "pass"
            gates.append(
                {
                    "id": gate_id,
                    "status": effective_status,
                    "submitted_status": status,
                    "acceptance_owner": acceptance_owner,
                    "reviewer": reviewer,
                    "evidence": evidence_notes,
                    "artifacts": resolved_artifacts,
                    "validation_failures": validation_failures,
                    "description": definition.get("description"),
                }
            )

        gate_results = {item["id"]: item for item in gates}

        scale = rubric.get("score_scale", {})
        minimum, maximum = scale.get("min", 0), scale.get("max", 4)
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)) or maximum <= minimum:
            raise ScorecardError("Invalid rubric score scale")
        dimensions: list[dict[str, Any]] = []
        active_weight = 0.0
        warnings: list[str] = []
        for definition in rubric.get("dimensions", []):
            dimension_id = definition.get("id")
            weight = definition.get("weight")
            if not isinstance(weight, (int, float)) or weight <= 0:
                raise ScorecardError(f"Dimension {dimension_id} has invalid weight")
            value = score_evidence.get(dimension_id)
            if not isinstance(value, dict):
                raise ScorecardError(f"Missing score evidence: {dimension_id}")
            status = value.get("status", "scored")
            if status == "not_applicable":
                if not definition.get("allow_not_applicable"):
                    raise ScorecardError(f"Dimension {dimension_id} cannot be not_applicable")
                dimensions.append({"id": dimension_id, "status": status, "weight": weight})
                continue
            if status != "scored":
                raise ScorecardError(f"Dimension {dimension_id}.status must be scored or not_applicable")
            score = value.get("score")
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not minimum <= score <= maximum:
                raise ScorecardError(f"Dimension {dimension_id}.score must be between {minimum} and {maximum}")
            artifacts = evidence_items(value.get("evidence", []), f"dimension {dimension_id}.evidence")
            if not artifacts:
                warnings.append(f"Dimension {dimension_id} has no evidence artifacts")
            active_weight += float(weight)
            dimensions.append(
                {
                    "id": dimension_id,
                    "status": "scored",
                    "score": score,
                    "submitted_score": score,
                    "weight": weight,
                    "evidence": artifacts,
                    "notes": value.get("notes"),
                }
            )
        if active_weight <= 0:
            raise ScorecardError("No active scored dimensions")

        dimension_results = {item["id"]: item for item in dimensions}
        score_caps_applied: list[dict[str, Any]] = []
        cap_rules = rubric.get("score_caps", [])
        if not isinstance(cap_rules, list):
            raise ScorecardError("rubric.score_caps must be a list")
        for index, rule in enumerate(cap_rules):
            if not isinstance(rule, dict):
                raise ScorecardError(f"score_caps[{index}] must be an object")
            gate_id = rule.get("gate")
            statuses = rule.get("statuses", ["fail", "not_tested"])
            caps = rule.get("dimensions")
            if not isinstance(gate_id, str) or not gate_id:
                raise ScorecardError(f"score_caps[{index}].gate must be a non-empty string")
            if (
                not isinstance(statuses, list)
                or not statuses
                or any(status not in {"pass", "fail", "not_tested"} for status in statuses)
            ):
                raise ScorecardError(f"score_caps[{index}].statuses contains an invalid gate status")
            if not isinstance(caps, dict) or not caps:
                raise ScorecardError(f"score_caps[{index}].dimensions must be a non-empty object")
            gate_result = gate_results.get(gate_id)
            if gate_result is None or gate_result["status"] not in statuses:
                continue
            for dimension_id, cap in caps.items():
                result = dimension_results.get(dimension_id)
                if result is None:
                    raise ScorecardError(f"score cap for {gate_id} references unknown dimension: {dimension_id}")
                if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not minimum <= cap <= maximum:
                    raise ScorecardError(
                        f"score cap for {gate_id}.{dimension_id} must be between {minimum} and {maximum}"
                    )
                if result.get("status") != "scored" or float(result["score"]) <= float(cap):
                    continue
                before = result["score"]
                result["score"] = cap
                score_caps_applied.append(
                    {
                        "gate": gate_id,
                        "gate_status": gate_result["status"],
                        "dimension": dimension_id,
                        "before": before,
                        "after": cap,
                    }
                )

        submitted_weighted_points = 0.0
        weighted_points = 0.0
        for result in dimensions:
            if result.get("status") != "scored":
                continue
            submitted_points = (
                (float(result["submitted_score"]) - minimum) / (maximum - minimum)
            ) * float(result["weight"])
            adjusted_points = (
                (float(result["score"]) - minimum) / (maximum - minimum)
            ) * float(result["weight"])
            submitted_weighted_points += submitted_points
            weighted_points += adjusted_points
            result["weighted_points"] = round(adjusted_points, 3)

        quality_floor_failures: list[dict[str, Any]] = []
        submitted_quality_floor_failures: list[dict[str, Any]] = []
        minimum_scores = case_definition.get("minimum_scores", {})
        if not isinstance(minimum_scores, dict):
            raise ScorecardError(f"Case {case_id}.minimum_scores must be an object")
        for dimension_id, required_score in minimum_scores.items():
            if dimension_id not in dimension_results:
                raise ScorecardError(
                    f"Case {case_id} requires unknown dimension: {dimension_id}"
                )
            if (
                isinstance(required_score, bool)
                or not isinstance(required_score, (int, float))
                or not minimum <= required_score <= maximum
            ):
                raise ScorecardError(
                    f"Case {case_id}.minimum_scores.{dimension_id} must be between "
                    f"{minimum} and {maximum}"
                )
            result = dimension_results[dimension_id]
            actual_score = result.get("score") if result.get("status") == "scored" else None
            submitted_actual_score = (
                result.get("submitted_score") if result.get("status") == "scored" else None
            )
            if actual_score is None or actual_score < required_score:
                quality_floor_failures.append(
                    {
                        "id": dimension_id,
                        "minimum_score": required_score,
                        "actual_score": actual_score,
                        "status": result.get("status"),
                    }
                )
            if submitted_actual_score is None or submitted_actual_score < required_score:
                submitted_quality_floor_failures.append(
                    {
                        "id": dimension_id,
                        "minimum_score": required_score,
                        "actual_score": submitted_actual_score,
                        "status": result.get("status"),
                    }
                )
        builder_quality_floor_failures: list[dict[str, Any]] = []
        external_deferred_quality_floors: list[dict[str, Any]] = []
        for failure in submitted_quality_floor_failures:
            dimension_id = failure["id"]
            submitted_actual = failure["actual_score"]
            pending_caps: list[dict[str, Any]] = []
            for rule in cap_rules:
                gate_id = rule["gate"]
                gate_result = gate_results.get(gate_id)
                statuses = rule.get("statuses", ["fail", "not_tested"])
                cap = rule["dimensions"].get(dimension_id)
                if (
                    gate_result is not None
                    and gate_result["acceptance_owner"] != "builder"
                    and gate_result["status"] == "not_tested"
                    and "not_tested" in statuses
                    and isinstance(cap, (int, float))
                    and not isinstance(cap, bool)
                ):
                    pending_caps.append({"gate": gate_id, "cap": cap})
            pre_external_floor = max(
                (float(item["cap"]) for item in pending_caps),
                default=None,
            )
            if (
                pre_external_floor is not None
                and isinstance(submitted_actual, (int, float))
                and not isinstance(submitted_actual, bool)
                and float(submitted_actual) >= pre_external_floor
            ):
                external_deferred_quality_floors.append(
                    {
                        **failure,
                        "pre_external_floor": pre_external_floor,
                        "pending_external_gates": [item["gate"] for item in pending_caps],
                    }
                )
            else:
                builder_quality_floor_failures.append(failure)
        blocking = blocking or bool(quality_floor_failures)

        submitted_score_100 = round(submitted_weighted_points / active_weight * 100.0, 2)
        score_100 = round(weighted_points / active_weight * 100.0, 2)
        thresholds = rubric.get("thresholds", {})
        if blocking:
            verdict = "blocked"
        elif score_100 >= thresholds.get("pass", 85):
            verdict = "pass"
        elif score_100 >= thresholds.get("conditional", 70):
            verdict = "conditional"
        else:
            verdict = "fail"

        builder_unresolved_gates = [
            gate["id"]
            for gate in gates
            if gate["acceptance_owner"] == "builder" and gate["status"] != "pass"
        ]
        external_failed_gates = [
            gate["id"]
            for gate in gates
            if gate["acceptance_owner"] != "builder" and gate["status"] == "fail"
        ]
        external_pending_gates = [
            gate["id"]
            for gate in gates
            if gate["acceptance_owner"] != "builder" and gate["status"] == "not_tested"
        ]
        builder_quality_ready = (
            not builder_quality_floor_failures
            and submitted_score_100 >= thresholds.get("pass", 85)
        )
        if verdict == "pass":
            responsibility_status = "publication_certified"
        elif (
            not builder_unresolved_gates
            and not external_failed_gates
            and builder_quality_ready
        ):
            responsibility_status = "ready_for_human_test"
        else:
            responsibility_status = "builder_work_remaining"

        baseline_score = None
        if args.baseline:
            baseline = read_json(args.baseline, "baseline")
            if baseline.get("case_id") != case_id:
                raise ScorecardError("baseline.case_id does not match --case")
            if isinstance(baseline.get("score_100"), (int, float)):
                baseline_score = float(baseline["score_100"])
        report = {
            "schema_version": 1,
            "case_id": case_id,
            "component_cases": selected_cases,
            "case": case_definition,
            "verdict": verdict,
            "score_100": score_100,
            "submitted_score_100": submitted_score_100,
            "score_caps_applied": score_caps_applied,
            "baseline_score_100": baseline_score,
            "delta": round(score_100 - baseline_score, 2) if baseline_score is not None else None,
            "blocking_gate_count": sum(gate["status"] != "pass" for gate in gates),
            "gate_validation_failure_count": sum(
                len(gate["validation_failures"]) for gate in gates if gate["submitted_status"] == "pass"
            ),
            "quality_floor_failure_count": len(quality_floor_failures),
            "quality_floor_failures": quality_floor_failures,
            "submitted_quality_floor_failure_count": len(submitted_quality_floor_failures),
            "submitted_quality_floor_failures": submitted_quality_floor_failures,
            "builder_quality_floor_failure_count": len(builder_quality_floor_failures),
            "builder_quality_floor_failures": builder_quality_floor_failures,
            "external_deferred_quality_floor_count": len(external_deferred_quality_floors),
            "external_deferred_quality_floors": external_deferred_quality_floors,
            "responsibility_status": responsibility_status,
            "builder_completion_status": (
                "complete"
                if responsibility_status in {"ready_for_human_test", "publication_certified"}
                else "incomplete"
            ),
            "publication_status": (
                "certified" if responsibility_status == "publication_certified" else "not_certified"
            ),
            "builder_owned_unresolved_gate_count": len(builder_unresolved_gates),
            "builder_owned_unresolved_gates": builder_unresolved_gates,
            "external_pending_gate_count": len(external_pending_gates),
            "external_pending_gates": external_pending_gates,
            "external_failed_gate_count": len(external_failed_gates),
            "external_failed_gates": external_failed_gates,
            "gates": gates,
            "dimensions": dimensions,
            "warnings": warnings,
            "artifact_root": str(artifact_root),
            "run_metadata": evidence.get("run_metadata", {}),
            "limitations": evidence.get("limitations", []),
            "acceptance_owner_definitions": owner_definitions,
            "optional_user_preference_policy": rubric.get("optional_user_preference_policy"),
            "responsibility_status_policy": rubric.get("responsibility_status_policy"),
        }
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"[RESULT] case={case_id} verdict={verdict} "
            f"responsibility={responsibility_status} score={score_100:.2f}/100 "
            f"submitted={submitted_score_100:.2f}/100 caps={len(score_caps_applied)} "
            f"blocking_gates={report['blocking_gate_count']} "
            f"builder_unresolved={report['builder_owned_unresolved_gate_count']} "
            f"external_pending={report['external_pending_gate_count']} "
            f"gate_validation_failures={report['gate_validation_failure_count']} "
            f"quality_floor_failures={report['quality_floor_failure_count']}"
        )
        if not args.summary:
            for gate in gates:
                submitted = (
                    f" submitted={gate['submitted_status']}"
                    if gate["submitted_status"] != gate["status"]
                    else ""
                )
                print(
                    f"[GATE {gate['status'].upper()}] {gate['id']} "
                    f"owner={gate['acceptance_owner']}{submitted}"
                )
                for failure in gate["validation_failures"]:
                    print(f"[ARTIFACT FAIL] gate={gate['id']} {failure}")
            for dimension in dimensions:
                if dimension["status"] == "scored":
                    submitted = dimension["submitted_score"]
                    suffix = f" submitted={submitted}" if submitted != dimension["score"] else ""
                    print(
                        f"[SCORE] {dimension['id']}={dimension['score']}/{maximum} "
                        f"weight={dimension['weight']}{suffix}"
                    )
                else:
                    print(f"[N/A] {dimension['id']}")
            for cap in score_caps_applied:
                print(
                    f"[CAP] gate={cap['gate']} status={cap['gate_status']} "
                    f"dimension={cap['dimension']} {cap['before']}->{cap['after']}"
                )
            for failure in quality_floor_failures:
                print(
                    f"[FLOOR FAIL] {failure['id']} actual={failure['actual_score']} "
                    f"required={failure['minimum_score']}"
                )
            for warning in warnings:
                print(f"[WARN] {warning}")
        return 1 if verdict in {"blocked", "fail"} else 0
    except ScorecardError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
