#!/usr/bin/env python3
"""Audit remote-config, telemetry queue, consent, and rollback traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {"online_valid", "offline_default", "timeout", "malformed", "stale", "rollback", "queue_overflow", "duplicate_retry", "opt_out", "deletion", "environment_mismatch"}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit LiveOps evidence.")
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
    integer(contract.get("config_schema_version"), "config_schema_version", 1)
    default_digest = text(contract.get("default_config_digest"), "default_config_digest")
    max_queue = integer(contract.get("maximum_queue_events"), "maximum_queue_events", 1)
    required = strings(contract.get("required_scenarios"), "required_scenarios")
    if not required:
        raise ContractError("required_scenarios must not be empty")
    unknown = sorted(required - ALLOWED_SCENARIOS)
    if unknown:
        raise ContractError(f"unknown required scenarios: {', '.join(unknown)}")
    forbidden = strings(contract.get("forbidden_fields"), "forbidden_fields")
    if boolean(contract.get("secrets_embedded"), "secrets_embedded"):
        raise ContractError("client contract embeds service secrets")

    errors: list[str] = []
    scenarios: set[str] = set()
    seen_ids: set[str] = set()
    traces = array(model.get("traces"), "traces")
    for index, raw in enumerate(traces):
        trace = obj(raw, f"traces[{index}]")
        trace_id = text(trace.get("id"), f"traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
        scenarios.add(scenario)
        if scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown scenario {scenario}")
        if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
            errors.append(f"trace {trace_id} is not target-build evidence")
        if text(trace.get("result"), f"trace {trace_id}.result") != "pass":
            errors.append(f"trace {trace_id} did not pass")
        if not boolean(trace.get("safe_state"), f"trace {trace_id}.safe_state"):
            errors.append(f"trace {trace_id} leaves an unsafe state")
        if integer(trace.get("duplicate_rewards"), f"trace {trace_id}.duplicate_rewards"):
            errors.append(f"trace {trace_id} duplicates rewards")
        sent = strings(trace.get("forbidden_fields_sent"), f"trace {trace_id}.forbidden_fields_sent")
        exposed = sorted(sent & forbidden)
        if exposed:
            errors.append(f"trace {trace_id} sends forbidden fields: {', '.join(exposed)}")
        if not boolean(trace.get("consent_respected"), f"trace {trace_id}.consent_respected"):
            errors.append(f"trace {trace_id} violates consent")
        queue_size = integer(trace.get("queue_size"), f"trace {trace_id}.queue_size")
        if queue_size > max_queue:
            errors.append(f"trace {trace_id} queue {queue_size} exceeds {max_queue}")
        if scenario in {"offline_default", "timeout", "malformed", "stale"} and text(
            trace.get("default_digest"), f"trace {trace_id}.default_digest"
        ) != default_digest:
            errors.append(f"trace {trace_id} does not use safe default config")
        if scenario == "rollback" and not boolean(
            trace.get("rollback_completed"), f"trace {trace_id}.rollback_completed"
        ):
            errors.append(f"trace {trace_id} does not complete rollback")
        if scenario == "queue_overflow" and integer(
            trace.get("events_dropped_by_policy"), f"trace {trace_id}.events_dropped_by_policy"
        ) < 1:
            errors.append(f"trace {trace_id} has no bounded overflow policy")
        if scenario == "duplicate_retry" and not boolean(
            trace.get("idempotent_event_ids"), f"trace {trace_id}.idempotent_event_ids"
        ):
            errors.append(f"trace {trace_id} retry is not idempotent")
        if scenario == "opt_out" and integer(
            trace.get("events_sent_after_opt_out"), f"trace {trace_id}.events_sent_after_opt_out"
        ):
            errors.append(f"trace {trace_id} sends events after opt-out")
        if scenario == "deletion" and not boolean(
            trace.get("deletion_completed"), f"trace {trace_id}.deletion_completed"
        ):
            errors.append(f"trace {trace_id} does not complete deletion")
        if scenario == "environment_mismatch" and not boolean(
            trace.get("request_blocked"), f"trace {trace_id}.request_blocked"
        ):
            errors.append(f"trace {trace_id} accepts environment mismatch")

    missing = sorted(required - scenarios)
    if missing:
        errors.append(f"missing required scenarios: {', '.join(missing)}")
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
        print(f"[{marker}] liveops id={report['contract_id']} traces={report['trace_count']} errors={len(report['errors'])}")
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
