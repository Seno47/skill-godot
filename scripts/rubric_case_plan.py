#!/usr/bin/env python3
"""Emit the exact fail-closed gate plan for one or more rubric cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from rubric_case_composer import CaseCompositionError, gate_applies, resolve_case_selector


class PlanError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan a single or hybrid Godot rubric case.")
    parser.add_argument("--rubric", required=True)
    parser.add_argument("--case", required=True, dest="case_id")
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise PlanError(f"rubric not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanError(f"could not read rubric {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PlanError("rubric root must be an object")
    return data


def make_plan(rubric: dict[str, Any], selector: str) -> dict[str, Any]:
    try:
        case_id, component_cases, definition = resolve_case_selector(rubric, selector)
    except CaseCompositionError as exc:
        raise PlanError(str(exc)) from exc
    owner_default = rubric.get("acceptance_owner_default", "builder")
    gates: list[dict[str, Any]] = []
    for gate in rubric.get("blocking_gates", []):
        if not isinstance(gate, dict):
            raise PlanError("blocking gate entries must be objects")
        try:
            applies = gate_applies(gate, component_cases)
        except CaseCompositionError as exc:
            raise PlanError(str(exc)) from exc
        if not applies:
            continue
        gate_id = gate.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            raise PlanError("applicable gate has no ID")
        requirements = gate.get("artifact_requirements", {})
        gates.append(
            {
                "id": gate_id,
                "owner": gate.get("acceptance_owner", owner_default),
                "minimum_artifacts": requirements.get("minimum_by_kind", {}),
                "required_states": sorted(requirements.get("required_states", {})),
            }
        )
    owner_counts: dict[str, int] = {}
    for gate in gates:
        owner_counts[gate["owner"]] = owner_counts.get(gate["owner"], 0) + 1
    return {
        "schema_version": 1,
        "case_id": case_id,
        "component_cases": component_cases,
        "minimum_scores": definition.get("minimum_scores", {}),
        "focus": definition.get("focus", []),
        "gate_count": len(gates),
        "owner_counts": owner_counts,
        "gates": gates,
    }


def main() -> int:
    args = parse_args()
    try:
        plan = make_plan(read_json(args.rubric), args.case_id)
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"[PASS] case-plan id={plan['case_id']} components={len(plan['component_cases'])} "
            f"gates={plan['gate_count']} owners={json.dumps(plan['owner_counts'], sort_keys=True)}"
        )
        if not args.summary:
            for gate in plan["gates"]:
                print(f"[GATE] {gate['id']} owner={gate['owner']}")
        return 0
    except PlanError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[ERROR] output failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
