#!/usr/bin/env python3
"""Audit replay, ghost, spectator, and divergence traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {"record_playback", "render_cap", "seek", "save_resume", "corrupt", "old_version", "spectator_catchup", "ghost_isolation"}
ALLOWED_MODES = {"replay", "ghost", "spectator"}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit replay evidence.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ContractError(f"model not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"could not read model {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError("model root must be an object")
    return data


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be boolean")
    return value


def strings(value: Any, label: str) -> set[str]:
    values = array(value, label)
    result = {text(item, f"{label}[{index}]") for index, item in enumerate(values)}
    if len(result) != len(values):
        raise ContractError(f"{label} contains duplicates")
    return result


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    text(model.get("build_id"), "build_id")
    contract = obj(model.get("contract"), "contract")
    integer(contract.get("replay_schema_version"), "replay_schema_version", 1)
    integer(contract.get("tick_rate"), "tick_rate", 1)
    text(contract.get("recorded_authority"), "recorded_authority")
    physics_input_only = boolean(contract.get("physics_input_only_claim"), "physics_input_only_claim")
    if physics_input_only and not boolean(
        contract.get("cross_machine_determinism_proved", False),
        "cross_machine_determinism_proved",
    ):
        raise ContractError("physics input-only replay requires proved cross-machine determinism")
    modes_required = strings(contract.get("required_modes"), "required_modes")
    scenarios_required = strings(contract.get("required_scenarios"), "required_scenarios")
    if not modes_required or not scenarios_required:
        raise ContractError("required_modes and required_scenarios must not be empty")
    unknown_modes = sorted(modes_required - ALLOWED_MODES)
    unknown_scenarios = sorted(scenarios_required - ALLOWED_SCENARIOS)
    if unknown_modes or unknown_scenarios:
        raise ContractError("contract contains unknown modes or scenarios")
    max_divergences = integer(contract.get("max_divergences"), "max_divergences")

    errors: list[str] = []
    seen_ids: set[str] = set()
    modes: set[str] = set()
    scenarios: set[str] = set()
    traces = array(model.get("traces"), "traces")
    for index, raw in enumerate(traces):
        trace = obj(raw, f"traces[{index}]")
        trace_id = text(trace.get("id"), f"traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        mode = text(trace.get("mode"), f"trace {trace_id}.mode")
        scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
        modes.add(mode)
        scenarios.add(scenario)
        if mode not in ALLOWED_MODES or scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown mode/scenario")
        if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
            errors.append(f"trace {trace_id} is not target-build evidence")
        if text(trace.get("result"), f"trace {trace_id}.result") != "pass":
            errors.append(f"trace {trace_id} did not pass")
        expected = text(trace.get("expected_digest"), f"trace {trace_id}.expected_digest")
        actual = text(trace.get("actual_digest"), f"trace {trace_id}.actual_digest")
        if expected != actual:
            errors.append(f"trace {trace_id} state digest diverges")
        divergences = integer(trace.get("divergences"), f"trace {trace_id}.divergences")
        if divergences > max_divergences:
            errors.append(f"trace {trace_id} divergence count {divergences} exceeds {max_divergences}")
        if not boolean(trace.get("external_outcomes_recorded"), f"trace {trace_id}.external_outcomes_recorded"):
            errors.append(f"trace {trace_id} omits external outcomes")
        if not boolean(trace.get("result_state_equal"), f"trace {trace_id}.result_state_equal"):
            errors.append(f"trace {trace_id} result state differs")
        if scenario in {"corrupt", "old_version"} and not boolean(
            trace.get("rejected_safely"), f"trace {trace_id}.rejected_safely"
        ):
            errors.append(f"trace {trace_id} does not reject incompatible data safely")
        if scenario == "ghost_isolation" and integer(
            trace.get("ghost_collision_events"), f"trace {trace_id}.ghost_collision_events"
        ):
            errors.append(f"trace {trace_id} ghost affects collision")

    missing_modes = sorted(modes_required - modes)
    missing_scenarios = sorted(scenarios_required - scenarios)
    if missing_modes:
        errors.append(f"missing required modes: {', '.join(missing_modes)}")
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    return {"status": "pass" if not errors else "fail", "contract_id": contract_id, "trace_count": len(traces), "errors": errors}


def main() -> int:
    args = parse_args()
    try:
        report = audit(read_json(args.model))
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(f"[{marker}] replay id={report['contract_id']} traces={report['trace_count']} errors={len(report['errors'])}")
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
