#!/usr/bin/env python3
"""Audit procedural-generation seed, solvability, variety, and budget evidence."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {"typical", "dense", "regression", "fallback", "save_resume", "performance"}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit procedural generation evidence.")
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
    integer(model.get("generator_version"), "generator_version", 1)
    integer(model.get("content_version"), "content_version", 1)
    contract = obj(model.get("contract"), "contract")
    minimum_seeds = integer(contract.get("minimum_unique_seeds"), "minimum_unique_seeds", 2)
    required_features = strings(contract.get("required_features"), "required_features")
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios")
    unknown = sorted(required_scenarios - ALLOWED_SCENARIOS)
    if unknown:
        raise ContractError(f"unknown required scenarios: {', '.join(unknown)}")
    max_generation = number(contract.get("max_generation_ms"), "max_generation_ms")
    max_retries = integer(contract.get("max_retry_count"), "max_retry_count")
    max_invalid = integer(contract.get("max_invalid_results"), "max_invalid_results")
    max_unreachable = integer(
        contract.get("max_unreachable_objectives"), "max_unreachable_objectives"
    )
    max_dominant = number(contract.get("max_dominant_layout_share"), "max_dominant_layout_share")
    if max_dominant > 1:
        raise ContractError("max_dominant_layout_share must be <= 1")

    errors: list[str] = []
    traces = array(model.get("seed_traces"), "seed_traces")
    if not traces:
        raise ContractError("seed_traces must not be empty")
    seen_ids: set[str] = set()
    scenarios: set[str] = set()
    seed_hashes: dict[str, set[tuple[str, str]]] = defaultdict(set)
    seed_resume_hashes: dict[str, set[str]] = defaultdict(set)
    seed_layout: dict[str, str] = {}
    invalid_results = 0
    for index, raw in enumerate(traces):
        trace = obj(raw, f"seed_traces[{index}]")
        trace_id = text(trace.get("id"), f"seed_traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        seed = text(trace.get("seed"), f"trace {trace_id}.seed")
        scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
        scenarios.add(scenario)
        if scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown scenario {scenario}")
        if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
            errors.append(f"trace {trace_id} is not target-build evidence")
        result = text(trace.get("result"), f"trace {trace_id}.result")
        if result != "pass":
            invalid_results += 1
            errors.append(f"trace {trace_id} did not produce a valid result")
        layout_hash = text(trace.get("layout_hash"), f"trace {trace_id}.layout_hash")
        topology_hash = text(trace.get("topology_hash"), f"trace {trace_id}.topology_hash")
        seed_hashes[seed].add((layout_hash, topology_hash))
        seed_layout.setdefault(seed, layout_hash)
        resume_hash = text(trace.get("save_resume_hash"), f"trace {trace_id}.save_resume_hash")
        seed_resume_hashes[seed].add(resume_hash)
        if not boolean(
            trace.get("start_exit_connected"), f"trace {trace_id}.start_exit_connected"
        ):
            errors.append(f"trace {trace_id} has disconnected start and exit")
        unreachable = integer(
            trace.get("unreachable_objectives"), f"trace {trace_id}.unreachable_objectives"
        )
        if unreachable > max_unreachable:
            errors.append(
                f"trace {trace_id} has {unreachable} unreachable objectives above {max_unreachable}"
            )
        features = strings(trace.get("features"), f"trace {trace_id}.features")
        missing_features = sorted(required_features - features)
        if missing_features:
            errors.append(f"trace {trace_id} misses features: {', '.join(missing_features)}")
        generation_ms = number(trace.get("generation_ms"), f"trace {trace_id}.generation_ms")
        if generation_ms > max_generation:
            errors.append(f"trace {trace_id} exceeds generation-time budget")
        retries = integer(trace.get("retry_count"), f"trace {trace_id}.retry_count")
        if retries > max_retries:
            errors.append(f"trace {trace_id} retry count {retries} exceeds {max_retries}")
        if retries and not boolean(
            trace.get("fallback_succeeded"), f"trace {trace_id}.fallback_succeeded"
        ):
            errors.append(f"trace {trace_id} retries without deterministic recovery")

    unique_seeds = set(seed_hashes)
    if len(unique_seeds) < minimum_seeds:
        errors.append(f"unique seed count {len(unique_seeds)} is below {minimum_seeds}")
    for seed, hashes in seed_hashes.items():
        if len(hashes) > 1:
            errors.append(f"seed {seed} is not deterministic across repeated traces")
    for seed, hashes in seed_resume_hashes.items():
        if len(hashes) > 1:
            errors.append(f"seed {seed} save/resume hash is unstable")
    if invalid_results > max_invalid:
        errors.append(f"invalid result count {invalid_results} exceeds {max_invalid}")
    missing_scenarios = sorted(required_scenarios - scenarios)
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    layout_counts = Counter(seed_layout.values())
    dominant_share = (
        Decimal(max(layout_counts.values())) / Decimal(len(unique_seeds))
        if unique_seeds
        else Decimal(1)
    )
    if dominant_share > max_dominant:
        errors.append(
            f"dominant layout share {dominant_share} exceeds {max_dominant}"
        )

    distributions = array(model.get("distributions"), "distributions")
    seen_distributions: set[str] = set()
    for index, raw in enumerate(distributions):
        item = obj(raw, f"distributions[{index}]")
        item_id = text(item.get("id"), f"distributions[{index}].id")
        if item_id in seen_distributions:
            errors.append(f"duplicate distribution ID {item_id}")
        seen_distributions.add(item_id)
        observed = number(item.get("observed_share"), f"distribution {item_id}.observed_share")
        minimum = number(item.get("minimum_share"), f"distribution {item_id}.minimum_share")
        maximum = number(item.get("maximum_share"), f"distribution {item_id}.maximum_share")
        if minimum > maximum or maximum > 1:
            errors.append(f"distribution {item_id} has invalid declared range")
        elif not minimum <= observed <= maximum:
            errors.append(f"distribution {item_id} observed share {observed} outside range")

    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "trace_count": len(traces),
        "unique_seed_count": len(unique_seeds),
        "dominant_layout_share": str(dominant_share),
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
            f"[{marker}] procedural-generation id={report['contract_id']} "
            f"seeds={report['unique_seed_count']} traces={report['trace_count']} "
            f"errors={len(report['errors'])}"
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
