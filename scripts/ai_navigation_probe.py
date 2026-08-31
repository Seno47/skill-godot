#!/usr/bin/env python3
"""Audit production AI perception, navigation, fairness, and capacity traces."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {
    "spawn_idle",
    "perception_boundary",
    "chase_route",
    "blocked_replan",
    "repeated_recovery",
    "unreachable_target",
    "crowd_avoidance",
    "combat_telegraph",
    "disengage_return",
    "pause_resume",
    "capacity",
}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit AI and navigation evidence.")
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


def number(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ContractError(f"{label} must be numeric")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ContractError(f"{label} is not numeric") from exc
    if not result.is_finite() or result < 0:
        raise ContractError(f"{label} must be finite and >= 0")
    return result


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
    required_archetypes = strings(contract.get("required_archetypes"), "required_archetypes")
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios")
    unknown = sorted(required_scenarios - ALLOWED_SCENARIOS)
    if unknown:
        raise ContractError(f"unknown required scenarios: {', '.join(unknown)}")
    forbidden = strings(contract.get("forbidden_information"), "forbidden_information")
    max_stuck = integer(contract.get("max_stuck_events"), "max_stuck_events")
    max_deadlocks = integer(contract.get("max_deadlocks"), "max_deadlocks")
    max_path = number(contract.get("max_path_ms"), "max_path_ms")
    max_replan = number(contract.get("max_replan_ms"), "max_replan_ms")
    max_recovery_attempts = integer(
        contract.get("max_recovery_attempts"), "max_recovery_attempts", 1
    )
    max_same_failed_candidate_retries = integer(
        contract.get("max_same_failed_candidate_retries"),
        "max_same_failed_candidate_retries",
    )
    minimum_recovery_progress = number(
        contract.get("minimum_recovery_progress"), "minimum_recovery_progress"
    )
    min_telegraph = number(contract.get("minimum_telegraph_ms"), "minimum_telegraph_ms")
    min_reaction = number(contract.get("minimum_reaction_ms"), "minimum_reaction_ms")
    max_tick = number(contract.get("max_capacity_tick_p95_ms"), "max_capacity_tick_p95_ms")
    target_agents = integer(contract.get("target_active_agents"), "target_active_agents", 1)
    max_offscreen = number(
        contract.get("max_offscreen_updates_per_second"),
        "max_offscreen_updates_per_second",
    )

    errors: list[str] = []
    seen_ids: set[str] = set()
    scenarios: set[str] = set()
    archetypes: set[str] = set()
    traces = array(model.get("traces"), "traces")
    if not traces:
        raise ContractError("traces must not be empty")
    for index, raw in enumerate(traces):
        trace = obj(raw, f"traces[{index}]")
        trace_id = text(trace.get("id"), f"traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
        archetype = text(trace.get("archetype"), f"trace {trace_id}.archetype")
        scenarios.add(scenario)
        archetypes.add(archetype)
        if scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown scenario {scenario}")
        if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
            errors.append(f"trace {trace_id} is not target-build evidence")
        if text(trace.get("result"), f"trace {trace_id}.result") != "pass":
            errors.append(f"trace {trace_id} did not pass")
        if not boolean(trace.get("state_transition_valid"), f"trace {trace_id}.state_transition_valid"):
            errors.append(f"trace {trace_id} has an illegal state transition")
        reads = strings(
            trace.get("forbidden_information_read", []),
            f"trace {trace_id}.forbidden_information_read",
        )
        bad_reads = sorted(reads & forbidden)
        if bad_reads:
            errors.append(f"trace {trace_id} reads forbidden information: {', '.join(bad_reads)}")
        stuck = integer(trace.get("stuck_events"), f"trace {trace_id}.stuck_events")
        deadlocks = integer(trace.get("deadlocks"), f"trace {trace_id}.deadlocks")
        if stuck > max_stuck:
            errors.append(f"trace {trace_id} stuck events {stuck} exceed {max_stuck}")
        if deadlocks > max_deadlocks:
            errors.append(f"trace {trace_id} deadlocks {deadlocks} exceed {max_deadlocks}")
        if number(trace.get("path_ms"), f"trace {trace_id}.path_ms") > max_path:
            errors.append(f"trace {trace_id} exceeds path-query budget")

        if scenario == "perception_boundary":
            if not boolean(trace.get("inside_detected"), f"trace {trace_id}.inside_detected"):
                errors.append(f"trace {trace_id} misses inside perception target")
            if boolean(trace.get("outside_detected"), f"trace {trace_id}.outside_detected"):
                errors.append(f"trace {trace_id} detects outside perception range")
            if boolean(trace.get("occluded_detected"), f"trace {trace_id}.occluded_detected"):
                errors.append(f"trace {trace_id} detects an occluded target")
            if number(trace.get("reaction_ms"), f"trace {trace_id}.reaction_ms") < min_reaction:
                errors.append(f"trace {trace_id} reacts faster than declared fairness floor")
        elif scenario in {"chase_route", "crowd_avoidance"}:
            if not boolean(trace.get("route_valid"), f"trace {trace_id}.route_valid"):
                errors.append(f"trace {trace_id} has an invalid route")
        elif scenario == "blocked_replan":
            if not boolean(trace.get("replan_succeeded"), f"trace {trace_id}.replan_succeeded"):
                errors.append(f"trace {trace_id} fails blocked-route replan")
            if number(trace.get("replan_ms"), f"trace {trace_id}.replan_ms") > max_replan:
                errors.append(f"trace {trace_id} exceeds replan budget")
        elif scenario == "repeated_recovery":
            attempts = array(trace.get("recovery_attempts"), f"trace {trace_id}.recovery_attempts")
            if not attempts:
                raise ContractError(f"trace {trace_id}.recovery_attempts must not be empty")
            if len(attempts) > max_recovery_attempts:
                errors.append(
                    f"trace {trace_id} recovery attempts {len(attempts)} exceed "
                    f"{max_recovery_attempts}"
                )
            failed_counts: dict[tuple[str, str], int] = {}
            saw_failure = False
            terminal_outcome = "failed"
            for attempt_index, raw_attempt in enumerate(attempts):
                attempt = obj(
                    raw_attempt,
                    f"trace {trace_id}.recovery_attempts[{attempt_index}]",
                )
                candidate_id = text(
                    attempt.get("candidate_id"),
                    f"trace {trace_id} recovery attempt {attempt_index}.candidate_id",
                )
                environment_revision = text(
                    attempt.get("environment_revision"),
                    f"trace {trace_id} recovery attempt {attempt_index}.environment_revision",
                )
                selection_basis = text(
                    attempt.get("selection_basis"),
                    f"trace {trace_id} recovery attempt {attempt_index}.selection_basis",
                )
                if selection_basis == "stable_instance_id_only":
                    errors.append(
                        f"trace {trace_id} recovery attempt {attempt_index} selects only by stable instance ID"
                    )
                outcome = text(
                    attempt.get("outcome"),
                    f"trace {trace_id} recovery attempt {attempt_index}.outcome",
                )
                if outcome not in {"failed", "recovered", "escalated"}:
                    raise ContractError(
                        f"trace {trace_id} recovery attempt {attempt_index}.outcome is unsupported"
                    )
                progress = number(
                    attempt.get("progress_distance"),
                    f"trace {trace_id} recovery attempt {attempt_index}.progress_distance",
                )
                key = (candidate_id, environment_revision)
                if failed_counts.get(key, 0) > max_same_failed_candidate_retries:
                    errors.append(
                        f"trace {trace_id} repeats failed recovery candidate {candidate_id} "
                        f"without a changed/revalidated environment"
                    )
                if outcome == "failed":
                    saw_failure = True
                    failed_counts[key] = failed_counts.get(key, 0) + 1
                elif outcome == "recovered":
                    if progress < minimum_recovery_progress:
                        errors.append(
                            f"trace {trace_id} claims recovery below the progress floor"
                        )
                    if not boolean(
                        attempt.get("target_progress_resumed"),
                        f"trace {trace_id} recovery attempt {attempt_index}.target_progress_resumed",
                    ):
                        errors.append(
                            f"trace {trace_id} recovery does not resume target progress"
                        )
                else:
                    escalation = text(
                        attempt.get("escalation"),
                        f"trace {trace_id} recovery attempt {attempt_index}.escalation",
                    )
                    if escalation not in {"repath", "backtrack", "safe_reset", "abandon_target"}:
                        errors.append(
                            f"trace {trace_id} uses unsupported recovery escalation {escalation}"
                        )
                if outcome in {"recovered", "escalated"} and attempt_index != len(attempts) - 1:
                    errors.append(
                        f"trace {trace_id} continues attempts after terminal recovery outcome"
                    )
                terminal_outcome = outcome
            if saw_failure and not boolean(
                trace.get("failed_candidate_memory_observed"),
                f"trace {trace_id}.failed_candidate_memory_observed",
            ):
                errors.append(f"trace {trace_id} does not retain failed recovery candidates")
            if terminal_outcome not in {"recovered", "escalated"}:
                errors.append(
                    f"trace {trace_id} exhausts recovery without bounded recovery or escalation"
                )
        elif scenario == "unreachable_target":
            if not boolean(trace.get("unreachable_handled"), f"trace {trace_id}.unreachable_handled"):
                errors.append(f"trace {trace_id} does not handle unreachable target")
            if boolean(trace.get("target_reached"), f"trace {trace_id}.target_reached"):
                errors.append(f"trace {trace_id} falsely reports unreachable target reached")
        elif scenario == "combat_telegraph":
            if number(trace.get("telegraph_ms"), f"trace {trace_id}.telegraph_ms") < min_telegraph:
                errors.append(f"trace {trace_id} telegraph is below declared floor")
            if number(trace.get("reaction_ms"), f"trace {trace_id}.reaction_ms") < min_reaction:
                errors.append(f"trace {trace_id} reaction is below declared floor")
        elif scenario == "disengage_return":
            if not boolean(trace.get("route_valid"), f"trace {trace_id}.route_valid"):
                errors.append(f"trace {trace_id} has an invalid return route")
            if not boolean(
                trace.get("returned_to_valid_state"),
                f"trace {trace_id}.returned_to_valid_state",
            ):
                errors.append(f"trace {trace_id} does not recover after disengage")
        elif scenario == "pause_resume":
            if boolean(
                trace.get("state_advanced_while_paused"),
                f"trace {trace_id}.state_advanced_while_paused",
            ):
                errors.append(f"trace {trace_id} advances while paused")
            if number(trace.get("cooldown_drift_ms"), f"trace {trace_id}.cooldown_drift_ms") != 0:
                errors.append(f"trace {trace_id} drifts cooldown while paused")
        elif scenario == "capacity":
            actors = integer(trace.get("actors"), f"trace {trace_id}.actors", 1)
            if actors < target_agents:
                errors.append(f"trace {trace_id} tests {actors} actors below target {target_agents}")
            if number(
                trace.get("capacity_tick_p95_ms"),
                f"trace {trace_id}.capacity_tick_p95_ms",
            ) > max_tick:
                errors.append(f"trace {trace_id} exceeds capacity tick budget")
            if number(
                trace.get("offscreen_updates_per_second"),
                f"trace {trace_id}.offscreen_updates_per_second",
            ) > max_offscreen:
                errors.append(f"trace {trace_id} exceeds off-screen update budget")

    missing_scenarios = sorted(required_scenarios - scenarios)
    missing_archetypes = sorted(required_archetypes - archetypes)
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    if missing_archetypes:
        errors.append(f"missing required archetypes: {', '.join(missing_archetypes)}")
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "trace_count": len(traces),
        "archetype_count": len(archetypes),
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit(read_json(args.model))
        if args.json_output:
            path = Path(args.json_output).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(
            f"[{marker}] ai-navigation id={report['contract_id']} traces={report['trace_count']} "
            f"archetypes={report['archetype_count']} errors={len(report['errors'])}"
        )
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        if not args.summary and not report["errors"]:
            print(json.dumps(report, indent=2))
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[ERROR] output failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
