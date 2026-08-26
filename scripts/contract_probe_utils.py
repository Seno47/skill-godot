#!/usr/bin/env python3
"""Small dependency-free validators shared by production contract probes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable


class ContractError(RuntimeError):
    pass


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def array(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        suffix = " and not be empty" if nonempty else ""
        raise ContractError(f"{label} must be an array{suffix}")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def number(value: Any, label: str, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
        raise ContractError(f"{label} must be a number >= {minimum}")
    return float(value)


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be boolean")
    return value


def strings(value: Any, label: str, *, nonempty: bool = False) -> set[str]:
    values = array(value, label, nonempty=nonempty)
    result = {text(item, f"{label}[{index}]") for index, item in enumerate(values)}
    if len(result) != len(values):
        raise ContractError(f"{label} contains duplicates")
    return result


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ContractError(f"model not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"could not read model {path}: {exc}") from exc
    return obj(data, "model root")


def contract_header(model: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    build_id = text(model.get("build_id"), "build_id")
    return contract_id, build_id, obj(model.get("contract"), "contract")


def trace_header(
    raw: Any, index: int, seen_ids: set[str]
) -> tuple[dict[str, Any], str, str]:
    trace = obj(raw, f"traces[{index}]")
    trace_id = text(trace.get("id"), f"traces[{index}].id")
    if trace_id in seen_ids:
        raise ContractError(f"duplicate trace ID {trace_id}")
    seen_ids.add(trace_id)
    scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
    return trace, trace_id, scenario


def require_target_pass(trace: dict[str, Any], trace_id: str, errors: list[str]) -> None:
    if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
        errors.append(f"trace {trace_id} is not target-build evidence")
    if text(trace.get("result"), f"trace {trace_id}.result") != "pass":
        errors.append(f"trace {trace_id} did not pass")


def require_true(
    trace: dict[str, Any], key: str, trace_id: str, errors: list[str]
) -> None:
    if not boolean(trace.get(key), f"trace {trace_id}.{key}"):
        errors.append(f"trace {trace_id} does not prove {key}")


def require_zero(
    trace: dict[str, Any], key: str, trace_id: str, errors: list[str]
) -> None:
    if integer(trace.get(key), f"trace {trace_id}.{key}") != 0:
        errors.append(f"trace {trace_id} reports non-zero {key}")


def require_coverage(required: set[str], observed: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(required - observed)
    if missing:
        errors.append(f"missing {label}: {', '.join(missing)}")


def finish_report(
    contract_id: str, traces: list[Any], errors: list[str], **counts: Any
) -> dict[str, Any]:
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "trace_count": len(traces),
        **counts,
        "errors": errors,
    }


def cli_main(label: str, audit: Callable[[dict[str, Any]], dict[str, Any]]) -> int:
    parser = argparse.ArgumentParser(description=f"Audit {label} evidence.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(read_json(args.model))
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(
            f"[{marker}] {label} id={report['contract_id']} "
            f"traces={report['trace_count']} errors={len(report['errors'])}"
        )
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
