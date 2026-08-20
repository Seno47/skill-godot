#!/usr/bin/env python3
"""Validate and score evidence from independent Godot skill evaluations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


class ScorecardError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a Godot skill evaluation against a stable rubric.")
    parser.add_argument("--rubric", required=True, help="Rubric JSON, normally evals/rubric.json.")
    parser.add_argument("--evidence", required=True, help="Evaluation evidence JSON.")
    parser.add_argument("--case", required=True, dest="case_id", help="Case ID from the rubric.")
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


def main() -> int:
    args = parse_args()
    try:
        rubric = read_json(args.rubric, "rubric")
        evidence = read_json(args.evidence, "evidence")
        if rubric.get("schema_version") != 1 or evidence.get("schema_version") != 1:
            raise ScorecardError("rubric and evidence schema_version must be 1")
        cases = {item.get("id"): item for item in rubric.get("cases", []) if isinstance(item, dict)}
        if args.case_id not in cases:
            raise ScorecardError(f"Unknown case ID: {args.case_id}")
        if evidence.get("case_id") != args.case_id:
            raise ScorecardError("evidence.case_id does not match --case")

        gate_evidence = evidence.get("gates")
        score_evidence = evidence.get("scores")
        if not isinstance(gate_evidence, dict) or not isinstance(score_evidence, dict):
            raise ScorecardError("evidence.gates and evidence.scores must be objects")

        gates: list[dict[str, Any]] = []
        blocking = False
        for definition in rubric.get("blocking_gates", []):
            gate_id = definition.get("id")
            case_filter = definition.get("cases")
            if case_filter is not None:
                if (
                    not isinstance(case_filter, list)
                    or not case_filter
                    or any(not isinstance(item, str) or not item for item in case_filter)
                ):
                    raise ScorecardError(f"Gate {gate_id}.cases must be a non-empty list of case IDs")
                if args.case_id not in case_filter:
                    continue
            value = gate_evidence.get(gate_id)
            if not isinstance(value, dict):
                raise ScorecardError(f"Missing gate evidence: {gate_id}")
            status = value.get("status")
            if status not in {"pass", "fail", "not_tested"}:
                raise ScorecardError(f"Gate {gate_id}.status must be pass, fail, or not_tested")
            artifacts = evidence_items(value.get("evidence", []), f"gate {gate_id}.evidence")
            if not artifacts:
                raise ScorecardError(f"Gate {gate_id} requires at least one evidence artifact or limitation record")
            blocking = blocking or status != "pass"
            gates.append(
                {
                    "id": gate_id,
                    "status": status,
                    "evidence": artifacts,
                    "description": definition.get("description"),
                }
            )

        scale = rubric.get("score_scale", {})
        minimum, maximum = scale.get("min", 0), scale.get("max", 4)
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)) or maximum <= minimum:
            raise ScorecardError("Invalid rubric score scale")
        dimensions: list[dict[str, Any]] = []
        weighted_points = 0.0
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
            weighted_points += ((float(score) - minimum) / (maximum - minimum)) * float(weight)
            active_weight += float(weight)
            dimensions.append(
                {
                    "id": dimension_id,
                    "status": "scored",
                    "score": score,
                    "weight": weight,
                    "weighted_points": round(((float(score) - minimum) / (maximum - minimum)) * float(weight), 3),
                    "evidence": artifacts,
                    "notes": value.get("notes"),
                }
            )
        if active_weight <= 0:
            raise ScorecardError("No active scored dimensions")

        quality_floor_failures: list[dict[str, Any]] = []
        minimum_scores = cases[args.case_id].get("minimum_scores", {})
        if not isinstance(minimum_scores, dict):
            raise ScorecardError(f"Case {args.case_id}.minimum_scores must be an object")
        dimension_results = {item["id"]: item for item in dimensions}
        for dimension_id, required_score in minimum_scores.items():
            if dimension_id not in dimension_results:
                raise ScorecardError(
                    f"Case {args.case_id} requires unknown dimension: {dimension_id}"
                )
            if (
                isinstance(required_score, bool)
                or not isinstance(required_score, (int, float))
                or not minimum <= required_score <= maximum
            ):
                raise ScorecardError(
                    f"Case {args.case_id}.minimum_scores.{dimension_id} must be between "
                    f"{minimum} and {maximum}"
                )
            result = dimension_results[dimension_id]
            actual_score = result.get("score") if result.get("status") == "scored" else None
            if actual_score is None or actual_score < required_score:
                quality_floor_failures.append(
                    {
                        "id": dimension_id,
                        "minimum_score": required_score,
                        "actual_score": actual_score,
                        "status": result.get("status"),
                    }
                )
        blocking = blocking or bool(quality_floor_failures)

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

        baseline_score = None
        if args.baseline:
            baseline = read_json(args.baseline, "baseline")
            if baseline.get("case_id") != args.case_id:
                raise ScorecardError("baseline.case_id does not match --case")
            if isinstance(baseline.get("score_100"), (int, float)):
                baseline_score = float(baseline["score_100"])
        report = {
            "schema_version": 1,
            "case_id": args.case_id,
            "case": cases[args.case_id],
            "verdict": verdict,
            "score_100": score_100,
            "baseline_score_100": baseline_score,
            "delta": round(score_100 - baseline_score, 2) if baseline_score is not None else None,
            "blocking_gate_count": sum(gate["status"] != "pass" for gate in gates),
            "quality_floor_failure_count": len(quality_floor_failures),
            "quality_floor_failures": quality_floor_failures,
            "gates": gates,
            "dimensions": dimensions,
            "warnings": warnings,
            "run_metadata": evidence.get("run_metadata", {}),
            "limitations": evidence.get("limitations", []),
        }
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"[RESULT] case={args.case_id} verdict={verdict} score={score_100:.2f}/100 "
            f"blocking_gates={report['blocking_gate_count']} "
            f"quality_floor_failures={report['quality_floor_failure_count']}"
        )
        if not args.summary:
            for gate in gates:
                print(f"[GATE {gate['status'].upper()}] {gate['id']}")
            for dimension in dimensions:
                if dimension["status"] == "scored":
                    print(f"[SCORE] {dimension['id']}={dimension['score']}/{maximum} weight={dimension['weight']}")
                else:
                    print(f"[N/A] {dimension['id']}")
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
