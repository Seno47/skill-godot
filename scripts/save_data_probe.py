#!/usr/bin/env python3
"""Audit versioned save, migration, recovery, and cloud-conflict traces."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {
    "clean_create",
    "round_trip",
    "interrupted_write",
    "corrupt_primary",
    "migration",
    "duplicate_load",
    "reset",
    "cloud_conflict",
}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit save-data integrity evidence.")
    parser.add_argument("--model", required=True, help="Save-data contract JSON.")
    parser.add_argument("--json-output", help="Optional complete audit report JSON.")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def read_model(value: str) -> dict[str, Any]:
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


def object_value(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def list_value(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    return value


def text_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def int_value(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def decimal_value(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ContractError(f"{label} must be numeric")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ContractError(f"{label} is not numeric") from exc
    if not result.is_finite() or result < 0:
        raise ContractError(f"{label} must be finite and >= 0")
    return result


def bool_value(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be boolean")
    return value


def string_set(value: Any, label: str) -> set[str]:
    items = list_value(value, label)
    result: set[str] = set()
    for index, item in enumerate(items):
        result.add(text_value(item, f"{label}[{index}]"))
    if len(result) != len(items):
        raise ContractError(f"{label} contains duplicates")
    return result


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text_value(model.get("contract_id"), "contract_id")
    text_value(model.get("build_id"), "build_id")
    contract = object_value(model.get("contract"), "contract")
    current = int_value(contract.get("current_save_version"), "current_save_version", 1)
    supported_values = list_value(contract.get("supported_source_versions"), "supported_source_versions")
    supported = {
        int_value(item, f"supported_source_versions[{index}]", 1)
        for index, item in enumerate(supported_values)
    }
    if len(supported) != len(supported_values):
        raise ContractError("supported_source_versions contains duplicates")
    required_scenarios = string_set(contract.get("required_scenarios"), "required_scenarios")
    unknown = sorted(required_scenarios - ALLOWED_SCENARIOS)
    if unknown:
        raise ContractError(f"unknown required scenarios: {', '.join(unknown)}")
    critical_fields = string_set(contract.get("critical_fields"), "critical_fields")
    if not critical_fields:
        raise ContractError("critical_fields must not be empty")
    atomic_commit = bool_value(contract.get("atomic_commit"), "atomic_commit")
    backup_generations = int_value(contract.get("backup_generations"), "backup_generations")
    text_value(contract.get("corruption_policy"), "corruption_policy")
    text_value(contract.get("future_version_policy"), "future_version_policy")
    cloud_policy = text_value(contract.get("cloud_conflict_policy"), "cloud_conflict_policy")
    max_save_ms = decimal_value(contract.get("max_save_ms"), "max_save_ms")
    max_load_ms = decimal_value(contract.get("max_load_ms"), "max_load_ms")
    max_save_bytes = int_value(contract.get("max_save_bytes"), "max_save_bytes", 1)

    errors: list[str] = []
    if current not in supported:
        errors.append("current_save_version is absent from supported_source_versions")
    if atomic_commit and backup_generations < 1:
        errors.append("atomic material saves require at least one backup generation")

    traces = list_value(model.get("traces"), "traces")
    if not traces:
        raise ContractError("traces must not be empty")
    seen_ids: set[str] = set()
    scenarios: set[str] = set()
    migration_sources: set[int] = set()
    for index, raw_trace in enumerate(traces):
        trace = object_value(raw_trace, f"traces[{index}]")
        trace_id = text_value(trace.get("id"), f"traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        scenario = text_value(trace.get("scenario"), f"trace {trace_id}.scenario")
        if scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown scenario {scenario}")
        scenarios.add(scenario)
        source = text_value(trace.get("source"), f"trace {trace_id}.source")
        if source not in {"target_build", "production_serializer_fixture"}:
            errors.append(f"trace {trace_id} source is not production-path evidence")
        if text_value(trace.get("result"), f"trace {trace_id}.result") != "pass":
            errors.append(f"trace {trace_id} did not pass")
        source_version = int_value(trace.get("source_version"), f"trace {trace_id}.source_version")
        result_version = int_value(trace.get("result_version"), f"trace {trace_id}.result_version", 1)
        if result_version != current:
            errors.append(f"trace {trace_id} result version {result_version} != current {current}")
        expected_digest = text_value(trace.get("expected_digest"), f"trace {trace_id}.expected_digest")
        actual_digest = text_value(trace.get("actual_digest"), f"trace {trace_id}.actual_digest")
        if expected_digest != actual_digest:
            errors.append(f"trace {trace_id} round-trip digest mismatch")
        lost = string_set(trace.get("critical_fields_lost", []), f"trace {trace_id}.critical_fields_lost")
        if lost:
            errors.append(f"trace {trace_id} loses critical fields: {', '.join(sorted(lost))}")
        temporary = int_value(
            trace.get("temporary_files_remaining", 0),
            f"trace {trace_id}.temporary_files_remaining",
        )
        if atomic_commit and temporary:
            errors.append(f"trace {trace_id} leaves {temporary} temporary files")
        save_bytes = int_value(trace.get("save_bytes", 1), f"trace {trace_id}.save_bytes", 1)
        if save_bytes > max_save_bytes:
            errors.append(f"trace {trace_id} save size {save_bytes} exceeds {max_save_bytes}")
        if "save_ms" in trace and decimal_value(trace["save_ms"], f"trace {trace_id}.save_ms") > max_save_ms:
            errors.append(f"trace {trace_id} exceeds save-time budget")
        if "load_ms" in trace and decimal_value(trace["load_ms"], f"trace {trace_id}.load_ms") > max_load_ms:
            errors.append(f"trace {trace_id} exceeds load-time budget")

        if scenario in {"clean_create", "round_trip"}:
            if not bool_value(trace.get("write_completed"), f"trace {trace_id}.write_completed"):
                errors.append(f"trace {trace_id} did not complete its write")
            if not bool_value(trace.get("primary_valid"), f"trace {trace_id}.primary_valid"):
                errors.append(f"trace {trace_id} primary is invalid")
        elif scenario == "interrupted_write":
            if bool_value(trace.get("write_completed"), f"trace {trace_id}.write_completed"):
                errors.append(f"trace {trace_id} is not an interrupted write")
            if not bool_value(trace.get("fallback_used"), f"trace {trace_id}.fallback_used"):
                errors.append(f"trace {trace_id} does not recover after interruption")
            if not bool_value(trace.get("primary_valid"), f"trace {trace_id}.primary_valid"):
                errors.append(f"trace {trace_id} destroyed the previous primary")
        elif scenario == "corrupt_primary":
            if bool_value(trace.get("primary_valid"), f"trace {trace_id}.primary_valid"):
                errors.append(f"trace {trace_id} does not exercise corrupt primary data")
            if not bool_value(trace.get("backup_valid"), f"trace {trace_id}.backup_valid"):
                errors.append(f"trace {trace_id} has no valid backup")
            if not bool_value(trace.get("fallback_used"), f"trace {trace_id}.fallback_used"):
                errors.append(f"trace {trace_id} does not use recovery")
            if bool_value(trace.get("source_overwritten"), f"trace {trace_id}.source_overwritten"):
                errors.append(f"trace {trace_id} overwrites the corrupt source before review/recovery")
        elif scenario == "migration":
            migration_sources.add(source_version)
            if source_version >= current:
                errors.append(f"trace {trace_id} is not an older-version migration")
            steps = list_value(trace.get("migration_steps"), f"trace {trace_id}.migration_steps")
            if not steps:
                errors.append(f"trace {trace_id} has no migration steps")
            if bool_value(trace.get("source_overwritten"), f"trace {trace_id}.source_overwritten"):
                errors.append(f"trace {trace_id} overwrites its migration source")
        elif scenario == "duplicate_load":
            if int_value(trace.get("load_attempts"), f"trace {trace_id}.load_attempts", 2) < 2:
                errors.append(f"trace {trace_id} does not repeat load")
            if int_value(trace.get("durable_mutations"), f"trace {trace_id}.durable_mutations") != 1:
                errors.append(f"trace {trace_id} is not idempotent")
            if int_value(trace.get("duplicate_rewards"), f"trace {trace_id}.duplicate_rewards") != 0:
                errors.append(f"trace {trace_id} duplicates rewards")
        elif scenario == "reset":
            if int_value(trace.get("unrelated_slots_changed"), f"trace {trace_id}.unrelated_slots_changed") != 0:
                errors.append(f"trace {trace_id} changes unrelated slots")
        elif scenario == "cloud_conflict":
            if not cloud_policy:
                errors.append("cloud conflict scenario has no policy")
            int_value(trace.get("winning_revision"), f"trace {trace_id}.winning_revision", 1)
            if not bool_value(trace.get("losing_copy_preserved"), f"trace {trace_id}.losing_copy_preserved"):
                errors.append(f"trace {trace_id} destroys the losing conflict copy")
            if int_value(trace.get("duplicate_rewards"), f"trace {trace_id}.duplicate_rewards") != 0:
                errors.append(f"trace {trace_id} duplicates cloud progress")

    missing_scenarios = sorted(required_scenarios - scenarios)
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    required_migrations = {version for version in supported if version < current}
    missing_migrations = sorted(required_migrations - migration_sources)
    if missing_migrations:
        errors.append(
            "missing migration traces from versions: " + ", ".join(map(str, missing_migrations))
        )
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "current_save_version": current,
        "trace_count": len(traces),
        "migration_source_count": len(migration_sources),
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit(read_model(args.model))
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(
            f"[{marker}] save-data id={report['contract_id']} traces={report['trace_count']} "
            f"migrations={report['migration_source_count']} errors={len(report['errors'])}"
        )
        if report["errors"]:
            for error in report["errors"]:
                print(f"[ERROR] {error}")
        elif not args.summary:
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
